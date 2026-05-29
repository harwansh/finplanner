import React, { useState, useRef, useEffect } from "react";

/*
  SmartFinly — Educational Finance Chatbot
  Premium black/gold conversational interface.

  Behaviour:
   - Posts {message} to the configured chat API (window.SMARTFINLY_CHAT_API).
   - If no API is configured (e.g. preview), it falls back to an in-browser
     demo knowledge base so the experience is fully interactive.
   - Two hard rules mirrored client-side: it never asks for sensitive data,
     and it refuses buy/sell/product advice (educational only).
*/

const GOLD = "#d8b15a";

// ---- Client-side guardrail mirrors (defence in depth; server is source of truth)
const ADVICE_RE =
  /\b(should i (buy|sell|invest|hold)|which (stock|fund|mutual fund|scheme|share|policy) should i|what should i (buy|sell|invest)|recommend (me )?(a |some )?(stock|fund|share)|best (stock|mutual fund|fund|share|scheme) to (buy|invest)|is .* a good (buy|investment|stock)|will .* (go up|rise|crash|fall)|where should i invest my)\b/i;

const SENSITIVE_RE =
  /(aadhaar|aadhar|\bpan\b|\botp\b|password|\bupi\b|account number|ifsc)/i;

const ADVICE_REDIRECT =
  "I'm an educational assistant, so I can't tell you what to buy, sell, or hold, or recommend a specific stock, fund, or product. I can explain the underlying concept so you can decide for yourself. For personalised, regulated advice, please consult a SEBI-registered investment adviser.";

const DISCLAIMER =
  "Educational information only — not investment, tax, or legal advice, and not a recommendation to buy or sell anything.";

// ---- Tiny built-in demo KB (used only when no backend is configured) -------
const DEMO_KB = [
  {
    k: ["emergency fund", "rainy day", "months expenses", "buffer"],
    topic: "Personal Finance Management",
    a: "An emergency fund is money set aside to cover unexpected costs — a job loss, medical bill, or urgent repair — without breaking long-term investments or taking on debt. A common educational guideline is to hold roughly three to six months of essential expenses (rent, EMIs, food, utilities, insurance premiums). It's usually kept somewhere safe and quickly accessible, such as a savings account or liquid instrument, rather than in volatile assets. The idea is to build this protection before taking on investment risk.",
  },
  {
    k: ["term insurance", "term life", "whole life", "life cover", "life insurance"],
    topic: "Life Insurance",
    a: "Term life insurance provides a death benefit for a fixed period (say 20–30 years) at a relatively low premium, and pays out only if the insured passes away during that term. Whole/traditional life policies offer lifelong cover and often a savings or maturity component, which makes premiums substantially higher. Educationally, term cover is often discussed as a pure-protection tool aligned to your working years and dependants, while bundled savings-plus-insurance products mix two goals. The 'right' structure depends on your dependants, liabilities and time horizon.",
  },
  {
    k: ["hra", "house rent allowance", "rent exemption"],
    topic: "Tax Planning",
    a: "House Rent Allowance (HRA) exemption under the old tax regime is the minimum of three amounts: (1) actual HRA received, (2) rent paid minus 10% of basic salary, and (3) 50% of basic salary if you live in a metro city, or 40% if non-metro. Only the exempt portion is tax-free; the remainder of HRA is taxable. This is a concept explainer — your actual figures depend on your salary structure and rent.",
  },
  {
    k: ["old regime", "new regime", "tax regime", "which regime"],
    topic: "Tax Planning",
    a: "India's old tax regime offers lower headline simplicity but allows many deductions and exemptions (such as 80C, 80D, HRA, home-loan interest). The new regime offers wider, lower slab rates and a higher standard deduction, but removes most deductions. Educationally, the old regime tends to suit people who actively use deductions, while the new regime can suit those who don't. The break-even depends entirely on how much you'd otherwise claim — worth comparing both with your own numbers.",
  },
  {
    k: ["sip", "systematic investment", "compounding", "rupee cost"],
    topic: "Investments — Asset Classes & Returns",
    a: "A Systematic Investment Plan (SIP) means investing a fixed amount at regular intervals rather than a lump sum. Two educational ideas underpin it: rupee-cost averaging (you buy more units when prices are low and fewer when high, smoothing your average cost) and compounding (returns themselves earn returns over time, so longer horizons matter a lot). SIPs are a contribution method, not a product — the outcome still depends on what you invest in and for how long.",
  },
  {
    k: ["will", "succession", "nominee", "estate", "inheritance"],
    topic: "Estate Planning",
    a: "A will is a legal document stating how you want your assets distributed after death and who should administer your estate (the executor). A nominee, by contrast, is often only a custodian who receives assets to pass on to legal heirs — nomination and ownership aren't always the same thing. Where there's no will, succession follows the applicable personal/inheritance laws. Estate planning concepts include wills, nomination, joint holding, and trusts, each with different control and tax characteristics.",
  },
  {
    k: ["health insurance", "mediclaim", "hospitalisation", "deductible"],
    topic: "Health Insurance",
    a: "Health insurance reimburses or pays for medical costs such as hospitalisation, up to a sum insured. Educational concepts to understand include the sum insured (your annual cover limit), room-rent limits, co-payment (a share you pay on each claim), waiting periods for pre-existing conditions, and network vs non-network hospitals. A higher sum insured and fewer restrictive sub-limits generally mean broader protection, which is reflected in the premium.",
  },
  {
    k: ["regulator", "sebi", "rbi", "irdai", "who regulates"],
    topic: "Financial Regulation & Intermediaries",
    a: "India's financial system has specialised regulators: SEBI oversees securities markets and intermediaries, the RBI handles banking and monetary matters, IRDAI regulates insurance, and PFRDA oversees pensions. This separation means different products fall under different rule-books and grievance channels. Understanding which regulator covers a product helps you know where investor protections and complaint mechanisms sit.",
  },
];

