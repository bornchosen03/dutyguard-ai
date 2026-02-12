import React from "react";

type TabKey =
  | "overview"
  | "impact"
  | "ai"
  | "intake"
  | "files"
  | "alerts"
  | "contact"
  | "deep"
  | "roadmap"
  | "gto";

type TariffFileItem = {
  storedName: string;
  bytes: number;
  modified: number;
};

export default function App() {
  const [tab, setTab] = React.useState<TabKey>("overview");
  const [files, setFiles] = React.useState<TariffFileItem[]>([]);
  const [filesError, setFilesError] = React.useState<string | null>(null);
  const [isLoadingFiles, setIsLoadingFiles] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [uploadOk, setUploadOk] = React.useState<string | null>(null);

  const [annualImportValue, setAnnualImportValue] = React.useState<string>("1000000");
  const [oldDutyRatePct, setOldDutyRatePct] = React.useState<string>("2.5");
  const [newDutyRatePct, setNewDutyRatePct] = React.useState<string>("15");

  const [contactCompany, setContactCompany] = React.useState<string>("");
  const [contactName, setContactName] = React.useState<string>("");
  const [contactEmail, setContactEmail] = React.useState<string>("");
  const [contactPhone, setContactPhone] = React.useState<string>("");
  const [contactMessage, setContactMessage] = React.useState<string>("");
  const [contactFiles, setContactFiles] = React.useState<FileList | null>(null);
  const [contactStatus, setContactStatus] = React.useState<string | null>(null);
  const [contactError, setContactError] = React.useState<string | null>(null);
  const [isSubmittingIntake, setIsSubmittingIntake] = React.useState(false);

  async function refreshFiles() {
    setIsLoadingFiles(true);
    setFilesError(null);
    try {
      const res = await fetch("/api/tariff-files");
      if (!res.ok) throw new Error(`Failed to list files (${res.status})`);
      const data = (await res.json()) as TariffFileItem[];
      setFiles(data);
    } catch (err) {
      setFilesError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoadingFiles(false);
    }
  }

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    setUploadError(null);
    setUploadOk(null);
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/tariff-files", { method: "POST", body: form });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Upload failed (${res.status}): ${text}`);
      }
      setUploadOk(`Uploaded: ${file.name}`);
      await refreshFiles();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    } finally {
      e.target.value = "";
    }
  }

  React.useEffect(() => {
    // Auto-open GuardDuty as the default experience.
    const path = window.location.pathname || "/";
    if (path === "/" || path.startsWith("/aidev")) {
      window.history.replaceState({}, "", "/guardduty");
    }
  }, []);

  async function submitIntake() {
    setContactStatus(null);
    setContactError(null);
    setIsSubmittingIntake(true);
    try {
      const form = new FormData();
      form.append("company", contactCompany);
      form.append("name", contactName);
      form.append("email", contactEmail);
      form.append("phone", contactPhone);
      form.append("message", contactMessage);
      if (contactFiles) {
        for (const f of Array.from(contactFiles)) {
          form.append("files", f);
        }
      }

      const res = await fetch("/api/intake", { method: "POST", body: form });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Intake submit failed (${res.status}): ${text}`);
      }
      const data = (await res.json()) as { id?: string };
      setContactStatus(`Submitted. Reference: ${data.id ?? "(ok)"}`);
      setContactCompany("");
      setContactName("");
      setContactEmail("");
      setContactPhone("");
      setContactMessage("");
      setContactFiles(null);
    } catch (err) {
      setContactError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSubmittingIntake(false);
    }
  }

  return (
    <div className="app">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ margin: 0 }}>GuardDuty</h1>
      </div>

      <nav style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16, marginTop: 16 }}>
        <button onClick={() => setTab("overview")} aria-pressed={tab === "overview"}>
          Overview
        </button>
        <button onClick={() => setTab("impact")} aria-pressed={tab === "impact"}>
          Tariff Impact
        </button>
        <button onClick={() => setTab("ai")} aria-pressed={tab === "ai"}>
          AI for Tariffs
        </button>
        <button onClick={() => setTab("intake")} aria-pressed={tab === "intake"}>
          What We Need
        </button>
        <button
          onClick={() => {
            setTab("files");
            void refreshFiles();
          }}
          aria-pressed={tab === "files"}
        >
          Tariff Files
        </button>
        <button onClick={() => setTab("alerts")} aria-pressed={tab === "alerts"}>
          Alerts
        </button>
        <button onClick={() => setTab("contact")} aria-pressed={tab === "contact"}>
          Contact
        </button>
        <button onClick={() => setTab("deep")} aria-pressed={tab === "deep"}>
          Deep Dive (2026)
        </button>
        <button onClick={() => setTab("roadmap")} aria-pressed={tab === "roadmap"}>
          Roadmap (2027)
        </button>
        <button onClick={() => setTab("gto")} aria-pressed={tab === "gto"}>
          Global Trade OS
        </button>
      </nav>

      {tab !== "overview" && (
        <div style={{ marginBottom: 12 }}>
          <button onClick={() => setTab("overview")}>← Back to Home</button>
        </div>
      )}

      {tab === "overview" && (
        <section>
          <h2>How we help</h2>
          <p>
            We help businesses identify duty overpayments, locate tariff-related documentation, and build a clear,
            audit-ready recovery package—so you can recover funds and reduce repeat losses.
          </p>
          <ul>
            <li>Find missed refunds and overpaid duties</li>
            <li>Improve classification consistency and compliance</li>
            <li>Get clearer visibility into tariff exposure by product/supplier/route</li>
          </ul>
          <h3>Fees</h3>
          <p>The industry standard is a Contingency Fee ranging from 15% to 30% of the recovered funds.</p>
        </section>
      )}

      {tab === "impact" && (
        <section>
          <h2>How tariffs impact businesses</h2>
          <p>
            Tariffs can affect supply chains, investment, and input costs. On the supply side, higher costs can
            translate into higher prices and operational pressure. On the demand side, weaker spending can reduce
            orders and hiring plans.
          </p>
          <ul>
            <li>
              <strong>Supply chain disruption:</strong> rerouting, supplier changes, and lead-time volatility.
            </li>
            <li>
              <strong>Higher input costs:</strong> landed cost increases reduce margin if pricing can’t adjust.
            </li>
            <li>
              <strong>Planning risk:</strong> rapid policy changes can force reactive decisions.
            </li>
          </ul>
        </section>
      )}

      {tab === "ai" && (
        <section>
          <h2>AI for tariff classification and planning</h2>
          <p>
            In 2026, building an AI-driven Tariff Logic Engine requires moving beyond simple keyword matching and toward
            systems capable of legal-style reasoning—often with multiple cooperating agents.
          </p>
          <p>
            Companies are increasingly using AI (machine learning, NLP, and LLMs) to automate normally manual tariff
            classification and strategic planning—reducing errors and reacting faster to changes.
          </p>
          <p>
            Many companies adopt this as a “secret weapon” to offset double-digit cost increases from rising tariffs by
            automating complex trade compliance and sourcing decisions.
          </p>
          <ul>
            <li>
              <strong>Automated HTS classification:</strong> analyze product descriptions/specs to recommend HTS codes.
            </li>
            <li>
              <strong>Real-time monitoring & alerts:</strong> track updates across trade data and announcements.
            </li>
            <li>
              <strong>What-if modeling:</strong> simulate tariff increases and their impact on cost and cash flow.
            </li>
            <li>
              <strong>Alternative sourcing:</strong> identify suppliers/regions with lower tariff exposure.
            </li>
            <li>
              <strong>Predictive analytics:</strong> anticipate changes using historical data and indicators.
            </li>
            <li>
              <strong>Dynamic pricing guidance:</strong> recommend pricing moves to protect margin.
            </li>
          </ul>
          <p>
            Beyond basic cost reduction, advanced systems can recommend optimal sourcing locations based on tariff
            scenarios, reroute shipments to minimize duties, and identify alternative suppliers in lower-tariff
            jurisdictions.
          </p>
        </section>
      )}

      {tab === "deep" && (
        <section>
          <h2>Automated Trade Compliance & Intelligence Engine</h2>
          <p>
            To build a business around identifying and optimizing tariffs using AI, you aren’t just looking for
            numbers in a table. You’re building an Automated Trade Compliance & Intelligence Engine.
          </p>
          <p>
            Companies use AI to navigate the Harmonized System (HS) codes—the international language of trade—where a
            single digit error can lead to fines, delays, or overpaid taxes.
          </p>

          <details open>
            <summary>
              <strong>1) How AI finds and analyzes tariffs</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <p>
                AI replaces manual lookups with predictive modeling, natural language processing (NLP), and increasingly
                multi-modal extraction.
              </p>
              <h3>Classification (the HS code engine)</h3>
              <ul>
                <li>
                  <strong>Fuzzy matching:</strong> maps unusual product descriptions to known categories.
                </li>
                <li>
                  <strong>Contextual logic:</strong> distinguishes similar items used in different industries.
                </li>
                <li>
                  <strong>Multi-modal inputs:</strong> can use product photos + text descriptions when available.
                </li>
              </ul>

              <h3>Regulatory monitoring (real-time scanning)</h3>
              <p>
                Automated monitors track official bulletins, customs updates, and announcements so rate changes can be
                detected quickly.
              </p>

              <h3>Total landed cost calculation</h3>
              <p>
                AI doesn’t just find the tariff; it helps model total landed cost by combining product price, freight,
                insurance, customs duty, anti-dumping fees, and VAT where applicable.
              </p>
              <p style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace" }}>
                Total Landed Cost = Product Price + Insurance + Freight + Customs Duty + Anti-Dumping Fees + VAT
              </p>
            </div>
          </details>

          <details>
            <summary>
              <strong>2) Essential features (“moats”) for a perfect platform</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <ul>
                <li>
                  <strong>Origin optimizer (Rules of Origin):</strong> analyze bills of materials (BOM) vs FTA rules to
                  identify 0% opportunities and missing proof.
                </li>
                <li>
                  <strong>Duty drawback discovery:</strong> match import entries with export records to find refunds.
                </li>
                <li>
                  <strong>Predictive risk scoring:</strong> stress-test data against audit/seizure patterns.
                </li>
                <li>
                  <strong>Tariff engineering:</strong> suggest product/design adjustments that change classification and
                  reduce duty.
                </li>
              </ul>
            </div>
          </details>

          <details>
            <summary>
              <strong>3) Business model strategy</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <ul>
                <li>
                  <strong>Phase 1 — Integrations:</strong> connect to ERPs to pull data automatically.
                </li>
                <li>
                  <strong>Phase 2 — Validation layer:</strong> human-in-the-loop review for high-liability items.
                </li>
                <li>
                  <strong>Phase 3 — Strategic intelligence:</strong> reports and recommendations for sourcing/build
                  decisions under tariff scenarios.
                </li>
              </ul>
            </div>
          </details>

          <details>
            <summary>
              <strong>4) 2026 architecture (RAG + audit trails)</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <ul>
                <li>
                  <strong>Ingestion layer:</strong> OCR + vision for invoices, packing lists, photos.
                </li>
                <li>
                  <strong>Source of truth:</strong> knowledge graph linking HS codes to notes, GRIs, rulings, FTAs.
                </li>
                <li>
                  <strong>Reasoning engine:</strong> constrained LLM + logic that produces a documented rationale.
                </li>
                <li>
                  <strong>HITL dashboard:</strong> confidence + rationale draft with expert sign-off.
                </li>
                <li>
                  <strong>Audit-ready trails:</strong> every decision has evidence and rule references.
                </li>
              </ul>
              <p>
                Pro tip: De Minimis (“mass-parcel”) classification at huge scale is a high-demand capability for
                cross-border e-commerce.
              </p>
            </div>
          </details>

          <details>
            <summary>
              <strong>5) Synthetic Trade Expert (logic chain + multi-agent reasoning)</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <p>
                To reach the summit of this industry, don’t treat AI like a search engine—treat it like a synthetic
                trade expert that can explain its full logic chain and surface opportunities a human might miss.
              </p>

              <h3>Multi-agent “council” (recursive reasoning)</h3>
              <p>
                A “council of agents” can debate classification from different angles and produce a risk-aware
                recommendation:
              </p>
              <ul>
                <li>
                  <strong>Materialist:</strong> reads the bill of materials (materials/components) and argues likely
                  chapters.
                </li>
                <li>
                  <strong>Functionalist:</strong> focuses on intended use and real-world function.
                </li>
                <li>
                  <strong>Legalist:</strong> searches rulings and precedent to support or reject options.
                </li>
                <li>
                  <strong>Moderator:</strong> compares arguments and presents risk vs reward with a documented rationale.
                </li>
              </ul>

              <h3>Deep feature: automated supply chain rerouting</h3>
              <p>
                The goal isn’t only to find the tariff—it’s to change the supply chain outcome using FTA rules,
                transformation rules, and cost modeling.
              </p>

              <h3>Deep feature: chemical-level intelligence</h3>
              <p>
                For industries like pharma, chemicals, and textiles, small specification differences can change duty
                outcomes. A top-tier system should be able to extract data from lab reports/formulas and flag where
                classification-sensitive thresholds may exist.
              </p>

              <h3>“Guaranteed correctness” (future product layer)</h3>
              <p>
                A premium service layer can pair decision logs + audit trails with third-party risk coverage.
                Implementation requires legal review and insurer partnership; it’s an advanced offering, not a default
                claim.
              </p>

              <h3>Training on “dark data” + self-healing compliance loop</h3>
              <ul>
                <li>
                  Train on precedent (rulings), anti-dumping petitions, explanatory notes, and other regulatory sources.
                </li>
                <li>
                  When customs feedback happens, ingest the feedback and update the logic so the whole network improves.
                </li>
              </ul>
            </div>
          </details>
        </section>
      )}

      {tab === "gto" && (
        <section>
          <h2>Global Trade Operating System (2026)</h2>
          <p>
            A “perfect” tariff-intelligence business doesn’t just report the news—it helps the client decide what to do
            next, supported by evidence, modeling, and an audit-ready rationale.
          </p>

          <details open>
            <summary>
              <strong>Blueprint 1: “Molecule-to-Margin” engine (chemical & material AI)</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <p>
                This capability targets highly technical categories (chemicals, materials, pharma, textiles) where small
                spec changes can shift classification and duty outcomes.
              </p>
              <ul>
                <li>
                  <strong>Ingestion (“lab layer”):</strong> extract fields from SDS/CoA PDFs (flash point, viscosity,
                  composition by weight).
                </li>
                <li>
                  <strong>Logic core:</strong> map names to identifiers (e.g., CAS numbers) and link to targeted duty
                  measures (including anti-dumping where applicable).
                </li>
                <li>
                  <strong>Purity thresholds:</strong> detect when a value sits near a threshold and flag how spec changes
                  could affect classification-sensitive outcomes.
                </li>
              </ul>
              <p style={{ opacity: 0.85 }}>
                Note: Any manufacturing/spec recommendations require engineering and legal review.
              </p>
            </div>
          </details>

          <details>
            <summary>
              <strong>Blueprint 2: “War Room” simulator (geopolitical engine)</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <ul>
                <li>
                  <strong>Sensor net:</strong> monitor official registers/journals and announcements frequently and flag
                  sector-level risk signals.
                </li>
                <li>
                  <strong>Digital twin simulation:</strong> model “what-if” scenarios and recalculate total landed cost
                  across SKUs/parts.
                </li>
                <li>
                  <strong>Ghost sourcing:</strong> when a critical alert triggers, identify alternative suppliers in safer
                  jurisdictions.
                </li>
              </ul>
            </div>
          </details>

          <details>
            <summary>
              <strong>Blueprint 3: Business model moat (risk coverage)</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <p>
                The strongest enterprise wedge is liability reduction. A premium offering can pair audit trails and
                human oversight with third-party Errors & Omissions coverage.
              </p>
              <p style={{ opacity: 0.85 }}>
                Important: Any “guarantee” must be contract-based, scoped, and underwritten. This UI is informational and
                not a blanket promise.
              </p>
            </div>
          </details>

          <details>
            <summary>
              <strong>The “green” future: CBAM (carbon is the new tariff)</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <p>
                By 2027, carbon-related adjustments (e.g., CBAM) become a major cost driver. A “carbon agent” can model
                tax + emissions together and recommend lower-emission sourcing.
              </p>
            </div>
          </details>

          <details>
            <summary>
              <strong>Execution checklist (first 90 days)</strong>
            </summary>
            <div style={{ marginTop: 8 }}>
              <ol>
                <li>
                  <strong>Pick a niche first:</strong> start with the highest-pain categories (e.g., chemicals, auto parts).
                </li>
                <li>
                  <strong>Use licensed sources:</strong> obtain licenses for restricted materials (don’t scrape).
                </li>
                <li>
                  <strong>Build a hook:</strong> “Tariff Auditor” intake—let clients upload spreadsheets and receive an
                  overpayment opportunity report.
                </li>
              </ol>
            </div>
          </details>
        </section>
      )}

      {tab === "intake" && (
        <section>
          <h2>What we need from your company</h2>
          <p>
            To find your tariff exposure and maximize recoveries, we’ll ask for a focused set of documents and data.
            If you don’t have everything, we can start with what you have.
          </p>
          <ul>
            <li>
              <strong>Shipment / entry data:</strong> entry summaries, commercial invoices, packing lists.
            </li>
            <li>
              <strong>Broker records:</strong> broker statements, duty/tax payments, amendments.
            </li>
            <li>
              <strong>Product details:</strong> descriptions, specs, materials, use-case, photos (if available).
            </li>
            <li>
              <strong>Supplier + country of origin:</strong> supplier lists and origin documentation.
            </li>
            <li>
              <strong>HTS codes used historically:</strong> what you’ve been classifying under today.
            </li>
            <li>
              <strong>Time window:</strong> which months/years you want audited first.
            </li>
          </ul>
          <p>
            If your supply chain is impacted by new or reciprocal tariffs, we can analyze where costs increased,
            identify the root causes (classification/origin/scope), and prioritize the highest-value recovery
            opportunities.
          </p>
        </section>
      )}

      {tab === "files" && (
        <section>
          <h2>Tariff files</h2>
          <p>
            Upload tariff-related documents here so we can locate and reference them quickly during classification,
            audit prep, and recovery work.
          </p>

          <div style={{ display: "grid", gap: 8, maxWidth: 720 }}>
            <label>
              <strong>Upload a file</strong>
              <div>
                <input type="file" onChange={onUpload} />
              </div>
            </label>
            {uploadOk && <div style={{ color: "#0a7a0a" }}>{uploadOk}</div>}
            {uploadError && <div style={{ color: "#b00020" }}>{uploadError}</div>}

            <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8 }}>
              <button onClick={() => void refreshFiles()} disabled={isLoadingFiles}>
                {isLoadingFiles ? "Refreshing…" : "Refresh list"}
              </button>
              {filesError && <span style={{ color: "#b00020" }}>{filesError}</span>}
            </div>

            <div>
              <h3 style={{ marginBottom: 8 }}>Stored files</h3>
              {files.length === 0 ? (
                <p>No uploaded files yet.</p>
              ) : (
                <ul>
                  {files.map((f) => (
                    <li key={f.storedName}>
                      <a href={`/api/tariff-files/${encodeURIComponent(f.storedName)}`} target="_blank" rel="noreferrer">
                        {f.storedName}
                      </a>{" "}
                      <span style={{ opacity: 0.75 }}>
                        ({Math.round(f.bytes / 1024)} KB, {new Date(f.modified * 1000).toLocaleString()})
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </section>
      )}

      {tab === "alerts" && (
        <section>
          <h2>Alert Agent (Protective Shield)</h2>
          <p>
            Tariffs can change quickly, with new Executive Orders, exemptions, retaliatory measures, or classification
            reinterpretations. If a company doesn’t get alerted early enough, the result is often multimillion-dollar
            landed-cost surprises, margin compression, rushed supplier switches, and compliance errors.
          </p>
          <p>
            GuardDuty’s Alert Agent is designed to act like a protective shield subscription: it monitors known tariff
            sources for changes, detects diffs, estimates financial exposure, and produces mitigation recommendations.
          </p>

          <h3>Fast exposure calculator</h3>
          <div style={{ display: "grid", gap: 10, maxWidth: 680 }}>
            <label>
              <strong>Annual import value (USD)</strong>
              <div>
                <input
                  inputMode="decimal"
                  value={annualImportValue}
                  onChange={(e) => setAnnualImportValue(e.target.value)}
                  placeholder="1000000"
                />
              </div>
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <label>
                <strong>Old duty rate (%)</strong>
                <div>
                  <input
                    inputMode="decimal"
                    value={oldDutyRatePct}
                    onChange={(e) => setOldDutyRatePct(e.target.value)}
                    placeholder="2.5"
                  />
                </div>
              </label>
              <label>
                <strong>New duty rate (%)</strong>
                <div>
                  <input
                    inputMode="decimal"
                    value={newDutyRatePct}
                    onChange={(e) => setNewDutyRatePct(e.target.value)}
                    placeholder="15"
                  />
                </div>
              </label>
            </div>

            {(() => {
              const v = Number(annualImportValue);
              const oldPct = Number(oldDutyRatePct);
              const newPct = Number(newDutyRatePct);
              const ok = Number.isFinite(v) && Number.isFinite(oldPct) && Number.isFinite(newPct) && v >= 0;
              if (!ok) return <div style={{ color: "#b00020" }}>Enter valid numbers to estimate exposure.</div>;
              const deltaPct = (newPct - oldPct) / 100;
              const delta = v * deltaPct;
              const fmt = (n: number) =>
                n.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
              return (
                <div className="card" style={{ padding: 14 }}>
                  <div>
                    <strong>Estimated annual delta duty:</strong> {fmt(delta)}
                  </div>
                  <div style={{ opacity: 0.8, marginTop: 6 }}>
                    Based on ${(deltaPct * 100).toFixed(2)}% change on {fmt(v)}.
                  </div>
                </div>
              );
            })()}
          </div>

          <h3 style={{ marginTop: 18 }}>How to run it</h3>
          <ol>
            <li>Run the scraper to refresh `knowledge_base/live_tariffs.csv`.</li>
            <li>Run the Alert Agent to diff and write `knowledge_base/tariff_alerts.json`.</li>
          </ol>
          <p>
            Use: <code>./scripts/run_scraper.sh</code> then <code>./scripts/run_alerts.sh</code>.
          </p>
        </section>
      )}

      {tab === "contact" && (
        <section>
          <h2>Contact / Intake</h2>
          <p>
            Upload your files and share your information here. We’ll use it to assess tariff exposure, duty recovery,
            and compliance risk.
          </p>

          <div className="card" style={{ padding: 14, maxWidth: 820 }}>
            <div style={{ display: "grid", gap: 10 }}>
              <label>
                <strong>Company</strong>
                <div>
                  <input value={contactCompany} onChange={(e) => setContactCompany(e.target.value)} />
                </div>
              </label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <label>
                  <strong>Name</strong>
                  <div>
                    <input value={contactName} onChange={(e) => setContactName(e.target.value)} />
                  </div>
                </label>
                <label>
                  <strong>Email</strong>
                  <div>
                    <input value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} />
                  </div>
                </label>
              </div>
              <label>
                <strong>Phone (optional)</strong>
                <div>
                  <input value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
                </div>
              </label>
              <label>
                <strong>What do you need help with?</strong>
                <div>
                  <textarea
                    value={contactMessage}
                    onChange={(e) => setContactMessage(e.target.value)}
                    rows={5}
                    placeholder="Tariff exposure, duty drawback, classification review, USMCA eligibility, audits…"
                  />
                </div>
              </label>
              <label>
                <strong>Upload files (PDFs, spreadsheets, invoices, 7501s, BOLs)</strong>
                <div>
                  <input type="file" multiple onChange={(e) => setContactFiles(e.target.files)} />
                </div>
              </label>

              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <button className="primary" onClick={() => void submitIntake()} disabled={isSubmittingIntake}>
                  {isSubmittingIntake ? "Submitting…" : "Submit"}
                </button>
                {contactStatus && <span style={{ color: "#0a7a0a" }}>{contactStatus}</span>}
                {contactError && <span style={{ color: "#b00020" }}>{contactError}</span>}
              </div>
            </div>
          </div>
        </section>
      )}

      {tab === "roadmap" && (
        <section>
          <h2>12‑Month “Zero‑to‑Scale” Roadmap (2027)</h2>
          <p>
            To become a top global company in AI-based tariff intelligence, the execution plan must combine regulatory
            agility, proprietary data, and high-value service layers—while minimizing legal risk.
          </p>

          <h3>Phase 1 — Foundation (Months 1–3)</h3>
          <ul>
            <li>
              <strong>Month 1: Data aggregation + knowledge graph</strong> — ingest Big 5 tariff schedules (US, EU,
              China, Japan, UK), build vector search over HS tables, rulings, and legal notes; validate against a
              “golden set” of complex items.
            </li>
            <li>
              <strong>Month 2: Audit-proof rationale generator</strong> — every classification includes rule-based
              rationale and human-oversight logs.
            </li>
            <li>
              <strong>Month 3: De Minimis alpha API</strong> — high-volume parcel classification API optimized for speed.
            </li>
          </ul>

          <h3>Phase 2 — Market entry (Months 4–6)</h3>
          <ul>
            <li>
              <strong>Month 4: US + Mexico wedge (USMCA)</strong> — free audit pilot + savings split; origin/RVC
              automation and certificate-of-origin tooling.
            </li>
            <li>
              <strong>Month 5: Duty drawback hunter</strong> — match historical imports to exports to locate refunds;
              fund growth via success fee.
            </li>
            <li>
              <strong>Month 6: ERP & commerce integrations</strong> — Shopify Plus + NetSuite plugins; accurate landed
              cost and pricing.
            </li>
          </ul>

          <h3>Phase 3 — Scaling & war‑gaming (Months 7–9)</h3>
          <ul>
            <li>
              <strong>Month 7: Vietnam + India expansion</strong> — “factory selector” recommendations under tariff
              scenarios.
            </li>
            <li>
              <strong>Month 8: Tariff engineering studio</strong> — design-time suggestions that reduce duty exposure.
            </li>
            <li>
              <strong>Month 9: Geopolitical war room</strong> — scenario planning that recalculates SKU-level margin
              impact and recommends supplier shifts or pricing changes.
            </li>
          </ul>

          <h3>Phase 4 — Ecosystem (Months 10–12)</h3>
          <ul>
            <li>
              <strong>Month 10: “Green lane” ESG / forced labor</strong> — multi-tier supplier mapping to flag risk before
              shipment.
            </li>
            <li>
              <strong>Month 11: API-first headless customs</strong> — white-label engine to forwarders; per-shipment
              micro-fee scaling.
            </li>
            <li>
              <strong>Month 12: Autonomous broker workflow</strong> — partner or license; generate/submit entries and
              archive audit trails.
            </li>
          </ul>

          <h3>Competitive advantages (“why we win”)</h3>
          <ul>
            <li>
              <strong>Pre-computation:</strong> refresh answers nightly as laws change for instant responses.
            </li>
            <li>
              <strong>The “Why” engine:</strong> every code includes a documented rationale and evidence trail.
            </li>
            <li>
              <strong>Margin protection:</strong> sell profit impact (saved duty) not just compliance.
            </li>
            <li>
              <strong>Shadow mode:</strong> run alongside current broker to prove accuracy and win trust.
            </li>
          </ul>

          <p style={{ opacity: 0.8 }}>
            Note: This roadmap is strategic guidance and not legal advice.
          </p>
        </section>
      )}
    </div>
  );
}
