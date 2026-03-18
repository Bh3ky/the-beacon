```js
import { useState } from "react";

const posts = [
  { id: 1, title: "Flutterwave raises $17M to expand payment infrastructure across West Africa", domain: "techcrunch.com", points: 312, author: "builderzw", time: "4 hours ago", comments: 87, category: "funding" },
  { id: 2, title: "Show Rift: I built an open-source M-Pesa SDK for Node.js developers", domain: "github.com", points: 284, author: "nairobidev", time: "6 hours ago", comments: 63, category: "show" },
  { id: 3, title: "Why African founders should stop building for Silicon Valley and start building for Accra", domain: "medium.com", points: 241, author: "kofi_atta", time: "8 hours ago", comments: 112, category: "opinion" },
  { id: 4, title: "Nigeria's SEC releases updated framework for crypto regulation in 2025", domain: "sec.gov.ng", points: 198, author: "fintech_ng", time: "10 hours ago", comments: 45, category: "policy" },
  { id: 5, title: "Ask Rift: Best local cloud hosting options for early-stage African startups?", domain: null, points: 176, author: "bheki_dev", time: "11 hours ago", comments: 94, category: "ask" },
  { id: 6, title: "Andela is now placing engineers across 100+ African companies — the model has shifted", domain: "andela.com", points: 154, author: "talentwatch", time: "13 hours ago", comments: 38, category: "news" },
  { id: 7, title: "The infrastructure problem: why payments still fail at 2AM across the continent", domain: "substack.com", points: 143, author: "infrabuilder", time: "14 hours ago", comments: 71, category: "opinion" },
  { id: 8, title: "Show Rift: Rift — a Hacker News for African tech (we're building this live)", domain: "getrift.africa", points: 398, author: "bheki_dev", time: "just now", comments: 0, category: "show" },
  { id: 9, title: "Egypt's fintech Paymob crosses 250k merchants — largest POS network in MENA-Africa", domain: "paymob.com", points: 129, author: "cairo_startup", time: "16 hours ago", comments: 29, category: "funding" },
  { id: 10, title: "Job: Senior Backend Engineer at Chipper Cash — Remote, Africa-based preferred", domain: "chippercash.com", points: 88, author: "chipperhiring", time: "18 hours ago", comments: 14, category: "job" },
];

const categoryColors = {
  funding: { bg: "#1a2e1a", text: "#4ade80", label: "funding" },
  show: { bg: "#2e1a0a", text: "#fb923c", label: "show rift" },
  ask: { bg: "#0a1a2e", text: "#60a5fa", label: "ask rift" },
  opinion: { bg: "#2a1a2e", text: "#c084fc", label: "opinion" },
  policy: { bg: "#2e2a0a", text: "#facc15", label: "policy" },
  news: { bg: "#1a1a1a", text: "#a1a1aa", label: "news" },
  job: { bg: "#2e1a1a", text: "#f87171", label: "job" },
};

const NavBar = ({ activeTab, setActiveTab }) => {
  const tabs = ["top", "new", "ask", "show", "jobs"];
  return (
    <nav style={{
      background: "#E8521A",
      padding: "0 24px",
      display: "flex",
      alignItems: "center",
      gap: "24px",
      height: "44px",
      position: "sticky",
      top: 0,
      zIndex: 100,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginRight: "8px" }}>
        <div style={{
          width: "26px", height: "26px",
          background: "#0D0B08",
          display: "flex", alignItems: "center", justifyContent: "center",
          borderRadius: "3px",
        }}>
          <span style={{ color: "#E8521A", fontFamily: "'DM Serif Display', serif", fontWeight: 700, fontSize: "14px" }}>R</span>
        </div>
        <span style={{
          color: "#0D0B08", fontFamily: "'DM Serif Display', serif",
          fontWeight: 700, fontSize: "18px", letterSpacing: "-0.3px"
        }}>Rift</span>
      </div>

      {tabs.map(tab => (
        <button key={tab} onClick={() => setActiveTab(tab)} style={{
          background: "none", border: "none", cursor: "pointer",
          color: activeTab === tab ? "#0D0B08" : "rgba(0,0,0,0.55)",
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: "12px", fontWeight: activeTab === tab ? 700 : 400,
          padding: "2px 0", letterSpacing: "0.3px",
          borderBottom: activeTab === tab ? "2px solid #0D0B08" : "none",
          textTransform: "lowercase",
        }}>{tab}</button>
      ))}

      <div style={{ marginLeft: "auto", display: "flex", gap: "16px", alignItems: "center" }}>
        <button style={{
          background: "none", border: "none", cursor: "pointer",
          color: "rgba(0,0,0,0.6)", fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px"
        }}>submit</button>
        <button style={{
          background: "#0D0B08", border: "none", cursor: "pointer",
          color: "#E8521A", fontFamily: "'IBM Plex Mono', monospace",
          fontSize: "12px", padding: "5px 12px", borderRadius: "3px"
        }}>login</button>
      </div>
    </nav>
  );
};

const PostRow = ({ post, rank }) => {
  const [votes, setVotes] = useState(post.points);
  const [voted, setVoted] = useState(false);
  const cat = categoryColors[post.category] || categoryColors.news;

  return (
    <div style={{
      display: "flex", gap: "12px", alignItems: "flex-start",
      padding: "12px 0",
      borderBottom: "1px solid #1E1A16",
      transition: "background 0.15s",
    }}
      onMouseEnter={e => e.currentTarget.style.background = "#130F0C"}
      onMouseLeave={e => e.currentTarget.style.background = "transparent"}
    >
      {/* Rank */}
      <span style={{
        color: "#3D3028", fontFamily: "'IBM Plex Mono', monospace",
        fontSize: "12px", minWidth: "22px", textAlign: "right",
        paddingTop: "2px",
      }}>{rank}.</span>

      {/* Upvote */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "3px", paddingTop: "1px" }}>
        <button onClick={() => { if (!voted) { setVotes(v => v + 1); setVoted(true); } }}
          style={{
            background: "none", border: "none", cursor: voted ? "default" : "pointer",
            color: voted ? "#E8521A" : "#4D3E33",
            fontSize: "14px", lineHeight: 1, padding: "0",
            transition: "color 0.15s, transform 0.1s",
            transform: voted ? "scale(1.2)" : "scale(1)",
          }}>▲</button>
        <span style={{
          color: voted ? "#E8521A" : "#6B5245",
          fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px"
        }}>{votes}</span>
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "8px", flexWrap: "wrap" }}>
          {/* Category badge */}
          {post.category !== "news" && (
            <span style={{
              background: cat.bg, color: cat.text,
              fontFamily: "'IBM Plex Mono', monospace", fontSize: "9px",
              padding: "2px 6px", borderRadius: "2px", letterSpacing: "0.5px",
              textTransform: "uppercase", whiteSpace: "nowrap",
            }}>{cat.label}</span>
          )}
          <a href="#" style={{
            color: "#F0EBE3", fontFamily: "'DM Serif Display', serif",
            fontSize: "15px", textDecoration: "none", lineHeight: 1.3,
            letterSpacing: "-0.1px",
          }}
            onMouseEnter={e => e.target.style.color = "#E8521A"}
            onMouseLeave={e => e.target.style.color = "#F0EBE3"}
          >{post.title}</a>
          {post.domain && (
            <span style={{
              color: "#4D3E33", fontFamily: "'IBM Plex Mono', monospace",
              fontSize: "10px", whiteSpace: "nowrap"
            }}>({post.domain})</span>
          )}
        </div>
        <div style={{
          marginTop: "5px", display: "flex", gap: "12px", alignItems: "center",
          fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px", color: "#4D3E33",
          flexWrap: "wrap",
        }}>
          <span>by <span style={{ color: "#7A6255" }}>{post.author}</span></span>
          <span>{post.time}</span>
          <a href="#" style={{ color: "#4D3E33", textDecoration: "none" }}
            onMouseEnter={e => e.target.style.color = "#E8521A"}
            onMouseLeave={e => e.target.style.color = "#4D3E33"}
          >{post.comments} comment{post.comments !== 1 ? "s" : ""}</a>
          <a href="#" style={{ color: "#4D3E33", textDecoration: "none" }}
            onMouseEnter={e => e.target.style.color = "#E8521A"}
            onMouseLeave={e => e.target.style.color = "#4D3E33"}
          >hide</a>
        </div>
      </div>
    </div>
  );
};

const Stats = () => (
  <div style={{
    display: "flex", gap: "32px", padding: "16px 0",
    borderBottom: "1px solid #1E1A16", marginBottom: "4px",
    flexWrap: "wrap",
  }}>
    {[
      { label: "builders", value: "2,847" },
      { label: "posts today", value: "143" },
      { label: "countries", value: "38" },
      { label: "comments", value: "891" },
    ].map(s => (
      <div key={s.label} style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        <span style={{ color: "#E8521A", fontFamily: "'DM Serif Display', serif", fontSize: "20px" }}>{s.value}</span>
        <span style={{ color: "#4D3E33", fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px", letterSpacing: "0.5px" }}>{s.label}</span>
      </div>
    ))}
  </div>
);

export default function Rift() {
  const [activeTab, setActiveTab] = useState("top");

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=IBM+Plex+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0D0B08; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0D0B08; }
        ::-webkit-scrollbar-thumb { background: #2E2420; border-radius: 3px; }
      `}</style>
      <div style={{ background: "#0D0B08", minHeight: "100vh", color: "#F0EBE3" }}>
        <NavBar activeTab={activeTab} setActiveTab={setActiveTab} />

        <div style={{ maxWidth: "780px", margin: "0 auto", padding: "0 20px 60px" }}>
          {/* Hero tagline */}
          <div style={{ padding: "28px 0 4px" }}>
            <p style={{
              fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px",
              color: "#4D3E33", letterSpacing: "1.5px", textTransform: "uppercase",
            }}>The pulse of African tech — curated by the community</p>
          </div>

          <Stats />

          {/* Post list */}
          <div style={{ marginTop: "4px" }}>
            {posts.map((post, i) => (
              <PostRow key={post.id} post={post} rank={i + 1} />
            ))}
          </div>

          {/* Load more */}
          <div style={{ padding: "24px 0 0 34px" }}>
            <a href="#" style={{
              color: "#4D3E33", fontFamily: "'IBM Plex Mono', monospace",
              fontSize: "12px", textDecoration: "none",
            }}
              onMouseEnter={e => e.target.style.color = "#E8521A"}
              onMouseLeave={e => e.target.style.color = "#4D3E33"}
            >more →</a>
          </div>
        </div>

        {/* Footer */}
        <footer style={{
          borderTop: "1px solid #1E1A16", padding: "20px",
          textAlign: "center", fontFamily: "'IBM Plex Mono', monospace",
          fontSize: "11px", color: "#3D3028",
        }}>
          <div style={{ display: "flex", justifyContent: "center", gap: "20px", flexWrap: "wrap" }}>
            {["guidelines", "faq", "api", "security", "legal", "contact"].map(link => (
              <a key={link} href="#" style={{ color: "#3D3028", textDecoration: "none" }}
                onMouseEnter={e => e.target.style.color = "#E8521A"}
                onMouseLeave={e => e.target.style.color = "#3D3028"}
              >{link}</a>
            ))}
          </div>
          <p style={{ marginTop: "12px", color: "#2A2018" }}>
            Rift · Built for the African tech ecosystem
          </p>
        </footer>
      </div>
    </>
  );
}
```