function demoAnswer(message) {
  const low = message.toLowerCase();
  let best = null;
  let bestScore = 0;
  for (const item of DEMO_KB) {
    const score = item.k.reduce((s, kw) => (low.includes(kw) ? s + 1 : s), 0);
    if (score > bestScore) {
      bestScore = score;
      best = item;
    }
  }
  if (best && bestScore > 0) {
    return { answer: best.a, source: "knowledge_base", confidence: "demo", topics: [best.topic], disclaimer: DISCLAIMER };
  }
  return {
    answer:
      "In this preview I can answer a focused set of topics from the educational library — try emergency funds, term vs whole life insurance, HRA, old vs new tax regime, SIPs and compounding, wills and succession, health insurance, or who regulates what. Connect the backend to unlock the full document library plus AI explanations.",
    source: "none",
    confidence: "none",
    topics: [],
    disclaimer: DISCLAIMER,
  };
}

const SUGGESTIONS = [
  "What is an emergency fund and how big should it be?",
  "Term vs whole life insurance — what's the difference?",
  "How is HRA exemption calculated?",
  "Old vs new tax regime, explained",
  "What is a SIP and how does compounding work?",
  "What does a will do, and what is a nominee?",
];

function SourceTag({ source, topics, confidence }) {
  let label = "Educational library";
  if (source === "ai") label = "AI explainer";
  else if (source === "guardrail") label = "Safety guideline";
  else if (source === "none") label = "No match";
  const topic = topics && topics.length ? topics[0] : null;
  return (
    <div className="sf-tag">
      <span className="sf-tag-dot" />
      {label}
      {topic ? <span className="sf-tag-topic">· {topic}</span> : null}
      {confidence === "low" ? <span className="sf-tag-topic">· approximate</span> : null}
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text:
        "Hi — I'm SmartFinly, your educational finance companion. Ask me to explain a concept in plain language: budgeting, emergency funds, insurance, tax basics, investing ideas, retirement or estate planning. I won't tell you what to buy or sell — only help you understand.",
      meta: { source: "knowledge_base", topics: [], confidence: "n/a" },
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const scrollRef = useRef(null);
  const taRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || busy) return;
    setNotice("");

    if (SENSITIVE_RE.test(message)) {
      setNotice("For your safety, never type PAN, Aadhaar, OTP, passwords, UPI IDs, or account numbers. I removed nothing — just please don't share those.");
    }

    setMessages((m) => [...m, { role: "user", text: message }]);
    setInput("");
    if (taRef.current) taRef.current.style.height = "auto";

    // Client-side advice guardrail (server enforces this too).
    if (ADVICE_RE.test(message)) {
      setMessages((m) => [
        ...m,
        { role: "bot", text: ADVICE_REDIRECT, meta: { source: "guardrail", topics: [], confidence: "n/a" } },
      ]);
      return;
    }

    setBusy(true);
    try {
      const api = typeof window !== "undefined" ? window.SMARTFINLY_CHAT_API : null;
      let data;
      if (api) {
        const res = await fetch(api, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message }),
        });
        data = await res.json();
        if (!res.ok) throw new Error(data?.error || "Request failed");
      } else {
        await new Promise((r) => setTimeout(r, 450)); // simulate latency
        data = demoAnswer(message);
      }
      setMessages((m) => [
        ...m,
        {
          role: "bot",
          text: data.answer || "I couldn't generate an answer just now. Please try rephrasing.",
          meta: { source: data.source, topics: data.topics || [], confidence: data.confidence },
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "bot", text: "I couldn't reach the educational service just now. Please try again in a moment.", meta: { source: "none", topics: [], confidence: "none" } },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function onKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function autosize(e) {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
  }

  return (
    <div className="sf-root">
      <style>{CSS}</style>
      <div className="sf-grain" />
      <div className="sf-glow" />

      <header className="sf-header">
        <div className="sf-brand">
          <div className="sf-mark" aria-hidden>
            <svg viewBox="0 0 32 32" width="26" height="26">
              <path d="M6 22 L13 13 L19 18 L26 8" fill="none" stroke={GOLD} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="26" cy="8" r="2.4" fill={GOLD} />
            </svg>
          </div>
          <div className="sf-brandtext">
            <span className="sf-name">SmartFinly</span>
            <span className="sf-sub">Educational finance companion</span>
          </div>
        </div>
        <div className="sf-pill">Education only · No buy / sell calls</div>
      </header>

      <main className="sf-chat" ref={scrollRef}>
        <div className="sf-inner">
          {messages.map((m, i) => (
            <div key={i} className={`sf-row ${m.role}`}>
              {m.role === "bot" && (
                <div className="sf-avatar" aria-hidden>
                  <svg viewBox="0 0 32 32" width="18" height="18">
                    <path d="M6 22 L13 13 L19 18 L26 8" fill="none" stroke="#0b0b08" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              )}
              <div className={`sf-bubble ${m.role}`}>
                <p>{m.text}</p>
                {m.role === "bot" && m.meta && m.meta.source && m.meta.source !== "n/a" && (
                  <SourceTag source={m.meta.source} topics={m.meta.topics} confidence={m.meta.confidence} />
                )}
              </div>
            </div>
          ))}

          {busy && (
            <div className="sf-row bot">
              <div className="sf-avatar" aria-hidden>
                <svg viewBox="0 0 32 32" width="18" height="18">
                  <path d="M6 22 L13 13 L19 18 L26 8" fill="none" stroke="#0b0b08" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="sf-bubble bot sf-typing">
                <span /><span /><span />
              </div>
            </div>
          )}

          {messages.length <= 1 && (
            <div className="sf-suggest">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="sf-chip" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </main>

      <footer className="sf-foot">
        {notice && <div className="sf-notice">{notice}</div>}
        <div className="sf-composer">
          <textarea
            ref={taRef}
            rows={1}
            value={input}
            placeholder="Ask about a financial concept…"
            onChange={autosize}
            onKeyDown={onKey}
          />
          <button className="sf-send" onClick={() => send()} disabled={busy || !input.trim()} aria-label="Send">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M4 12 L20 4 L13 20 L11 13 Z" fill="none" stroke="#0b0b08" strokeWidth="1.8" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
        <div className="sf-disclaimer">{DISCLAIMER} Never share PAN, Aadhaar, OTP, passwords or account details.</div>
      </footer>
    </div>
  );
}

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Outfit:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }
.sf-root {
  position: relative;
  height: 100vh;
  max-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(216,177,90,0.10), transparent 60%),
    radial-gradient(900px 500px at 0% 110%, rgba(216,177,90,0.06), transparent 55%),
    #0b0b08;
  color: #f1ece1;
  font-family: 'Outfit', system-ui, sans-serif;
  overflow: hidden;
}
.sf-grain {
  position: absolute; inset: 0; pointer-events: none; opacity: 0.04; mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.sf-glow { position:absolute; top:-30%; right:-10%; width:60vw; height:60vw; background: radial-gradient(circle, rgba(216,177,90,0.12), transparent 60%); filter: blur(40px); pointer-events:none; }

.sf-header {
  position: relative; z-index: 2;
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(216,177,90,0.16);
  backdrop-filter: blur(8px);
}
.sf-brand { display:flex; align-items:center; gap:12px; }
.sf-mark {
  width:42px; height:42px; border-radius:12px;
  display:grid; place-items:center;
  background: linear-gradient(145deg, rgba(216,177,90,0.18), rgba(216,177,90,0.04));
  border:1px solid rgba(216,177,90,0.35);
}
.sf-brandtext { display:flex; flex-direction:column; line-height:1.1; }
.sf-name { font-family:'Fraunces', serif; font-size:1.32rem; letter-spacing:0.2px; color:#f6efe0; }
.sf-sub { font-size:0.72rem; color:#a79c84; letter-spacing:0.3px; }
.sf-pill {
  font-size:0.72rem; color:#d8b15a; padding:7px 13px; border-radius:999px;
  border:1px solid rgba(216,177,90,0.30); background:rgba(216,177,90,0.06); white-space:nowrap;
}

.sf-chat { position:relative; z-index:1; flex:1; overflow-y:auto; padding: 26px 0 14px; }
.sf-inner { max-width: 820px; margin:0 auto; padding: 0 22px; }
.sf-chat::-webkit-scrollbar { width:9px; }
.sf-chat::-webkit-scrollbar-thumb { background: rgba(216,177,90,0.22); border-radius:10px; }

.sf-row { display:flex; gap:12px; margin: 16px 0; animation: rise .42s cubic-bezier(.2,.7,.3,1) both; }
.sf-row.user { justify-content:flex-end; }
@keyframes rise { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform:none; } }

.sf-avatar { flex:none; width:32px; height:32px; border-radius:50%; margin-top:2px;
  display:grid; place-items:center;
  background: linear-gradient(145deg, #e6c878, #c9a24c);
  box-shadow: 0 4px 14px rgba(216,177,90,0.25);
}

.sf-bubble { max-width: 76%; padding: 14px 17px; border-radius: 18px; font-size: 0.97rem; line-height: 1.58; }
.sf-bubble p { margin:0; white-space: pre-wrap; }
.sf-bubble.bot {
  background: rgba(255,255,255,0.035);
  border:1px solid rgba(216,177,90,0.14);
  border-top-left-radius:6px;
  color:#ece6d9;
}
.sf-bubble.user {
  background: linear-gradient(145deg, rgba(216,177,90,0.95), rgba(201,162,76,0.92));
  color:#1a1505; font-weight:500; border-top-right-radius:6px;
  box-shadow: 0 6px 20px rgba(216,177,90,0.18);
}

.sf-tag { display:flex; align-items:center; gap:7px; margin-top:11px; padding-top:10px;
  border-top:1px solid rgba(216,177,90,0.12); font-size:0.72rem; color:#9c9276; }
.sf-tag-dot { width:7px; height:7px; border-radius:50%; background:#d8b15a; box-shadow:0 0 8px #d8b15a; }
.sf-tag-topic { color:#7f765f; }

.sf-typing { display:flex; gap:5px; align-items:center; }
.sf-typing span { width:7px; height:7px; border-radius:50%; background:#d8b15a; opacity:0.5; animation: blink 1.2s infinite; }
.sf-typing span:nth-child(2){ animation-delay:.2s; } .sf-typing span:nth-child(3){ animation-delay:.4s; }
@keyframes blink { 0%,60%,100%{ opacity:.25; transform:translateY(0);} 30%{ opacity:1; transform:translateY(-3px);} }

.sf-suggest { display:flex; flex-wrap:wrap; gap:10px; margin: 22px 0 8px 44px; }
.sf-chip {
  font-family:'Outfit'; font-size:0.84rem; color:#e8dcc0;
  padding:10px 15px; border-radius:13px; cursor:pointer;
  background: rgba(255,255,255,0.03); border:1px solid rgba(216,177,90,0.2);
  transition: all .2s ease;
}
.sf-chip:hover { background: rgba(216,177,90,0.12); border-color: rgba(216,177,90,0.5); transform: translateY(-1px); }

.sf-foot { position:relative; z-index:2; padding: 12px 22px 16px;
  border-top:1px solid rgba(216,177,90,0.14); background: rgba(11,11,8,0.7); backdrop-filter: blur(8px); }
.sf-notice { max-width:820px; margin:0 auto 10px; font-size:0.78rem; color:#e7b96a;
  background:rgba(216,177,90,0.08); border:1px solid rgba(216,177,90,0.25); padding:9px 13px; border-radius:11px; }
.sf-composer { max-width:820px; margin:0 auto; display:flex; gap:10px; align-items:flex-end;
  background: rgba(255,255,255,0.04); border:1px solid rgba(216,177,90,0.25); border-radius:16px; padding:8px 8px 8px 16px; }
.sf-composer:focus-within { border-color: rgba(216,177,90,0.6); box-shadow: 0 0 0 3px rgba(216,177,90,0.08); }
.sf-composer textarea {
  flex:1; resize:none; border:none; outline:none; background:transparent; color:#f1ece1;
  font-family:'Outfit'; font-size:0.97rem; line-height:1.5; padding:8px 0; max-height:160px;
}
.sf-composer textarea::placeholder { color:#8a8169; }
.sf-send { flex:none; width:42px; height:42px; border:none; border-radius:12px; cursor:pointer;
  background: linear-gradient(145deg, #e6c878, #c9a24c); display:grid; place-items:center; transition: all .2s; }
.sf-send:hover:not(:disabled) { transform: translateY(-1px); box-shadow:0 6px 18px rgba(216,177,90,0.3); }
.sf-send:disabled { opacity:0.4; cursor:not-allowed; }
.sf-disclaimer { max-width:820px; margin:10px auto 0; font-size:0.7rem; color:#7d745d; text-align:center; line-height:1.5; }

@media (max-width:560px){
  .sf-bubble{ max-width:86%; } .sf-pill{ display:none; }
  .sf-suggest{ margin-left:0; } .sf-name{ font-size:1.15rem; }
}
`;
