from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from adcvd_checker import check_ad_cvd_risk
from de_minimis_optimizer import evaluate_de_minimis
from drawback_audit import DrawbackAuditAgent
from precedent_agent import PrecedentAgent
from sourcing_arbitrage import SourcingOption, choose_best_sourcing
from war_room import as_rows, build_war_room_report


DEFAULT_API_BASE = os.environ.get("DUTYGUARD_API_BASE", "http://127.0.0.1:8080")


CAS_RE = re.compile(r"\b(\d{2,7}-\d{2}-\d)\b")


def extract_cas_numbers(text: str) -> list[str]:
    if not text:
        return []
    return sorted(set(CAS_RE.findall(text)))


def estimate_cbam_carbon_tariff(
    quantity_tonnes: float,
    emissions_tco2_per_tonne: float,
    carbon_price_usd_per_tco2: float,
    free_allowance_pct: float,
) -> float:
    """Very rough CBAM-style estimate (placeholder model).

    CBAM is complex and sector-specific; this MVP gives an executive signal.
    """

    qty = max(0.0, float(quantity_tonnes))
    intensity = max(0.0, float(emissions_tco2_per_tonne))
    price = max(0.0, float(carbon_price_usd_per_tco2))
    allowance = min(100.0, max(0.0, float(free_allowance_pct))) / 100.0

    chargeable = qty * intensity * (1.0 - allowance)
    return chargeable * price


def _safe_get_secrets_value(key: str) -> Optional[str]:
    try:
        if key in st.secrets:
            value = st.secrets[key]
            return str(value) if value is not None else None
    except Exception:
        return None
    return None


def normalize_api_base(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""

    # Common paste errors: full /health URL, or /api prefix.
    raw = raw.rstrip("/")
    if raw.endswith("/health"):
        raw = raw[: -len("/health")]
    raw = raw.rstrip("/")
    if raw.endswith("/api"):
        raw = raw[: -len("/api")]
    return raw.rstrip("/")


def get_api_base() -> str:
    if "api_base" in st.session_state and st.session_state.api_base:
        candidate = normalize_api_base(str(st.session_state.api_base))
        return candidate or DEFAULT_API_BASE.rstrip("/")

    secret = _safe_get_secrets_value("DUTYGUARD_API_BASE")
    candidate = normalize_api_base(secret or "")
    return (candidate or DEFAULT_API_BASE).rstrip("/")


def call_classify_api(api_base: str, prod: dict[str, Any]) -> tuple[bool, dict[str, Any] | str]:
    try:
        res = requests.post(f"{api_base}/api/classify", json=prod, timeout=30)
        if not res.ok:
            return False, f"{res.status_code}: {res.text}"
        return True, res.json()
    except Exception as exc:
        return False, str(exc)


@st.cache_data(ttl=20, show_spinner=False)
def api_health(api_base: str) -> tuple[bool, str]:
    try:
        res = requests.get(f"{api_base}/health", timeout=5)
        if res.ok:
            return True, "ok"
        return False, f"{res.status_code}: {res.text[:200]}"
    except Exception as exc:
        return False, str(exc)


@st.cache_data(ttl=30, show_spinner=False)
def load_alerts_json(api_base: str) -> Optional[dict[str, Any]]:
    try:
        res = requests.get(f"{api_base}/api/alerts", timeout=10)
        if res.ok:
            return res.json()
    except Exception:
        pass

    # Fallback: show nothing if endpoint not present yet.
    return None


def show_drawback_page() -> None:
    st.header("💰 Duty Drawback Recovery Portal")
    st.info("CBP Electronic Refund Mandate: Feb 6, 2026 — ACH only (no paper checks).")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Recoverable Duties (5-Year Lookback)", "$412,890", delta="Ready to File")
    with col2:
        st.metric("Accelerated Payment Status", "Active", help="Typical refund timing varies by program.")

    st.subheader("Run an audit (CSV upload)")
    st.caption("Imports CSV requires: `hs_code`, `duty_paid` (and optional `import_date`).")
    st.caption("Exports CSV requires: `hs_code` (and optional `export_proof`, `export_date`).")

    imp = st.file_uploader("Import records (ACE/7501 extract)", type=["csv"], key="imp")
    exp = st.file_uploader("Export / destruction proof", type=["csv"], key="exp")

    if imp and exp:
        if st.button("Run Drawback Audit"):
            tmp_dir = Path("knowledge_base")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            imp_path = tmp_dir / "imports_upload.csv"
            exp_path = tmp_dir / "exports_upload.csv"
            imp_path.write_bytes(imp.getvalue())
            exp_path.write_bytes(exp.getvalue())

            try:
                agent = DrawbackAuditAgent(imp_path, exp_path)
                matches = agent.find_matches()
                summary = agent.summarize(matches)

                st.success(
                    f"✅ Potential refund pool (99% cap): ${summary.total_potential_refund:,.0f} "
                    f"across {summary.total_matches} substitution matches."
                )
                st.warning(summary.mandate_notice)

                st.subheader("Audit Findings")
                if len(matches) == 0:
                    st.write("No substitution matches found (check HS codes/columns).")
                else:
                    st.dataframe(matches, use_container_width=True)

                    csv_bytes = matches.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download matches CSV",
                        data=csv_bytes,
                        file_name="drawback_matches.csv",
                        mime="text/csv",
                    )

                    if st.button("Generate CBP Form 7551 (MVP)"):
                        st.success("MVP: generated matches CSV + audit trail fields. Next: render official PDF.")
            except Exception as exc:
                st.error(f"Audit failed: {exc}")

    st.subheader("Example findings")
    st.table(
        [
            {
                "HTS Code": "8471.30",
                "Import Date": "2024-05-12",
                "Duty Paid": "$12,000",
                "Export Proof": "BOL-9921",
                "Refund": "$11,880",
            },
            {
                "HTS Code": "8517.62",
                "Import Date": "2025-01-10",
                "Duty Paid": "$8,500",
                "Export Proof": "INV-5542",
                "Refund": "$8,415",
            },
        ]
    )


