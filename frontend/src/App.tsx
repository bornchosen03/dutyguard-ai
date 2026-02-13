import React from "react";

type TabKey =
  | "overview"
  | "impact"
  | "ai"
  | "intake"
  | "files"
  | "alerts"
  | "contact"
  | "deep";

type TariffFileItem = {
  storedName: string;
  bytes: number;
  modified: number;
};

const USER_KEY_STORAGE = "dutyguard_user_key";

function getOrCreateUserKey(): string {
  const existing = window.localStorage.getItem(USER_KEY_STORAGE);
  if (existing && existing.trim()) {
    return existing;
  }

  const next =
    typeof window.crypto !== "undefined" && typeof window.crypto.randomUUID === "function"
      ? window.crypto.randomUUID()
      : `user_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;

  window.localStorage.setItem(USER_KEY_STORAGE, next);
  return next;
}

export default function App() {
  const [userKey] = React.useState<string>(() => getOrCreateUserKey());
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
  const [contactWebsite, setContactWebsite] = React.useState<string>("");
  const [contactTopic, setContactTopic] = React.useState<string>("Tariff exposure review");
  const [contactMessage, setContactMessage] = React.useState<string>("");
  const [contactFiles, setContactFiles] = React.useState<FileList | null>(null);
  const [contactStatus, setContactStatus] = React.useState<string | null>(null);
  const [contactError, setContactError] = React.useState<string | null>(null);
  const [isSubmittingIntake, setIsSubmittingIntake] = React.useState(false);
  // Lead-capture modal state
  const [showLeadModal, setShowLeadModal] = React.useState(false);
  const [leadCompany, setLeadCompany] = React.useState("");
  const [leadEmail, setLeadEmail] = React.useState("");
  const [leadFile, setLeadFile] = React.useState<File | null>(null);
  const [leadError, setLeadError] = React.useState<string | null>(null);
  const [leadSubmitting, setLeadSubmitting] = React.useState(false);

  async function refreshFiles() {
    setIsLoadingFiles(true);
    setFilesError(null);
    try {
      const res = await fetch(`/api/tariff-files?user=${encodeURIComponent(userKey)}`);
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
      const res = await fetch(`/api/tariff-files?user=${encodeURIComponent(userKey)}`, {
        method: "POST",
        body: form,
      });
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

  function handleCTA() {
    // open quick lead modal to capture a contact and optional file
    setLeadCompany("");
    setLeadEmail("");
    setLeadFile(null);
    setLeadError(null);
    setShowLeadModal(true);
  }

  async function submitLeadModal() {
    setLeadError(null);
    const company = leadCompany.trim();
    const email = leadEmail.trim();
    if (!company || !email) {
      setLeadError("Please enter company and email.");
      return;
    }
    setLeadSubmitting(true);
    try {
      const form = new FormData();
      form.append("company", company);
      form.append("name", company);
      form.append("email", email);
      form.append("phone", "");
      form.append("website", "");
      form.append("message", `Fast estimate request (lead capture) from ${company}`);
      if (leadFile) {
        form.append("files", leadFile);
      }

      const res = await fetch("/api/intake", { method: "POST", body: form });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Lead submit failed (${res.status}): ${text}`);
      }
      const data = await res.json();
      // prefill contact page and switch there for more details
      setContactCompany(company);
      setContactEmail(email);
      setContactTopic("Tariff exposure review");
      setContactMessage("Please review my submission and provide an estimate.");
      setShowLeadModal(false);
      setTab("contact");
      setContactStatus(`Thanks — reference: ${data.id ?? "(ok)"}`);
    } catch (err) {
      setLeadError(err instanceof Error ? err.message : String(err));
    } finally {
      setLeadSubmitting(false);
    }
  }

  async function submitIntake() {
    setContactStatus(null);
    setContactError(null);

    const company = contactCompany.trim();
    const name = contactName.trim();
    const email = contactEmail.trim();
    const phone = contactPhone.trim();
    const message = contactMessage.trim();
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    if (!company || !name || !email || !message) {
      setContactError("Please complete Company, Name, Email, and Message.");
      return;
    }
    if (!emailOk) {
      setContactError("Please enter a valid email address.");
      return;
    }

    setIsSubmittingIntake(true);
    try {
      const form = new FormData();
      form.append("company", company);
      form.append("name", name);
      form.append("email", email);
      form.append("phone", phone);
      form.append("website", contactWebsite);
      form.append(
        "message",
        `Topic: ${contactTopic}\n\n${message}`
      );
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
      setContactStatus(`Thank you — your request was received. Reference: ${data.id ?? "(ok)"}`);
      setContactCompany("");
      setContactName("");
      setContactEmail("");
      setContactPhone("");
      setContactTopic("Tariff exposure review");
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
      </nav>

      {tab !== "overview" && (
        <div style={{ marginBottom: 12 }}>
          <button onClick={() => setTab("overview")}>← Back to Home</button>
        </div>
      )}

      {tab === "overview" && (
        <section>
          <h2>How we help</h2>
          <p style={{ fontSize: 18, fontWeight: 600 }}>
            Stop overpaying duties. We find recoverable dollars in your historical imports and build an audit-ready
            claim path your team can act on quickly.
          </p>
          <p>
            We help businesses identify duty overpayments, locate tariff-related documentation, and build a clear,
            audit-ready recovery package—so you can recover funds and reduce repeat losses.
          </p>
          <div style={{ marginTop: 12 }}>
            <button className="primary" onClick={handleCTA}>
              Get Free Tariff Recovery Estimate
            </button>
          </div>
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
                      <a
                        href={`/api/tariff-files/${encodeURIComponent(f.storedName)}?user=${encodeURIComponent(userKey)}`}
                        target="_blank"
                        rel="noreferrer"
                      >
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
        </section>
      )}

      {tab === "contact" && (
        <section>
          <h2>Contact Us</h2>
          <p>
            Share your request and supporting documents. Our team will review your submission and reply with next
            steps for tariff exposure analysis, duty recovery, and compliance support.
          </p>
          <p style={{ opacity: 0.85 }}>Typical response time: within 1 business day.</p>

          <div className="card" style={{ padding: 14, maxWidth: 820 }}>
            <div style={{ display: "grid", gap: 10 }}>
              <label>
                <strong>Company *</strong>
                <div>
                  <input
                    value={contactCompany}
                    onChange={(e) => setContactCompany(e.target.value)}
                    placeholder="Acme Imports LLC"
                  />
                </div>
              </label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <label>
                  <strong>Name *</strong>
                  <div>
                    <input
                      value={contactName}
                      onChange={(e) => setContactName(e.target.value)}
                      placeholder="Jane Smith"
                    />
                  </div>
                </label>
                <label>
                  <strong>Email *</strong>
                  <div>
                    <input
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      placeholder="jane@company.com"
                    />
                  </div>
                </label>
              </div>
              <label>
                <strong>Phone (optional)</strong>
                <div>
                  <input
                    value={contactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </label>
              <div style={{ display: "none" }} aria-hidden="true">
                <label>
                  Website
                  <input
                    tabIndex={-1}
                    autoComplete="off"
                    value={contactWebsite}
                    onChange={(e) => setContactWebsite(e.target.value)}
                  />
                </label>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 10 }}>
                <label>
                  <strong>Request type</strong>
                  <div>
                    <select value={contactTopic} onChange={(e) => setContactTopic(e.target.value)}>
                      <option>Tariff exposure review</option>
                      <option>Duty drawback / refunds</option>
                      <option>Classification review</option>
                      <option>USMCA / origin support</option>
                      <option>Compliance and audit readiness</option>
                    </select>
                  </div>
                </label>
              </div>
              <label>
                <strong>How can we help? *</strong>
                <div>
                  <textarea
                    value={contactMessage}
                    onChange={(e) => setContactMessage(e.target.value)}
                    rows={5}
                    placeholder="Tell us your current challenge, goals, and any deadlines."
                  />
                </div>
              </label>
              <label>
                <strong>Upload files (optional)</strong>
                <div>
                  <input type="file" multiple onChange={(e) => setContactFiles(e.target.files)} />
                </div>
              </label>

              <div style={{ fontSize: 13, opacity: 0.8 }}>
                By submitting this form, you consent to be contacted regarding your request.
              </div>

              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <button className="primary" onClick={() => void submitIntake()} disabled={isSubmittingIntake}>
                  {isSubmittingIntake ? "Submitting…" : "Submit Request"}
                </button>
                {contactStatus && <span style={{ color: "#0a7a0a" }}>{contactStatus}</span>}
                {contactError && <span style={{ color: "#b00020" }}>{contactError}</span>}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Lead capture modal */}
      {showLeadModal && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "fixed",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(0,0,0,0.4)",
            zIndex: 9999,
          }}
        >
          <div style={{ background: "#fff", padding: 20, borderRadius: 8, width: 520, maxWidth: "92%" }}>
            <h3 style={{ marginTop: 0 }}>Quick Estimate — Tell us the basics</h3>
            <div style={{ display: "grid", gap: 8 }}>
              <label>
                <strong>Company *</strong>
                <div>
                  <input value={leadCompany} onChange={(e) => setLeadCompany(e.target.value)} />
                </div>
              </label>
              <label>
                <strong>Email *</strong>
                <div>
                  <input value={leadEmail} onChange={(e) => setLeadEmail(e.target.value)} />
                </div>
              </label>
              <label>
                <strong>Attach a file (optional)</strong>
                <div>
                  <input
                    type="file"
                    onChange={(e) => setLeadFile(e.target.files?.[0] ?? null)}
                  />
                </div>
              </label>
              {leadError && <div style={{ color: "#b00020" }}>{leadError}</div>}
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button onClick={() => setShowLeadModal(false)} disabled={leadSubmitting}>
                  Cancel
                </button>
                <button className="primary" onClick={() => void submitLeadModal()} disabled={leadSubmitting}>
                  {leadSubmitting ? "Sending…" : "Request Estimate"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
