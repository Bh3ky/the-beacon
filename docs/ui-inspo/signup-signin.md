
```js
import { useState } from "react";

const C = {
  bg: "#0D0B08",
  surface: "#110E0B",
  border: "#1E1A16",
  borderLight: "#2A2218",
  orange: "#E8521A",
  orangeHover: "#FF6B35",
  orangeDim: "#7A2E0E",
  text: "#F0EBE3",
  textMuted: "#7A6255",
  textDim: "#4D3E33",
  error: "#F87171",
  success: "#4ade80",
};

const BEACON_STATS = [
  { value: "2,847", label: "builders" },
  { value: "38", label: "countries" },
  { value: "143", label: "posts today" },
];

const TESTIMONIALS = [
  { text: "First place I check every morning for what's moving in African tech.", author: "nairobidev", country: "🇰🇪" },
  { text: "Finally a signal feed that actually understands our market context.", author: "kofi_atta", country: "🇬🇭" },
  { text: "Found my last two hires through Beacon job listings.", author: "builderzw", country: "🇿🇼" },
];

function Input({ label, type = "text", value, onChange, placeholder, error, hint }) {
  const [focused, setFocused] = useState(false);
  const [show, setShow] = useState(false);
  const isPassword = type === "password";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <label style={{
          fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px",
          color: focused ? C.orange : C.textMuted,
          letterSpacing: "1px", textTransform: "uppercase",
          transition: "color 0.15s",
        }}>{label}</label>
        {hint && (
          <span style={{
            fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px", color: C.textDim,
          }}>{hint}</span>
        )}
      </div>
      <div style={{ position: "relative" }}>
        <input
          type={isPassword && show ? "text" : type}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width: "100%", background: focused ? "#130F0C" : C.bg,
            border: `1px solid ${error ? C.error : focused ? C.orange : C.border}`,
            borderRadius: "4px", color: C.text,
            fontFamily: "'IBM Plex Mono', monospace", fontSize: "13px",
            padding: isPassword ? "11px 40px 11px 14px" : "11px 14px",
            outline: "none", transition: "all 0.15s",
            letterSpacing: "0.2px",
          }}
          autoComplete={isPassword ? "current-password" : type === "email" ? "email" : "username"}
        />
        {isPassword && (
          <button
            onClick={() => setShow(!show)}
            style={{
              position: "absolute", right: "12px", top: "50%",
              transform: "translateY(-50%)",
              background: "none", border: "none", cursor: "pointer",
              color: C.textDim, fontSize: "11px",
              fontFamily: "'IBM Plex Mono', monospace",
              transition: "color 0.15s",
            }}
            onMouseEnter={e => e.target.style.color = C.orange}
            onMouseLeave={e => e.target.style.color = C.textDim}
          >{show ? "hide" : "show"}</button>
        )}
      </div>
      {error && (
        <span style={{
          fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px",
          color: C.error, letterSpacing: "0.3px",
        }}>↳ {error}</span>
      )}
    </div>
  );
}

function StrengthBar({ password }) {
  const getStrength = (p) => {
    if (!p) return 0;
    let score = 0;
    if (p.length >= 8) score++;
    if (p.length >= 12) score++;
    if (/[A-Z]/.test(p)) score++;
    if (/[0-9]/.test(p)) score++;
    if (/[^A-Za-z0-9]/.test(p)) score++;
    return score;
  };

  const strength = getStrength(password);
  const labels = ["", "weak", "fair", "good", "strong", "very strong"];
  const colors = ["", "#F87171", "#fb923c", "#facc15", "#4ade80", "#4ade80"];

  if (!password) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
      <div style={{ display: "flex", gap: "3px" }}>
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} style={{
            flex: 1, height: "2px", borderRadius: "2px",
            background: i <= strength ? colors[strength] : C.border,
            transition: "background 0.3s",
          }} />
        ))}
      </div>
      <span style={{
        fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px",
        color: colors[strength], letterSpacing: "0.5px",
        transition: "color 0.3s",
      }}>{labels[strength]}</span>
    </div>
  );
}

function SignInForm({ onSwitch }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = () => {
    const errs = {};
    if (!username.trim()) errs.username = "Username is required";
    if (!password) errs.password = "Password is required";
    setErrors(errs);
    if (Object.keys(errs).length) return;

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
    }, 1400);
  };

  if (success) {
    return (
      <div style={{
        display: "flex", flexDirection: "column", alignItems: "center",
        gap: "16px", padding: "40px 0", textAlign: "center",
      }}>
        <div style={{
          width: "48px", height: "48px",
          background: "#1a2e1a", borderRadius: "50%",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "22px",
        }}>✓</div>
        <p style={{
          fontFamily: "'DM Serif Display', serif", fontSize: "20px", color: C.text,
        }}>Welcome back to The Beacon</p>
        <p style={{
          fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px", color: C.textDim,
        }}>Redirecting you to the feed...</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <Input label="Username" value={username} onChange={setUsername}
        placeholder="your_username" error={errors.username} />
      <Input label="Password" type="password" value={password} onChange={setPassword}
        placeholder="••••••••" error={errors.password}
        hint={<span style={{ cursor: "pointer", color: C.textDim }}
          onMouseEnter={e => e.target.style.color = C.orange}
          onMouseLeave={e => e.target.style.color = C.textDim}>forgot?</span>}
      />

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          background: loading ? C.orangeDim : C.orange,
          border: "none", cursor: loading ? "wait" : "pointer",
          color: "#0D0B08", fontFamily: "'IBM Plex Mono', monospace",
          fontSize: "12px", fontWeight: 700, padding: "13px",
          borderRadius: "4px", letterSpacing: "1px",
          textTransform: "uppercase", transition: "all 0.15s",
          display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
        }}
        onMouseEnter={e => { if (!loading) e.target.style.background = C.orangeHover; }}
        onMouseLeave={e => { if (!loading) e.target.style.background = C.orange; }}
      >
        {loading ? (
          <>
            <span style={{
              width: "12px", height: "12px", border: "2px solid #0D0B08",
              borderTopColor: "transparent", borderRadius: "50%",
              display: "inline-block",
              animation: "spin 0.7s linear infinite",
            }} />
            signing in...
          </>
        ) : "sign in →"}
      </button>

      <p style={{
        fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px",
        color: C.textDim, textAlign: "center",
      }}>
        New to The Beacon?{" "}
        <span onClick={onSwitch} style={{
          color: C.orange, cursor: "pointer", textDecoration: "underline",
          textUnderlineOffset: "3px",
        }}>create an account</span>
      </p>
    </div>
  );
}

function SignUpForm({ onSwitch }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const validate = () => {
    const errs = {};
    if (!username.trim()) errs.username = "Username is required";
    else if (!/^[a-zA-Z0-9_-]{3,50}$/.test(username)) errs.username = "Letters, numbers, _ and - only (3–50 chars)";
    if (!email.trim()) errs.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errs.email = "Enter a valid email";
    if (!password) errs.password = "Password is required";
    else if (password.length < 8) errs.password = "At least 8 characters required";
    return errs;
  };

  const handleSubmit = () => {
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setLoading(true);
    setTimeout(() => { setLoading(false); setSuccess(true); }, 1600);
  };

  if (success) {
    return (
      <div style={{
        display: "flex", flexDirection: "column", alignItems: "center",
        gap: "16px", padding: "40px 0", textAlign: "center",
      }}>
        <div style={{
          width: "48px", height: "48px",
          background: "#1a2e1a", borderRadius: "50%",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "22px",
        }}>🏮</div>
        <p style={{ fontFamily: "'DM Serif Display', serif", fontSize: "20px", color: C.text }}>
          Welcome to The Beacon, {username}
        </p>
        <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px", color: C.textDim }}>
          Your account is ready. Taking you to the feed...
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
      <Input label="Username" value={username} onChange={setUsername}
        placeholder="your_username" error={errors.username}
        hint="visible to everyone" />
      <Input label="Email" type="email" value={email} onChange={setEmail}
        placeholder="you@example.com" error={errors.email}
        hint="never shown publicly" />
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <Input label="Password" type="password" value={password} onChange={setPassword}
          placeholder="••••••••" error={errors.password} />
        <StrengthBar password={password} />
      </div>

      <p style={{
        fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px",
        color: C.textDim, lineHeight: 1.6, letterSpacing: "0.2px",
      }}>
        By joining you agree to The Beacon's{" "}
        <span style={{ color: C.textMuted, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: "2px" }}>
          community guidelines
        </span>
        . We don't sell your data. Ever.
      </p>

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          background: loading ? C.orangeDim : C.orange,
          border: "none", cursor: loading ? "wait" : "pointer",
          color: "#0D0B08", fontFamily: "'IBM Plex Mono', monospace",
          fontSize: "12px", fontWeight: 700, padding: "13px",
          borderRadius: "4px", letterSpacing: "1px",
          textTransform: "uppercase", transition: "all 0.15s",
          display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
        }}
        onMouseEnter={e => { if (!loading) e.target.style.background = C.orangeHover; }}
        onMouseLeave={e => { if (!loading) e.target.style.background = C.orange; }}
      >
        {loading ? (
          <>
            <span style={{
              width: "12px", height: "12px", border: "2px solid #0D0B08",
              borderTopColor: "transparent", borderRadius: "50%",
              display: "inline-block",
              animation: "spin 0.7s linear infinite",
            }} />
            creating account...
          </>
        ) : "join the beacon →"}
      </button>

      <p style={{
        fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px",
        color: C.textDim, textAlign: "center",
      }}>
        Already a member?{" "}
        <span onClick={onSwitch} style={{
          color: C.orange, cursor: "pointer", textDecoration: "underline",
          textUnderlineOffset: "3px",
        }}>sign in</span>
      </p>
    </div>
  );
}

export default function BeaconAuth() {
  const [mode, setMode] = useState("signin"); // "signin" | "signup"
  const [testimonialIdx, setTestimonialIdx] = useState(0);

  const t = TESTIMONIALS[testimonialIdx];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }
      `}</style>

      <div style={{
        background: C.bg, minHeight: "100vh",
        display: "flex", flexDirection: "column",
        fontFamily: "'IBM Plex Mono', monospace",
      }}>

        {/* Top bar */}
        <nav style={{
          padding: "16px 28px", display: "flex",
          alignItems: "center", justifyContent: "space-between",
          borderBottom: `1px solid ${C.border}`,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "28px", height: "28px", background: C.orange,
              display: "flex", alignItems: "center", justifyContent: "center",
              borderRadius: "4px",
            }}>
              <span style={{
                color: "#0D0B08", fontFamily: "'DM Serif Display', serif",
                fontSize: "16px", fontWeight: 700,
              }}>B</span>
            </div>
            <span style={{
              color: C.text, fontFamily: "'DM Serif Display', serif",
              fontSize: "18px", letterSpacing: "-0.3px",
            }}>The Beacon</span>
          </div>
          <span style={{ color: C.textDim, fontSize: "11px" }}>thebeacon.africa</span>
        </nav>

        {/* Main layout */}
        <div style={{
          flex: 1, display: "flex",
          alignItems: "stretch",
        }}>

          {/* Left panel — branding */}
          <div style={{
            flex: 1, display: "flex", flexDirection: "column",
            justifyContent: "space-between",
            padding: "52px 48px",
            borderRight: `1px solid ${C.border}`,
            position: "relative", overflow: "hidden",
          }}>
            {/* Background texture */}
            <div style={{
              position: "absolute", inset: 0, opacity: 0.03,
              backgroundImage: `repeating-linear-gradient(
                0deg, transparent, transparent 24px,
                #E8521A 24px, #E8521A 25px
              ), repeating-linear-gradient(
                90deg, transparent, transparent 24px,
                #E8521A 24px, #E8521A 25px
              )`,
            }} />

            {/* Glow */}
            <div style={{
              position: "absolute", bottom: "-80px", left: "-80px",
              width: "360px", height: "360px",
              background: "radial-gradient(circle, rgba(232,82,26,0.08) 0%, transparent 70%)",
              pointerEvents: "none",
            }} />

            <div style={{ position: "relative", zIndex: 1 }}>
              <p style={{
                fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px",
                color: C.orange, letterSpacing: "2px",
                textTransform: "uppercase", marginBottom: "20px",
              }}>thebeacon.africa</p>

              <h1 style={{
                fontFamily: "'DM Serif Display', serif",
                fontSize: "38px", color: C.text,
                lineHeight: 1.25, letterSpacing: "-0.5px",
                marginBottom: "16px",
              }}>
                Africa's tech<br />
                <span style={{ fontStyle: "italic", color: C.orange }}>conversation</span>,<br />
                ranked by the<br />community.
              </h1>

              <p style={{
                fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px",
                color: C.textMuted, lineHeight: 1.7, maxWidth: "320px",
              }}>
                One feed. No algorithm manipulation. Community-curated signal from builders, founders, and operators across the continent.
              </p>
            </div>

            {/* Stats */}
            <div style={{
              position: "relative", zIndex: 1,
              display: "flex", gap: "28px", marginTop: "40px",
            }}>
              {BEACON_STATS.map(s => (
                <div key={s.label} style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
                  <span style={{
                    fontFamily: "'DM Serif Display', serif",
                    fontSize: "24px", color: C.orange,
                  }}>{s.value}</span>
                  <span style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontSize: "10px", color: C.textDim, letterSpacing: "0.5px",
                  }}>{s.label}</span>
                </div>
              ))}
            </div>

            {/* Testimonial */}
            <div style={{
              position: "relative", zIndex: 1,
              border: `1px solid ${C.border}`, borderRadius: "6px",
              padding: "18px 20px", marginTop: "32px",
              background: "rgba(17,14,11,0.6)",
              animation: "fadeUp 0.4s ease",
              key: testimonialIdx,
            }}>
              <p style={{
                fontFamily: "'DM Serif Display', serif", fontStyle: "italic",
                fontSize: "14px", color: C.text, lineHeight: 1.65,
                marginBottom: "12px",
              }}>"{t.text}"</p>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "14px" }}>{t.country}</span>
                <span style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: "11px", color: C.orange,
                }}>@{t.author}</span>
              </div>
            </div>

            {/* Testimonial dots */}
            <div style={{ display: "flex", gap: "6px", marginTop: "12px" }}>
              {TESTIMONIALS.map((_, i) => (
                <button key={i} onClick={() => setTestimonialIdx(i)} style={{
                  width: i === testimonialIdx ? "20px" : "6px",
                  height: "6px", borderRadius: "3px",
                  background: i === testimonialIdx ? C.orange : C.border,
                  border: "none", cursor: "pointer",
                  transition: "all 0.25s",
                }} />
              ))}
            </div>
          </div>

          {/* Right panel — form */}
          <div style={{
            width: "420px", minWidth: "420px",
            display: "flex", flexDirection: "column",
            justifyContent: "center",
            padding: "48px 44px",
          }}>

            {/* Tab switcher */}
            <div style={{
              display: "flex", marginBottom: "36px",
              borderBottom: `1px solid ${C.border}`,
            }}>
              {["signin", "signup"].map(tab => (
                <button key={tab} onClick={() => setMode(tab)} style={{
                  flex: 1, background: "none", border: "none",
                  cursor: "pointer", padding: "0 0 12px",
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: "12px", letterSpacing: "0.5px",
                  color: mode === tab ? C.orange : C.textDim,
                  borderBottom: `2px solid ${mode === tab ? C.orange : "transparent"}`,
                  marginBottom: "-1px",
                  transition: "all 0.15s",
                  textTransform: "lowercase",
                }}>
                  {tab === "signin" ? "sign in" : "create account"}
                </button>
              ))}
            </div>

            {/* Heading */}
            <div style={{ marginBottom: "28px" }}>
              <h2 style={{
                fontFamily: "'DM Serif Display', serif",
                fontSize: "26px", color: C.text,
                letterSpacing: "-0.3px", marginBottom: "6px",
              }}>
                {mode === "signin" ? "Welcome back" : "Join The Beacon"}
              </h2>
              <p style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: "11px", color: C.textDim, lineHeight: 1.5,
              }}>
                {mode === "signin"
                  ? "Sign in to vote, comment, and submit posts."
                  : "Free to join. Be part of the conversation shaping African tech."}
              </p>
            </div>

            {/* Form */}
            <div style={{ animation: "fadeUp 0.25s ease" }} key={mode}>
              {mode === "signin"
                ? <SignInForm onSwitch={() => setMode("signup")} />
                : <SignUpForm onSwitch={() => setMode("signin")} />
              }
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div style={{
          borderTop: `1px solid ${C.border}`,
          padding: "14px 28px",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          flexWrap: "wrap", gap: "8px",
        }}>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px", color: C.textDim }}>
            © 2026 The Beacon · Built for African builders
          </span>
          <div style={{ display: "flex", gap: "20px" }}>
            {["guidelines", "privacy", "contact"].map(link => (
              <a key={link} href="#" style={{
                fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px",
                color: C.textDim, textDecoration: "none",
                transition: "color 0.15s",
              }}
                onMouseEnter={e => e.target.style.color = C.orange}
                onMouseLeave={e => e.target.style.color = C.textDim}
              >{link}</a>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

```