def show_war_room_page(alerts_payload: Optional[dict[str, Any]]) -> None:
    st.header("🚨 Tariff War Room")
    report = build_war_room_report(alerts_payload)
    st.caption(f"Generated: {report.generated_at_utc}")
    rows = as_rows(report)
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No active war-room signals.")


def show_optimizers_page() -> None:
    st.header("🧠 Trade Optimizers")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("De Minimis Optimizer")
        order_value = st.number_input("Order value (USD)", min_value=0.0, value=650.0, step=25.0, key="mini_val")
        threshold = st.number_input("Threshold (USD)", min_value=0.0, value=800.0, step=50.0, key="mini_thr")
        plan = evaluate_de_minimis(order_value, threshold)
        st.write("Eligible:", "Yes" if plan.eligible else "No")
        st.caption(plan.recommendation)

        st.subheader("AD/CVD Risk Checker")
        hs_code = st.text_input("HS code", value="7208.38", key="ad_hs")
        origin = st.text_input("Origin country (ISO-2)", value="CN", key="ad_origin")
        ad = check_ad_cvd_risk(hs_code, origin)
        st.write("Risk:", ad.risk_level.upper())
        st.caption(ad.notes)

    with c2:
        st.subheader("Sourcing Arbitrage")
        base_value = st.number_input("Base product value (USD)", min_value=0.0, value=100000.0, step=1000.0, key="arb_base")
        a_country = st.text_input("Option A country", value="VN", key="arb_a_country")
        a_duty = st.number_input("A duty rate (%)", min_value=0.0, value=5.0, step=0.5, key="arb_a_duty")
        a_log = st.number_input("A logistics (USD)", min_value=0.0, value=4200.0, step=100.0, key="arb_a_log")
        b_country = st.text_input("Option B country", value="MX", key="arb_b_country")
        b_duty = st.number_input("B duty rate (%)", min_value=0.0, value=2.0, step=0.5, key="arb_b_duty")
        b_log = st.number_input("B logistics (USD)", min_value=0.0, value=6800.0, step=100.0, key="arb_b_log")

        decision = choose_best_sourcing(
            base_value_usd=base_value,
            option_a=SourcingOption(country=a_country, duty_rate_pct=a_duty, logistics_cost_usd=a_log),
            option_b=SourcingOption(country=b_country, duty_rate_pct=b_duty, logistics_cost_usd=b_log),
        )
        st.success(f"Best sourcing: {decision.best_country}")
        st.metric("Estimated total cost", f"${decision.estimated_total_cost_usd:,.0f}")
        st.caption(decision.rationale)

        st.subheader("Precedent Search")
        query = st.text_input("Search precedent", value="lithium battery classification", key="prec_query")
        matches = PrecedentAgent().search(query, top_k=3)
        for m in matches:
            st.write(f"- **{m.title}** ({m.source})")
            st.caption(m.summary)


# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="DutyGuard AI — Command Center", layout="wide", page_icon="🛡️")


def demo_classify(description: str) -> dict[str, Any]:
    text = (description or "").lower()
    if any(k in text for k in ["drone", "quad", "uav"]):
        hs = "8806.22"
        rate = "0–5% (varies)"
    elif any(k in text for k in ["lithium", "battery", "li-ion", "lion"]):
        hs = "8507.60"
        rate = "3.4% (example)"
    elif any(k in text for k in ["steel", "bolt", "screw", "fastener"]):
        hs = "7318.15"
        rate = "Free–8.5% (varies)"
    else:
        hs = "8479.89"
        rate = "2.5% (example)"

    return {
        "suggested_hs_code": hs,
        "duty_rate": rate,
        "confidence_interval": [0.55, 0.80],
        "requires_human_review": True,
        "reasoning_manifesto": [
            "Demo mode: backend API is not connected yet.",
            "Deploy the FastAPI backend (Render recommended) and set DUTYGUARD_API_BASE in Streamlit Secrets.",
            "This output is a placeholder to keep the dashboard usable.",
        ],
    }


# --- SIDEBAR: CONTROLS & SETTINGS ---
with st.sidebar:
    st.title("DutyGuard AI")

    page_options = ["Overview", "Duty Drawback Audit", "War Room", "Trade Optimizers"]
    if "page" not in st.session_state or st.session_state["page"] not in page_options:
        st.session_state["page"] = "Overview"

    api_base = get_api_base()
    healthy, health_msg = api_health(api_base)

    st.subheader("Connection")
    st.text_input(
        "API base URL",
        value=api_base,
        key="api_base",
        help="Set this to your hosted backend, e.g. https://dutyguard-api-xxxx.onrender.com",
    )
    api_base = get_api_base()
    healthy, health_msg = api_health(api_base)
    if healthy:
        st.success("API: online")
    else:
        st.error("API: offline")
        st.caption(f"Details: {health_msg}")

    page = st.radio("Command Center", page_options, key="page")
    region = st.selectbox("Global Region", ["North America (USMCA)", "European Union", "ASEAN", "China"])
    risk_threshold = st.slider("Alert Sensitivity", 0.0, 1.0, 0.75)
    st.caption("Current API:")
    st.code(api_base)

    st.caption("Deploy backend on Render:")
    st.markdown("- https://render.com")
    st.markdown("- New + → Blueprint → pick `bornchosen03/dutyguard-ai`")
    st.markdown("- It will use `render.yaml` to deploy the API")

    if not healthy:
        st.info(
            "Dashboard is in Demo mode until a backend is deployed. "
            "Classify + Alerts will show placeholders."
        )

# --- MAIN DASHBOARD INTERFACE ---
if page != "Overview":
    if st.button("← Back to Home", type="secondary"):
        st.session_state["page"] = "Overview"
        st.rerun()

if page == "Duty Drawback Audit":
    show_drawback_page()
    st.stop()

if page == "War Room":
    alerts_payload = load_alerts_json(api_base) if healthy else None
    show_war_room_page(alerts_payload)
    st.stop()

if page == "Trade Optimizers":
    show_optimizers_page()
    st.stop()

st.title("🛡️ DutyGuard AI Command Center")
st.markdown("### Tariff, drawback, and compliance intelligence")

# --- ROW 1: TOP LEVEL KPIs (MVP placeholders) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Landed Cost", "$1.2M", "+$45k", delta_color="inverse")
col2.metric("Tariff Engineering Savings", "$312k", "15.4%", delta_color="normal")
col3.metric("Audit Risk Score", "0.12", "-0.05", delta_color="normal")
col4.metric("Live Tracked SKUs", "4,205", "New Law Detected", delta_color="off")

