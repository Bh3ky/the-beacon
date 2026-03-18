```js
import { useState } from "react";

const COLORS = {
  bg: "#0D0B08",
  surface: "#110E0B",
  surfaceHover: "#171210",
  border: "#1E1A16",
  borderLight: "#2A2218",
  orange: "#E8521A",
  orangeDim: "#9E3A12",
  text: "#F0EBE3",
  textMuted: "#7A6255",
  textDim: "#4D3E33",
  textFaint: "#2E2420",
};

const INDENT_COLORS = ["#E8521A", "#C4782A", "#8B6B3D", "#5C4E3A", "#3D3530"];

const SAMPLE_POST = {
  title: "Why African founders should stop building for Silicon Valley and start building for Accra",
  domain: "medium.com",
  points: 241,
  author: "kofi_atta",
  time: "8 hours ago",
  comment_count: 6,
};

const SAMPLE_COMMENTS = [
  {
    id: 1, author: "nairobidev", time: "7 hours ago", points: 84, depth: 0,
    text: "This is the most important essay I've read this year. We keep benchmarking ourselves against metrics designed for a completely different context — TAM calculations based on credit card penetration rates, growth curves that assume reliable internet, unit economics that ignore agent networks and cash-based markets. The frameworks themselves are the problem.",
    replies: [
      {
        id: 2, author: "builderzw", time: "6 hours ago", points: 47, depth: 1,
        text: "Exactly. I pitched to a London-based VC last month and spent 20 minutes explaining why our churn numbers look different when your primary distribution is through USSD. They kept asking when we'd move to a 'proper app'. That question itself reveals the blind spot.",
        replies: [
          {
            id: 3, author: "kofi_atta", time: "5 hours ago", points: 31, depth: 2,
            text: "That's the author here — this is precisely the scenario I had in mind writing this. The USSD channel serves 400M people who will never be on a smartphone. That's not a stepping stone, that's the market.",
            replies: [],
          }
        ],
      },
      {
        id: 4, author: "cairo_startup", time: "6 hours ago", points: 22, depth: 1,
        text: "Strong agree from the MENA side. Egypt has 105M people, mobile penetration is 94%, but smartphone penetration is 45%. Half our market doesn't exist in the metrics VCs look at. We built our whole stack around feature phones and it's our biggest competitive moat.",
        replies: [],
      }
    ],
  },
  {
    id: 5, author: "fintech_ng", time: "7 hours ago", points: 63, depth: 0,
    text: "The irony is that African founders who 'build for Accra' end up with better businesses. Lower burn, stronger retention, real revenue from day one. They just can't raise because the pitch doesn't fit the pattern-matching. The incentives are broken not the founders.",
    replies: [
      {
        id: 6, author: "talentwatch", time: "4 hours ago", points: 18, depth: 1,
        text: "This is the crux of it. The fundraising market and the product market are misaligned. Solve for the product market first — the fundraising will come once the numbers are undeniable. Chipper, Wave, Moniepoint all did this.",
        replies: [],
      }
    ],
  },
];

function timeAgo(t) { return t; }

function CommentBox({ onSubmit, onCancel, placeholder = "Share your perspective...", autoFocus = false }) {
  const [text, setText] = useState("");
  return (
    <div style={{ marginTop: "8px" }}>
      <textarea
        autoFocus={autoFocus}
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder={placeholder}
        rows={4}
        style={{
          width: "100%", background: "#0D0B08",
          border: `1px solid ${COLORS.borderLight}`,
          borderRadius: "4px", color: COLORS.text,
          fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px",
          padding: "10px 12px", resize: "vertical", outline: "none",
          lineHeight: 1.6,
          transition: "border-color 0.15s",
        }}
        onFocus={e => e.target.style.borderColor = COLORS.orange}
        onBlur={e => e.target.style.borderColor = COLORS.borderLight}
      />
      <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
        <button
          onClick={() => { if (text.trim()) { onSubmit(text); setText(""); } }}
          style={{
            background: COLORS.orange, border: "none", cursor: "pointer",
            color: "#0D0B08", fontFamily: "'IBM Plex Mono', monospace",
            fontSize: "11px", fontWeight: 700, padding: "6px 14px", borderRadius: "3px",
            letterSpacing: "0.3px",
          }}
        >add comment</button>
        {onCancel && (
          <button onClick={onCancel} style={{
            background: "none", border: `1px solid ${COLORS.border}`,
            cursor: "pointer", color: COLORS.textMuted,
            fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px",
            padding: "6px 12px", borderRadius: "3px",
          }}>cancel</button>
        )}
      </div>
    </div>
  );
}

function Comment({ comment, depth = 0 }) {
  const [voted, setVoted] = useState(false);
  const [points, setPoints] = useState(comment.points);
  const [replying, setReplying] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [replies, setReplies] = useState(comment.replies || []);
  const indentColor = INDENT_COLORS[Math.min(depth, INDENT_COLORS.length - 1)];

  const handleReply = (text) => {
    setReplies(prev => [...prev, {
      id: Date.now(), author: "you", time: "just now",
      points: 1, depth: depth + 1, text, replies: [],
    }]);
    setReplying(false);
  };

  return (
    <div style={{
      display: "flex", gap: "0",
      marginBottom: "2px",
      opacity: collapsed ? 0.6 : 1,
      transition: "opacity 0.2s",
    }}>
      {/* Indent line */}
      {depth > 0 && (
        <div style={{
          width: "20px", minWidth: "20px",
          display: "flex", justifyContent: "center",
          paddingTop: "2px",
        }}>
          <div style={{
            width: "1px", background: indentColor,
            opacity: 0.25, borderRadius: "1px",
            cursor: "pointer",
          }}
            onClick={() => setCollapsed(!collapsed)}
          />
        </div>
      )}

      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Comment header */}
        <div style={{
          display: "flex", alignItems: "center", gap: "10px",
          flexWrap: "wrap", marginBottom: collapsed ? 0 : "6px",
        }}>
          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{
              background: "none", border: "none", cursor: "pointer",
              color: COLORS.textDim, fontFamily: "'IBM Plex Mono', monospace",
              fontSize: "10px", padding: "0", lineHeight: 1,
            }}
          >{collapsed ? "[+]" : "[–]"}</button>

          <span style={{
            color: comment.author === "kofi_atta" ? COLORS.orange : COLORS.textMuted,
            fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px", fontWeight: 700,
          }}>{comment.author}</span>

          {comment.author === "kofi_atta" && (
            <span style={{
              background: "#2e1a0a", color: COLORS.orange,
              fontFamily: "'IBM Plex Mono', monospace", fontSize: "9px",
              padding: "1px 5px", borderRadius: "2px", letterSpacing: "0.5px",
            }}>author</span>
          )}

          <span style={{ color: COLORS.textDim, fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px" }}>
            {timeAgo(comment.time)}
          </span>

          {/* Vote */}
          <div style={{ display: "flex", alignItems: "center", gap: "4px", marginLeft: "2px" }}>
            <button
              onClick={() => { if (!voted) { setVoted(true); setPoints(p => p + 1); } }}
              style={{
                background: "none", border: "none", cursor: voted ? "default" : "pointer",
                color: voted ? COLORS.orange : COLORS.textDim,
                fontSize: "11px", padding: "0", lineHeight: 1,
                transition: "color 0.15s, transform 0.1s",
                transform: voted ? "scale(1.3)" : "scale(1)",
              }}>▲</button>
            <span style={{
              color: voted ? COLORS.orange : COLORS.textDim,
              fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px",
            }}>{points}</span>
          </div>
        </div>

        {/* Comment body */}
        {!collapsed && (
          <>
            <p style={{
              color: COLORS.text, fontFamily: "'DM Serif Display', serif",
              fontSize: "14px", lineHeight: 1.7, margin: "0 0 8px 0",
              letterSpacing: "0.1px",
            }}>{comment.text}</p>

            {/* Actions */}
            <div style={{ display: "flex", gap: "14px", marginBottom: "10px" }}>
              {["reply", "share", "flag"].map(action => (
                <button key={action}
                  onClick={() => action === "reply" && setReplying(!replying)}
                  style={{
                    background: "none", border: "none", cursor: "pointer",
                    color: replying && action === "reply" ? COLORS.orange : COLORS.textDim,
                    fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px",
                    padding: "0", letterSpacing: "0.3px",
                    transition: "color 0.15s",
                  }}
                  onMouseEnter={e => e.target.style.color = COLORS.orange}
                  onMouseLeave={e => e.target.style.color = replying && action === "reply" ? COLORS.orange : COLORS.textDim}
                >{action}</button>
              ))}
            </div>

            {/* Reply box */}
            {replying && (
              <CommentBox
                autoFocus
                placeholder={`Replying to ${comment.author}...`}
                onSubmit={handleReply}
                onCancel={() => setReplying(false)}
              />
            )}

            {/* Nested replies */}
            {replies.length > 0 && (
              <div style={{ marginTop: "8px" }}>
                {replies.map(reply => (
                  <Comment key={reply.id} comment={reply} depth={depth + 1} />
                ))}
              </div>
            )}
          </>
        )}

        {collapsed && replies.length > 0 && (
          <span style={{
            color: COLORS.textDim, fontFamily: "'IBM Plex Mono', monospace",
            fontSize: "10px", marginLeft: "4px",
          }}>{replies.length} repl{replies.length === 1 ? "y" : "ies"} hidden</span>
        )}
      </div>
    </div>
  );
}

export default function BeaconComments() {
  const [allComments, setAllComments] = useState(SAMPLE_COMMENTS);
  const [postVoted, setPostVoted] = useState(false);
  const [postPoints, setPostPoints] = useState(SAMPLE_POST.points);

  const handleTopLevel = (text) => {
    setAllComments(prev => [{
      id: Date.now(), author: "you", time: "just now",
      points: 1, depth: 0, text, replies: [],
    }, ...prev]);
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=IBM+Plex+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: #0D0B08; }
        ::-webkit-scrollbar-thumb { background: #2A2218; border-radius: 3px; }
      `}</style>

      <div style={{ background: COLORS.bg, minHeight: "100vh", padding: "0 0 80px" }}>

        {/* Nav */}
        <nav style={{
          background: COLORS.orange, padding: "0 24px",
          display: "flex", alignItems: "center", gap: "16px", height: "44px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{
              width: "24px", height: "24px", background: "#0D0B08",
              display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "3px",
            }}>
              <span style={{ color: COLORS.orange, fontFamily: "'DM Serif Display', serif", fontSize: "13px" }}>B</span>
            </div>
            <span style={{ color: "#0D0B08", fontFamily: "'DM Serif Display', serif", fontSize: "17px", fontWeight: 700 }}>The Beacon</span>
          </div>
          <span style={{ color: "rgba(0,0,0,0.4)", fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px" }}>|</span>
          <span style={{ color: "rgba(0,0,0,0.55)", fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px" }}>
            {SAMPLE_POST.comment_count + allComments.length - SAMPLE_COMMENTS.length} comments
          </span>
          <a href="#" style={{
            marginLeft: "auto", color: "rgba(0,0,0,0.55)",
            fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px", textDecoration: "none",
          }}>← back</a>
        </nav>

        <div style={{ maxWidth: "720px", margin: "0 auto", padding: "28px 20px 0" }}>

          {/* Post header */}
          <div style={{
            borderBottom: `1px solid ${COLORS.border}`,
            paddingBottom: "20px", marginBottom: "24px",
          }}>
            <h1 style={{
              fontFamily: "'DM Serif Display', serif",
              fontSize: "22px", color: COLORS.text,
              lineHeight: 1.35, letterSpacing: "-0.2px",
              marginBottom: "10px",
            }}>{SAMPLE_POST.title}</h1>

            <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                <button
                  onClick={() => { if (!postVoted) { setPostVoted(true); setPostPoints(p => p + 1); }}}
                  style={{
                    background: "none", border: "none", cursor: postVoted ? "default" : "pointer",
                    color: postVoted ? COLORS.orange : COLORS.textDim, fontSize: "13px",
                    transition: "color 0.15s, transform 0.1s",
                    transform: postVoted ? "scale(1.2)" : "scale(1)",
                  }}>▲</button>
                <span style={{
                  color: postVoted ? COLORS.orange : COLORS.textMuted,
                  fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px",
                }}>{postPoints}</span>
              </div>
              <span style={{ color: COLORS.textDim, fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px" }}>
                by <span style={{ color: COLORS.textMuted }}>{SAMPLE_POST.author}</span>
              </span>
              <span style={{ color: COLORS.textDim, fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px" }}>
                {SAMPLE_POST.time}
              </span>
              <a href="#" style={{
                color: COLORS.textDim, fontFamily: "'IBM Plex Mono', monospace",
                fontSize: "11px", textDecoration: "none",
              }}
                onMouseEnter={e => e.target.style.color = COLORS.orange}
                onMouseLeave={e => e.target.style.color = COLORS.textDim}
              >({SAMPLE_POST.domain}) →</a>
            </div>
          </div>

          {/* Top-level comment box */}
          <div style={{ marginBottom: "28px" }}>
            <p style={{
              fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px",
              color: COLORS.textDim, marginBottom: "8px", letterSpacing: "0.5px",
              textTransform: "uppercase",
            }}>add to the conversation</p>
            <CommentBox onSubmit={handleTopLevel} />
          </div>

          {/* Comment count */}
          <div style={{
            display: "flex", alignItems: "center", gap: "12px",
            marginBottom: "16px",
          }}>
            <span style={{
              fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px",
              color: COLORS.textDim, letterSpacing: "0.5px", textTransform: "uppercase",
            }}>{allComments.length + allComments.reduce((a, c) => a + c.replies.length + c.replies.reduce((b, r) => b + r.replies.length, 0), 0)} comments</span>
            <div style={{ flex: 1, height: "1px", background: COLORS.border }} />
          </div>

          {/* Comments */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {allComments.map(comment => (
              <div key={comment.id} style={{
                background: COLORS.surface,
                border: `1px solid ${COLORS.border}`,
                borderRadius: "4px", padding: "14px 16px",
                transition: "border-color 0.15s",
              }}
                onMouseEnter={e => e.currentTarget.style.borderColor = COLORS.borderLight}
                onMouseLeave={e => e.currentTarget.style.borderColor = COLORS.border}
              >
                <Comment comment={comment} depth={0} />
              </div>
            ))}
          </div>

        </div>
      </div>
    </>
  );
}
```