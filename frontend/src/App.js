import React, { useEffect, useRef, useState } from "react";
import "@/App.css";
import axios from "axios";
import { Moon, Sun, ArrowRight, MessageSquare, X, Send, ExternalLink, CheckCircle2, Sparkles, Users, Info } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ---------------- Session ---------------- //
function getSessionId() {
  let sid = localStorage.getItem("fc_session_id");
  if (!sid) {
    sid = "s-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem("fc_session_id", sid);
  }
  return sid;
}

// ---------------- Intro ---------------- //
function Intro({ onDone }) {
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const t = setTimeout(onDone, reduce ? 0 : 2100);
    return () => clearTimeout(t);
  }, [onDone]);
  return (
    <div className="intro-wrap" onClick={onDone} data-testid="intro-screen">
      <div className="intro-mark">
        <span className="intro-shape s1" />
        <span className="intro-shape s2" />
        <span className="intro-shape s3" />
        <span className="intro-shape s4" />
        <div className="intro-word">Founder Copilot</div>
        <div className="intro-tag">your AI cofounder · for Indian startups</div>
      </div>
      <div className="intro-skip">tap anywhere to skip</div>
    </div>
  );
}

// ---------------- Theme toggle ---------------- //
function useTheme() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("fc_theme");
    if (saved) return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("fc_theme", theme);
  }, [theme]);
  return [theme, setTheme];
}

function TopBar({ theme, setTheme, onOpenAbout }) {
  return (
    <div className="fixed top-0 left-0 right-0 z-30 flex items-center justify-between px-5 md:px-10 py-5">
      <div className="flex items-center gap-3">
        <div
          className="w-11 h-11 rounded-2xl flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, var(--fc-accent), var(--fc-accent-pressed))",
            boxShadow: "var(--fc-raised-sm)",
            color: "white",
            fontFamily: "'Fraunces', serif",
            fontSize: 22,
            fontWeight: 600,
          }}
        >
          F
        </div>
        <div>
          <div className="fc-display" style={{ fontSize: 18, color: "var(--fc-text)" }}>Founder Copilot</div>
          <div style={{ fontSize: 11, color: "var(--fc-text-mute)", letterSpacing: "0.06em" }}>YOUR AI COFOUNDER</div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          className="neo-icon-btn"
          data-testid="about-btn"
          onClick={onOpenAbout}
          aria-label="About the team"
          title="About Team Forca"
        >
          <Info size={18} />
        </button>
        <button
          className="neo-icon-btn"
          data-testid="theme-toggle"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
          title="Toggle theme"
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </div>
  );
}

