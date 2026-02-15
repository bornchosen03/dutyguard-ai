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
  // Color palette
  const colors = {
    primary: "#0ea5e9",
    accent: "#ff4d6d",
    accent2: "#9b5cff",
    accent3: "#00d4ff",
    background: "#000000",
    highlight: "#ffd166",
    text: "#f8fafc",
  };

  // Header and navigation items
  const navItems = [
    { key: "overview", label: "Home" },
    { key: "intake", label: "Upload" },
    { key: "files", label: "Quotes" },
    { key: "impact", label: "Invoices" },
    { key: "alerts", label: "Results" },
    { key: "contact", label: "Support" },
  ];
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
  const [remainingQuotes, setRemainingQuotes] = React.useState<number | null>(null);
  // Lead-capture modal state
  const [showLeadModal, setShowLeadModal] = React.useState(false);
  const [leadCompany, setLeadCompany] = React.useState("");
  const [leadEmail, setLeadEmail] = React.useState("");
  const [leadFile, setLeadFile] = React.useState<File | null>(null);
  const [leadError, setLeadError] = React.useState<string | null>(null);
  const [leadSubmitting, setLeadSubmitting] = React.useState(false);

  // Sample testimonials
  const testimonials = [
    { name: "Acme Imports", quote: "DutyGuard-AI reduced our tariff exposure by 30%.", role: "Head of Ops" },
    { name: "Global Traders LLC", quote: "Fast, accurate classification and easy export.", role: "Compliance Manager" },
  ];

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

  React.useEffect(() => {
    // fetch remaining free-quote count for this user
    (async () => {
      try {
        const res = await fetch(`/api/quote-status?user=${encodeURIComponent(userKey)}`);
        if (!res.ok) return;
        const data = await res.json();
        setRemainingQuotes(typeof data.remaining === 'number' ? data.remaining : null);
      } catch (e) {
        // ignore
      }
    })();

    // Inject Tawk.to live chat widget
    const script = document.createElement("script");
    script.src = "https://embed.tawk.to/your_tawkto_property_id/default";
    script.async = true;
    script.charset = "UTF-8";
    script.setAttribute("crossorigin", "*");
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  // Analytics: basic Google Analytics (replace MEASUREMENT_ID)
  React.useEffect(() => {
    const GA_ID = (window as any).__DG_GA_ID || "G-XXXXXXXXXX";
    if (!GA_ID) return;
    // load gtag
    const s = document.createElement("script");
    s.async = true;
    s.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
    document.head.appendChild(s);
    (window as any).dataLayer = (window as any).dataLayer || [];
    function gtag(...args: any[]) {
      (window as any).dataLayer.push(arguments);
    }
    ; (window as any).gtag = gtag;
    gtag("js", new Date());
    gtag("config", GA_ID, { send_page_view: true });
    return () => {
      // no-op cleanup; script remains but won't double-init in dev
    };
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
    <div style={{ fontFamily: 'Inter, sans-serif', background: colors.background, minHeight: '100vh', color: colors.text }}>
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 2rem', background: '#fff', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ fontWeight: 700, fontSize: 24, color: colors.primary }}>DutyGuard-AI</div>
        <nav style={{ display: 'flex', gap: '2rem' }}>
          {navItems.map(item => (
            <button
              key={item.key}
              style={{ background: 'none', border: 'none', color: tab === item.key ? colors.primary : colors.text, fontWeight: tab === item.key ? 700 : 400, fontSize: 16, cursor: 'pointer' }}
              onClick={() => setTab(item.key as TabKey)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div>
          <button style={{ background: colors.accent, color: '#fff', border: 'none', borderRadius: 6, padding: '0.5rem 1.2rem', fontWeight: 600, fontSize: 16, cursor: 'pointer' }}>
            Login / Signup
          </button>
        </div>
      </header>

      {/* Hero Section */}
      {tab === "overview" && (
        <section style={{ padding: '3rem 2rem 2rem 2rem', textAlign: 'center', background: '#fff' }}>
          <h1 style={{ fontSize: 36, fontWeight: 800, color: colors.primary, marginBottom: 12 }}>
            Unlock Your Tariff Data Instantly
          </h1>
          <div style={{ display: 'inline-block', background: colors.highlight, color: colors.text, fontWeight: 700, borderRadius: 8, padding: '0.3rem 1rem', marginBottom: 16 }}>
            First Quote Free!
          </div>
          <div style={{ margin: '2rem 0' }}>
            <button
              style={{ background: colors.accent2, color: '#fff', fontWeight: 700, fontSize: 20, border: 'none', borderRadius: 8, padding: '1rem 2.5rem', cursor: 'pointer', boxShadow: '0 2px 8px #0001' }}
              onClick={() => setTab("intake")}
            >
              Upload Now
            </button>
          </div>
        </section>
      )}

      {/* Main Dashboard */}
      {tab === "overview" && (
        <section style={{ maxWidth: 900, margin: '2rem auto', background: '#fff', borderRadius: 12, boxShadow: '0 2px 12px #0001', padding: '2rem' }}>
          {/* Progress Bar */}
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
            <div style={{ flex: 1, height: 8, background: '#e5e7eb', borderRadius: 4, marginRight: 12 }}>
              <div style={{ width: '33%', height: 8, background: colors.primary, borderRadius: 4 }} />
            </div>
            <span style={{ fontWeight: 600, color: colors.primary }}>Upload → Quote → Payment → Results</span>
          </div>
          {/* Current Status */}
          <div style={{ fontWeight: 600, marginBottom: 16 }}>
            {remainingQuotes === null ? 'Checking free quotes...' : `You have ${remainingQuotes} free quote${remainingQuotes === 1 ? '' : 's'} left!`}
          </div>
          {/* Recent Activity */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Recent Activity</div>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {files.length === 0 && <li>No uploads yet.</li>}
              {files.map(f => (
                <li key={f.storedName} style={{ marginBottom: 4 }}>
                  {f.storedName} ({(f.bytes / 1024).toFixed(1)} KB)
                </li>
              ))}
            </ul>
          </div>
          {/* CTA */}
          <div>
            <button
              style={{ background: colors.accent, color: '#fff', fontWeight: 700, fontSize: 18, border: 'none', borderRadius: 8, padding: '0.8rem 2rem', cursor: 'pointer', boxShadow: '0 2px 8px #0001' }}
              onClick={() => setTab("intake")}
            >
              Get Started
            </button>
          </div>
          {/* Testimonials */}
          <div style={{ marginTop: 24 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Customer Testimonials</div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {testimonials.map((t) => (
                <div key={t.name} style={{ background: '#f8fafc', padding: 12, borderRadius: 8, minWidth: 220 }}>
                  <div style={{ fontWeight: 700 }}>{t.name}</div>
                  <div style={{ fontStyle: 'italic', margin: '8px 0' }}>&ldquo;{t.quote}&rdquo;</div>
                  <div style={{ fontSize: 12, color: '#6b7280' }}>{t.role}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ...existing code for other tabs and features... */}


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