# --- ROW 2: AI INTERACTIVE CLASSIFIER ---
st.divider()
st.subheader("🔍 Instant AI Product Classifier")
col_left, col_right = st.columns([2, 1])

with col_left:
    prod_desc = st.text_area(
        "Enter Product Description or Lab Report Details:",
        placeholder="e.g., Industrial drone with 95% carbon fiber frame and lithium-ion power...",
        height=140,
    )

    st.caption("Tip: include materials + intended use + origin/destination.")

    cas = extract_cas_numbers(prod_desc)
    if cas:
        st.write("Detected CAS numbers:", ", ".join(cas))

    if st.button("Run AI Intelligence Analysis"):
        if not prod_desc.strip():
            st.warning("Add a product description first.")
            st.stop()

        # Map text area into current backend schema
        payload = {
            "name": "Dashboard Product",
            "description": prod_desc,
            "materials": {"steel": 0.0},
            "value": 10000.0,
            "origin_country": "CN" if region in ["China"] else "MX" if region.startswith("North") else "VN",
            "destination_country": "US" if region.startswith("North") else "EU" if region == "European Union" else "US",
            "intended_use": "Client-submitted dashboard analysis",
        }

        with st.spinner("Analyzing..."):
            if healthy:
                ok, out = call_classify_api(api_base, payload)
                if not ok:
                    st.error(f"API classify failed: {out}")
                    st.stop()
                data = out if isinstance(out, dict) else {}
            else:
                data = demo_classify(prod_desc)

        st.success(f"✅ Suggested HS Code: {data.get('suggested_hs_code')}")
        st.write("**Duty Rate:**", data.get("duty_rate"))
        st.write("**Confidence Interval:**", data.get("confidence_interval"))
        if data.get("requires_human_review"):
            st.warning("Human-in-the-loop review required (min CI < 0.92).")
        st.info("**Reasoning Manifesto:**\n\n" + "\n".join(data.get("reasoning_manifesto", [])))
        if data.get("reasoning_log_path"):
            st.caption(f"Audit log: {data['reasoning_log_path']}")

with col_right:
    st.markdown("#### Financial Simulation")
    st.write("Current Tariff: **15%**")
    st.write("Engineering Arbitrage (Vietnam): **0%**")

    st.markdown("#### Carbon Tariff (Executive estimate)")
    qty = st.number_input("Quantity (tonnes)", min_value=0.0, value=10.0, step=1.0)
    intensity = st.number_input("Emissions intensity (tCO₂ / tonne)", min_value=0.0, value=2.1, step=0.1)
    price = st.number_input("Carbon price ($/tCO₂)", min_value=0.0, value=80.0, step=5.0)
    allowance = st.slider("Free allowance (%)", 0.0, 100.0, 0.0)
    cbam = estimate_cbam_carbon_tariff(qty, intensity, price, allowance)
    st.metric("Estimated carbon tariff", f"${cbam:,.0f}")

# --- ROW 2b: Alerts snapshot ---
st.divider()
st.subheader("🛰️ Alert Agent Snapshot")
if healthy:
    alerts = load_alerts_json(api_base)
    if alerts is None:
        st.caption("No alerts yet (or alert agent hasn’t generated `tariff_alerts.json`).")
    else:
        st.json(alerts)
else:
    st.info(
        "Alerts are unavailable until the backend is deployed. "
        "Once Render is live and DUTYGUARD_API_BASE is set, this will populate."
    )

# --- ROW 3: GEOPOLITICAL RISK HEATMAP (MVP mock) ---
st.divider()
st.subheader("⚠️ Predictive Risk Monitor")
chart_data = pd.DataFrame(
    {
        "Country": ["China", "Mexico", "Vietnam", "India", "EU"],
        "Risk Level": [0.95, 0.20, 0.45, 0.30, 0.15],
    }
)
fig = px.bar(
    chart_data,
    x="Country",
    y="Risk Level",
    color="Risk Level",
    title="Current Geopolitical Tariff Risk by Source",
    color_continuous_scale="Reds",
)
st.plotly_chart(fig, use_container_width=True)

# --- FOOTER ---
st.caption(f"Last Intelligence Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