// ---------------- Entry Screen ---------------- //
function EntryScreen({ onDone, sessionId }) {
  const [idea, setIdea] = useState("");
  const [targetMarket, setTargetMarket] = useState("");
  const [businessModel, setBusinessModel] = useState("b2c");
  const [stage, setStage] = useState("idea");
  const [foundersCount, setFoundersCount] = useState(1);
  const [state, setState] = useState("");
  const [dpiit, setDpiit] = useState(false);
  const [fundingGoal, setFundingGoal] = useState("bootstrap");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const submit = async () => {
    if (!idea.trim() || idea.trim().length < 20) {
      setErr("Give me at least a sentence or two — hard to help with 3 words.");
      return;
    }
    setErr("");
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/founder/analyze`, {
        session_id: sessionId,
        idea, target_market: targetMarket, business_model: businessModel,
        founders_count: Number(foundersCount) || 1,
        state, stage, dpiit_registered: dpiit, funding_goal: fundingGoal,
      });
      onDone(data);
    } catch (e) {
      setErr("Something broke on my end — try again in a second.");
      setLoading(false);
    }
  };

  const chips = (arr, val, setter, testidPrefix) => (
    <div className="flex flex-wrap gap-2">
      {arr.map((v) => (
        <button
          key={v.value}
          data-testid={`${testidPrefix}-${v.value}`}
          onClick={() => setter(v.value)}
          className="neo-chip"
          style={{
            boxShadow: val === v.value ? "var(--fc-pressed-sm)" : "var(--fc-raised-sm)",
            color: val === v.value ? "var(--fc-accent)" : "var(--fc-text-soft)",
            fontWeight: val === v.value ? 600 : 500,
            cursor: "pointer",
          }}
        >
          {v.label}
        </button>
      ))}
    </div>
  );

  return (
    <div className="screen-enter min-h-screen flex flex-col items-center px-5 md:px-10 pt-28 pb-32">
      <div className="max-w-3xl w-full" data-testid="entry-screen">
        <div className="mb-8">
          <div className="neo-chip inline-flex" style={{ marginBottom: 20 }}>
            <Sparkles size={13} style={{ color: "var(--fc-warm)" }} />
            <span>Built for Indian founders · DPIIT · MSME · SIDBI aware</span>
          </div>
          <h1
            className="fc-display"
            style={{ fontSize: "clamp(30px, 5vw, 46px)", lineHeight: 1.12, letterSpacing: "-0.02em", margin: 0, color: "var(--fc-text)" }}
          >
            Most masterpiece ideas never become a company.
            <br />
            <span style={{ color: "var(--fc-accent)" }}>Let's see if yours will.</span>
          </h1>
          <p style={{ color: "var(--fc-text-soft)", marginTop: 16, fontSize: 15.5, lineHeight: 1.6, maxWidth: 640 }}>
            Tell me what you're building. In two minutes I'll pressure-test the idea, match you to Indian funding schemes,
            recommend the right entity, and hand you a first-100-users plan. No fluff.
          </p>
        </div>

        <div className="panel" style={{ padding: 28 }}>
          <label className="block mb-2" style={{ fontSize: 13, fontWeight: 600, color: "var(--fc-text-soft)" }}>
            What are you building?
          </label>
          <textarea
            data-testid="idea-input"
            className="neo-input neo-textarea"
            placeholder="e.g., A WhatsApp-first AI copilot that helps small kirana stores in tier-3 cities forecast demand in Hindi. Two of us, based in Pune, want to raise a seed round in 12 months."
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-6">
            <div>
              <label className="block mb-2" style={{ fontSize: 12, fontWeight: 600, color: "var(--fc-text-soft)", letterSpacing: "0.06em" }}>
                TARGET MARKET
              </label>
              <input
                data-testid="target-market-input"
                className="neo-input"
                placeholder="e.g., kirana stores in tier-3 UP"
                value={targetMarket}
                onChange={(e) => setTargetMarket(e.target.value)}
              />
            </div>
            <div>
              <label className="block mb-2" style={{ fontSize: 12, fontWeight: 600, color: "var(--fc-text-soft)", letterSpacing: "0.06em" }}>
                STATE (india)
              </label>
              <input
                data-testid="state-input"
                className="neo-input"
                placeholder="e.g., Karnataka"
                value={state}
                onChange={(e) => setState(e.target.value)}
              />
            </div>
          </div>

          <div className="mt-6">
            <label className="block mb-2" style={{ fontSize: 12, fontWeight: 600, color: "var(--fc-text-soft)", letterSpacing: "0.06em" }}>
              BUSINESS MODEL
            </label>
            {chips(
              [
                { value: "b2c", label: "B2C" },
                { value: "b2b saas", label: "B2B / SaaS" },
                { value: "d2c", label: "D2C" },
                { value: "marketplace", label: "Marketplace" },
                { value: "service agency", label: "Services / Agency" },
              ],
              businessModel, setBusinessModel, "bm"
            )}
          </div>

          <div className="mt-6">
            <label className="block mb-2" style={{ fontSize: 12, fontWeight: 600, color: "var(--fc-text-soft)", letterSpacing: "0.06em" }}>
              STAGE
            </label>
            {chips(
              [
                { value: "idea", label: "Idea" },
                { value: "prototype", label: "Prototype" },
                { value: "mvp", label: "MVP" },
                { value: "revenue", label: "Revenue" },
                { value: "growth", label: "Growth" },
              ],
              stage, setStage, "stage"
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-6">
            <div>
              <label className="block mb-2" style={{ fontSize: 12, fontWeight: 600, color: "var(--fc-text-soft)", letterSpacing: "0.06em" }}>
                FOUNDERS
              </label>
              <input
                data-testid="founders-input"
                type="number" min={1} max={10}
                className="neo-input"
                value={foundersCount}
                onChange={(e) => setFoundersCount(e.target.value)}
              />
            </div>
            <div>
              <label className="block mb-2" style={{ fontSize: 12, fontWeight: 600, color: "var(--fc-text-soft)", letterSpacing: "0.06em" }}>
                FUNDING GOAL
              </label>
              {chips(
                [
                  { value: "bootstrap", label: "Bootstrap" },
                  { value: "grants", label: "Grants" },
                  { value: "seed vc", label: "Seed VC" },
                ],
                fundingGoal, setFundingGoal, "fg"
              )}
            </div>
            <div>
              <label className="block mb-2" style={{ fontSize: 12, fontWeight: 600, color: "var(--fc-text-soft)", letterSpacing: "0.06em" }}>
                DPIIT RECOGNISED?
              </label>
              {chips(
                [
                  { value: false, label: "Not yet" },
                  { value: true, label: "Yes" },
                ],
                dpiit, setDpiit, "dpiit"
              )}
            </div>
          </div>

          {err && (
            <div className="mt-5" style={{ color: "var(--fc-warm)", fontSize: 13.5, fontWeight: 500 }} data-testid="entry-error">
              {err}
            </div>
          )}

          <div className="mt-8 flex items-center justify-between flex-wrap gap-4">
            <div style={{ fontSize: 12, color: "var(--fc-text-mute)" }}>
              Takes ~10 seconds. No signup. Your profile is remembered on this device.
            </div>
            <button
              data-testid="validate-btn"
              onClick={submit}
              disabled={loading}
              className="neo-btn neo-btn-primary"
              style={{ padding: "16px 30px", fontSize: 15.5 }}
            >
              {loading ? "Thinking through it…" : "Validate my idea"}
              {!loading && <ArrowRight size={18} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------- Report Screen ---------------- //
function GaugeCircle({ label, value, testid }) {
  return (
    <div className="flex flex-col items-center" data-testid={testid}>
      <div className="gauge-ring" style={{ "--p": Math.max(0, Math.min(100, value)) }}>
        <span>{value}</span>
      </div>
      <div style={{ marginTop: 12, fontSize: 12, color: "var(--fc-text-soft)", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase" }}>
        {label}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const isOpen = status === "open";
  return (
    <span
      className="neo-chip"
      style={{
        fontSize: 11,
        color: isOpen ? "#1E7F5B" : "var(--fc-warm)",
        fontWeight: 600,
        letterSpacing: "0.04em",
      }}
    >
      <span style={{
        width: 8, height: 8, borderRadius: 999,
        background: isOpen ? "#2FBF7E" : "var(--fc-warm)",
      }} />
      {isOpen ? "Open now" : "Closed · next cycle TBD"}
    </span>
  );
}

function ReportScreen({ data, sessionId, onNew }) {
  const r = data.report;
  return (
    <div className="screen-enter min-h-screen px-5 md:px-10 pt-28 pb-32" data-testid="report-screen">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
          <div>
            <div className="neo-chip inline-flex" style={{ marginBottom: 12 }} data-testid="profile-badge">
              <Users size={13} style={{ color: "var(--fc-accent)" }} />
              Your Founder Copilot profile is building…
            </div>
            <h1 className="fc-display" style={{ fontSize: "clamp(28px, 4vw, 40px)", margin: 0, letterSpacing: "-0.02em" }}>
              Here's the honest read.
            </h1>
            <p style={{ color: "var(--fc-text-soft)", marginTop: 6, fontSize: 14.5, maxWidth: 620 }}>
              Everything below is grounded in what you just told me. Ask the chat for anything deeper.
            </p>
          </div>
          <button className="neo-btn" onClick={onNew} data-testid="new-idea-btn">
            <ArrowRight size={16} style={{ transform: "rotate(180deg)" }} />
            New idea
          </button>
        </div>

        {/* Validation */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="panel lg:col-span-2" data-testid="validation-panel">
            <h3>Validation</h3>
            <h2>How the idea reads today</h2>
            <div className="flex flex-wrap items-center gap-8 mb-6">
              <GaugeCircle label="Market signal" value={r.validation.market_signal} testid="gauge-market" />
              <GaugeCircle label="Feasibility"   value={r.validation.feasibility}   testid="gauge-feas" />
              <GaugeCircle label="Room to win"   value={r.validation.competition}   testid="gauge-comp" />
              <div className="flex-1 min-w-[220px]">
                <div style={{ fontSize: 12, color: "var(--fc-text-mute)", letterSpacing: "0.06em", fontWeight: 600 }}>OVERALL</div>
                <div className="fc-display" style={{ fontSize: 44, lineHeight: 1, color: "var(--fc-accent)" }}>{r.validation.overall}</div>
                <div style={{ fontSize: 13, color: "var(--fc-text-soft)" }}>out of 100 · a signal, not a verdict</div>
              </div>
            </div>
            <div style={{ borderTop: "1px solid rgba(0,0,0,0.05)", paddingTop: 18 }}>
              <div style={{ fontSize: 12, color: "var(--fc-text-mute)", letterSpacing: "0.06em", fontWeight: 600, marginBottom: 8 }}>
                SIGNALS
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, color: "var(--fc-text-soft)", fontSize: 14, lineHeight: 1.7 }}>
                {r.validation.signals.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          </div>

          <div className="panel" style={{
            background: "linear-gradient(160deg, rgba(232,130,61,0.10), rgba(107,91,255,0.06))",
          }} data-testid="priority-panel">
            <h3 style={{ color: "var(--fc-warm)" }}>Top priority to fix</h3>
            <h2>{r.validation.top_priority.area}</h2>
            <p style={{ color: "var(--fc-text)", fontSize: 15, lineHeight: 1.6, margin: 0 }}>
              {r.validation.top_priority.action}
            </p>
          </div>
        </div>

        {/* Funding */}
        <div className="panel mt-6" data-testid="funding-panel">
          <div className="flex items-start justify-between flex-wrap gap-3 mb-4">
            <div>
              <h3>Funding</h3>
              <h2 style={{ marginBottom: 0 }}>Schemes you're eligible for</h2>
            </div>
            <div className="neo-chip" style={{ fontSize: 12 }}>{r.funding.dpiit_hint}</div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {r.funding.schemes.map((s, i) => (
              <a
                key={i}
                href={s.url} target="_blank" rel="noreferrer"
                className="neo-surface block p-5"
                style={{ textDecoration: "none", color: "inherit" }}
                data-testid={`funding-card-${i}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 15, color: "var(--fc-text)" }}>{s.name}</div>
                    <div style={{ fontSize: 12, color: "var(--fc-text-mute)", marginTop: 2 }}>{s.run_by}</div>
                  </div>
                  <div className="neo-chip" style={{
                    background: "var(--fc-bg)",
                    boxShadow: "var(--fc-pressed-sm)",
                    color: "var(--fc-accent)", fontWeight: 700,
                  }}>{s.fit_score}% fit</div>
                </div>
                <div style={{ fontSize: 14, color: "var(--fc-text-soft)", marginTop: 10 }}>{s.amount}</div>
                <div className="mt-3 flex items-center justify-between flex-wrap gap-2">
                  <StatusBadge status={s.status} />
                  <span style={{ fontSize: 12, color: "var(--fc-text-mute)", display: "inline-flex", alignItems: "center", gap: 4 }}>
                    Open portal <ExternalLink size={12} />
                  </span>
                </div>
                <div style={{ fontSize: 12.5, color: "var(--fc-text-mute)", marginTop: 10, lineHeight: 1.5 }}>{s.note}</div>
              </a>
            ))}
          </div>
        </div>

        {/* Entity + GTM */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <div className="panel" data-testid="entity-panel">
            <h3>Legal entity</h3>
            <h2>{r.entity.entity}</h2>
            <p style={{ color: "var(--fc-text-soft)", fontSize: 14, lineHeight: 1.6 }}>{r.entity.rationale}</p>
            <div className="mt-4">
              <div style={{ fontSize: 12, color: "var(--fc-text-mute)", letterSpacing: "0.06em", fontWeight: 600, marginBottom: 8 }}>
                DOCUMENT CHECKLIST
              </div>
              <div className="flex flex-wrap gap-2">
                {r.entity.doc_checklist.map((c, i) => (
                  <span key={i} className="neo-chip" style={{ fontSize: 12 }}>
                    <CheckCircle2 size={12} style={{ color: "var(--fc-accent)" }} />
                    {c}
                  </span>
                ))}
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-3" style={{ fontSize: 12, color: "var(--fc-text-mute)" }}>
              <span>⏱ {r.entity.typical_setup_time}</span>
              <span>· {r.entity.typical_setup_cost}</span>
            </div>
          </div>

          <div className="panel" data-testid="gtm-panel">
            <h3>GTM playbook</h3>
            <h2>Your first moves</h2>
            <ol style={{ margin: 0, padding: 0, listStyle: "none" }}>
              {r.gtm.tactics.map((t, i) => (
                <li key={i} style={{ display: "flex", gap: 12, marginBottom: 10 }}>
                  <span
                    className="neo-inset-sm"
                    style={{
                      minWidth: 26, height: 26, display: "grid", placeItems: "center",
                      fontSize: 12, fontWeight: 700, color: "var(--fc-accent)",
                    }}
                  >{i + 1}</span>
                  <span style={{ color: "var(--fc-text)", fontSize: 14, lineHeight: 1.55 }}>{t}</span>
                </li>
              ))}
            </ol>
            <div className="mt-4" style={{ padding: 14, borderRadius: 14, boxShadow: "var(--fc-pressed-sm)" }}>
              <div style={{ fontSize: 11, color: "var(--fc-text-mute)", letterSpacing: "0.06em", fontWeight: 600 }}>FIRST 100 USERS</div>
              <div style={{ fontSize: 13.5, color: "var(--fc-text-soft)", marginTop: 4, lineHeight: 1.55 }}>{r.gtm.first_100_users_plan}</div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="neo-chip" style={{ fontSize: 12 }}>
                <Sparkles size={12} style={{ color: "var(--fc-warm)" }} />
                North star: {r.gtm.north_star_metric}
              </span>
              <span className="neo-chip" style={{ fontSize: 12 }}>Cadence: {r.gtm.cadence}</span>
            </div>
          </div>
        </div>

        {/* Growth opportunities */}
        <div className="panel mt-6" data-testid="growth-panel">
          <h3>Growth opportunities</h3>
          <h2>Real portals to plug into this month</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {r.growth.opportunities.map((o, i) => (
              <a
                key={i}
                href={o.url} target="_blank" rel="noreferrer"
                className="neo-surface block p-4"
                style={{ textDecoration: "none", color: "inherit" }}
                data-testid={`growth-card-${i}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="neo-chip" style={{ fontSize: 10.5, textTransform: "uppercase", letterSpacing: "0.08em" }}>{o.type}</span>
                  <span style={{ fontSize: 12, color: "var(--fc-accent)", fontWeight: 700 }}>{o.fit_score}%</span>
                </div>
                <div style={{ fontWeight: 600, fontSize: 14, color: "var(--fc-text)" }}>{o.name}</div>
                <div style={{ fontSize: 12, color: "var(--fc-text-mute)", marginTop: 2 }}>{o.when}</div>
                <div style={{ fontSize: 12.5, color: "var(--fc-text-soft)", marginTop: 8, lineHeight: 1.5 }}>{o.why}</div>
              </a>
            ))}
          </div>
        </div>

        <div className="mt-8 text-center" style={{ color: "var(--fc-text-mute)", fontSize: 13 }}>
          Want to go deeper? Tap the chat bubble in the corner — I have your full profile in memory.
        </div>
      </div>
    </div>
  );
}

// ---------------- Chat ---------------- //
function ChatPanel({ open, onClose, sessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        const { data } = await axios.get(`${API}/founder/chat/${sessionId}`);
        setMessages(data.messages || []);
      } catch {}
    })();
  }, [open, sessionId]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, streaming]);

  const send = async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setStreaming(true);

    try {
      const resp = await fetch(`${API}/founder/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() || "";
        for (const p of parts) {
          if (!p.startsWith("data:")) continue;
          const payload = p.slice(5).trim();
          try {
            const obj = JSON.parse(payload);
            if (obj.delta) {
              setMessages((m) => {
                const copy = m.slice();
                copy[copy.length - 1] = { role: "assistant", content: (copy[copy.length - 1].content || "") + obj.delta };
                return copy;
              });
            } else if (obj.tool_call) {
              setMessages((m) => {
                const copy = m.slice();
                // reset assistant text once tool-call happened; tool line was placeholder
                copy[copy.length - 1] = { role: "assistant", content: "" };
                return copy;
              });
            } else if (obj.error) {
              setMessages((m) => {
                const copy = m.slice();
                copy[copy.length - 1] = { role: "assistant", content: "Hit a snag reaching the model. Try again in a moment." };
                return copy;
              });
            }
          } catch {}
        }
      }
    } catch {
      setMessages((m) => {
        const copy = m.slice();
        copy[copy.length - 1] = { role: "assistant", content: "Network hiccup — try again." };
        return copy;
      });
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div
      className={`fixed inset-0 z-50 transition-opacity ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
      style={{ transition: "opacity 240ms ease-out" }}
      data-testid="chat-panel"
    >
      <div
        className="absolute inset-0"
        style={{ background: "rgba(0,0,0,0.25)", backdropFilter: "blur(4px)" }}
        onClick={onClose}
      />
      <div
        className="absolute right-0 bottom-0 top-0 w-full md:w-[440px] flex flex-col"
        style={{
          background: "var(--fc-bg)",
          boxShadow: "-12px 0 30px rgba(0,0,0,0.12)",
          transform: open ? "translateX(0)" : "translateX(20px)",
          transition: "transform 280ms cubic-bezier(0.22,1,0.36,1)",
        }}
      >
        <div className="flex items-center justify-between p-5" style={{ borderBottom: "1px solid rgba(0,0,0,0.05)" }}>
          <div className="flex items-center gap-3">
            <div className="neo-icon-btn active" style={{ pointerEvents: "none" }}>
              <MessageSquare size={18} />
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>Ask your cofounder</div>
              <div style={{ fontSize: 12, color: "var(--fc-text-mute)" }}>Grounded in your profile · streaming</div>
            </div>
          </div>
          <button className="neo-icon-btn" onClick={onClose} data-testid="chat-close" aria-label="Close chat">
            <X size={18} />
          </button>
        </div>

        <div ref={scrollRef} className="chat-scroll flex-1 overflow-y-auto p-5 flex flex-col gap-3">
          {messages.length === 0 && (
            <>
              <div className="chat-bubble-assistant">
                I've got your profile in memory. Ask me anything — "which scheme should I apply to first?", "find me more hackathons", "what did you recommend for my entity again?".
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {["Find me more hackathons", "Which scheme first?", "Rewrite my one-liner"].map((s) => (
                  <button
                    key={s}
                    className="neo-chip"
                    style={{ cursor: "pointer" }}
                    onClick={() => setInput(s)}
                    data-testid={`suggest-${s.slice(0,10)}`}
                  >{s}</button>
                ))}
              </div>
            </>
          )}
          {messages.map((m, i) => {
            let content = m.content || "";
            // Hide any tool-invocation prefix like [TOOL: name {...}] from the UI
            if (m.role === "assistant" && content.trimStart().startsWith("[TOOL:")) {
              const idx = content.indexOf("]");
              content = idx >= 0 ? content.slice(idx + 1).trimStart() : "";
            }
            return (
              <div key={i} className={m.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"} data-testid={`msg-${m.role}-${i}`}>
                {content || (streaming && i === messages.length - 1 ? "…" : "")}
              </div>
            );
          })}
        </div>

        <div className="p-4 flex items-center gap-2" style={{ borderTop: "1px solid rgba(0,0,0,0.05)" }}>
          <input
            className="neo-input"
            data-testid="chat-input"
            placeholder="Ask a follow-up…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") send(); }}
          />
          <button
            className="neo-btn neo-btn-primary"
            onClick={send}
            disabled={streaming || !input.trim()}
            data-testid="chat-send"
            style={{ padding: "12px 18px" }}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------- About Modal ---------------- //
function AboutModal({ open, onClose }) {
  if (!open) return null;
  const team = ["Abhiram Mamidi", "Joseph Rezin", "Ashish Rajesh", "Manushka A G"];
  return (
    <div className="fixed inset-0 z-50 grid place-items-center px-4" data-testid="about-modal">
      <div className="absolute inset-0" style={{ background: "rgba(0,0,0,0.35)", backdropFilter: "blur(4px)" }} onClick={onClose} />
      <div className="neo-surface-lg relative max-w-md w-full p-8">
        <button className="neo-icon-btn absolute" style={{ top: 16, right: 16 }} onClick={onClose} data-testid="about-close">
          <X size={16} />
        </button>
        <div className="neo-chip inline-flex" style={{ marginBottom: 12 }}>Team Forca</div>
        <h2 className="fc-display" style={{ margin: 0, fontSize: 24 }}>Built at hack pace, with care.</h2>
        <p style={{ color: "var(--fc-text-soft)", fontSize: 14, lineHeight: 1.6, marginTop: 8 }}>
          Founder Copilot is a demo of what an always-on AI cofounder for Indian founders can look like — plugged into DPIIT, SIDBI, MSME, and the real programs that matter.
        </p>
        <div className="flex flex-wrap gap-2 mt-4">
          {team.map((n) => <span key={n} className="neo-chip" style={{ fontSize: 12 }}>{n}</span>)}
        </div>
      </div>
    </div>
  );
}

// ---------------- Root ---------------- //
export default function App() {
  const [theme, setTheme] = useTheme();
  const [intro, setIntro] = useState(() => !sessionStorage.getItem("fc_intro_shown"));
  const [screen, setScreen] = useState("entry");
  const [report, setReport] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const sessionId = useRef(getSessionId()).current;

  useEffect(() => {
    // If we already have a report for this session, jump straight in
    (async () => {
      try {
        const { data } = await axios.get(`${API}/founder/report/${sessionId}`);
        if (data?.report) {
          setReport({ report: data.report, session_id: sessionId });
          setScreen("report");
        }
      } catch {}
    })();
  }, [sessionId]);

  const handleIntroDone = () => {
    sessionStorage.setItem("fc_intro_shown", "1");
    setIntro(false);
  };

  return (
    <div className="App" style={{ position: "relative", minHeight: "100vh" }}>
      {intro && <Intro onDone={handleIntroDone} />}

      <TopBar theme={theme} setTheme={setTheme} onOpenAbout={() => setAboutOpen(true)} />

      {screen === "entry" && (
        <EntryScreen
          sessionId={sessionId}
          onDone={(data) => { setReport(data); setScreen("report"); }}
        />
      )}
      {screen === "report" && report && (
        <ReportScreen
          data={report}
          sessionId={sessionId}
          onNew={() => { setReport(null); setScreen("entry"); }}
        />
      )}

      {/* Floating chat FAB */}
      <button
        className="neo-btn neo-btn-primary"
        data-testid="chat-fab"
        onClick={() => setChatOpen(true)}
        style={{
          position: "fixed",
          bottom: 60,
          right: 20,
          zIndex: 40,
          borderRadius: 999,
          padding: "14px 20px",
          fontSize: 14,
        }}
      >
        <MessageSquare size={18} />
        Ask cofounder
      </button>

      <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} sessionId={sessionId} />
      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />

      {/* Persistent watermark + team credit */}
      <div className="watermark" data-testid="watermark">Made with NitroStack</div>
      <div className="credit">
        <span className="credit-pill" onClick={() => setAboutOpen(true)} data-testid="team-credit">Team Forca</span>
      </div>
    </div>
  );
}
