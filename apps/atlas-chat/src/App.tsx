import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  BenchReport,
  ChatMessage,
  bench as fetchBench,
  chat,
  entities as fetchEntities,
  EntityDetail,
  EntityGraph,
  entityDetail as fetchEntityDetail,
  entityGraph as fetchEntityGraph,
  EntitySummary,
  health,
  loadSettings,
  mindmap,
  MindmapGraph,
  pull,
  saveSettings,
  sessionEnd,
  Settings,
  wake,
} from "./api";

type SyncState = "ok" | "busy" | "err";
type Tab = "chat" | "mindmap" | "entities" | "savings";

export default function App() {
  const [settings, setSettings] = useState<Settings>(() => loadSettings());
  const [showSettings, setShowSettings] = useState(false);
  const [tab, setTab] = useState<Tab>("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [greeting, setGreeting] = useState<string | null>(null);
  const [sync, setSync] = useState<{ state: SyncState; label: string }>({
    state: "busy",
    label: "starting…",
  });
  const [busy, setBusy] = useState(false);
  const [graph, setGraph] = useState<MindmapGraph | null>(null);
  const [mapPeriod, setMapPeriod] = useState("day");
  const [benchReport, setBenchReport] = useState<BenchReport | null>(null);
  const [daemonLabel, setDaemonLabel] = useState("daemon…");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setSync({ state: "busy", label: "pulling…" });
      try {
        try {
          const h = await health();
          if (!cancelled) {
            setDaemonLabel(
              h.ok
                ? `daemon ${h.version || h.service || "up"}`
                : "daemon offline",
            );
          }
        } catch {
          if (!cancelled) setDaemonLabel("daemon offline — run atlas daemon");
        }
        await pull(settings.lifeRoot || undefined);
        if (cancelled) return;
        const w = await wake(settings.lifeRoot || undefined);
        if (cancelled) return;
        if (w.session_init?.summary) {
          setGreeting(
            w.session_init.greeting ||
              `Resuming: ${w.session_init.summary}`,
          );
        }
        setSync({
          state: "ok",
          label: w.keys?.day ? `synced · ${w.keys.day}` : "synced",
        });
      } catch (e) {
        if (cancelled) return;
        setSync({
          state: "err",
          label: e instanceof Error ? e.message : "offline / local only",
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [settings.lifeRoot]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  useEffect(() => {
    if (tab !== "mindmap") return;
    let cancelled = false;
    (async () => {
      try {
        const g = await mindmap(mapPeriod, settings.lifeRoot || undefined);
        if (!cancelled) setGraph(g);
      } catch {
        if (!cancelled) setGraph(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tab, mapPeriod, settings.lifeRoot]);

  useEffect(() => {
    const onLeave = () => {
      if (messages.length === 0) return;
      const payload = JSON.stringify({
        messages,
        push: settings.autoPush,
        life_root: settings.lifeRoot || undefined,
      });
      navigator.sendBeacon?.(
        "/api/session-end",
        new Blob([payload], { type: "application/json" }),
      );
    };
    window.addEventListener("pagehide", onLeave);
    return () => window.removeEventListener("pagehide", onLeave);
  }, [messages, settings]);

  async function onSend(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    const next = [...messages, { role: "user" as const, content: text }];
    setMessages(next);
    setInput("");
    setBusy(true);
    setSync({ state: "busy", label: "thinking…" });
    try {
      const res = await chat(next, settings);
      setMessages([...next, { role: "assistant", content: res.reply }]);
      const n = Array.isArray(res.memories) ? res.memories.length : 0;
      setSync({
        state: "ok",
        label: n
          ? settings.autoPush
            ? `saved ${n} · pushed`
            : `saved ${n}`
          : "synced",
      });
    } catch (err) {
      setSync({
        state: "err",
        label: err instanceof Error ? err.message : "chat failed",
      });
    } finally {
      setBusy(false);
    }
  }

  async function endSession() {
    setSync({ state: "busy", label: "saving init…" });
    try {
      await sessionEnd(messages, settings);
      setSync({ state: "ok", label: "init ready for next wake" });
      setMessages([]);
      setGreeting("Session init saved. Next open will resume from here.");
    } catch (e) {
      setSync({
        state: "err",
        label: e instanceof Error ? e.message : "session-end failed",
      });
    }
  }

  function persistSettings(next: Settings) {
    setSettings(next);
    saveSettings(next);
    setShowSettings(false);
  }

  return (
    <div className="app">
      <header className="top">
        <div>
          <h1 className="brand">Atlas</h1>
          <p className="sub">Remembers your conversations — day, week, month, year — on your private GitHub.</p>
          <nav className="tabs" aria-label="Views">
            <button type="button" className={tab === "chat" ? "tab active" : "tab"} onClick={() => setTab("chat")}>
              Chat
            </button>
            <button
              type="button"
              className={tab === "mindmap" ? "tab active" : "tab"}
              onClick={() => setTab("mindmap")}
            >
              Mind Map
            </button>
            <button
              type="button"
              className={tab === "entities" ? "tab active" : "tab"}
              onClick={() => setTab("entities")}
            >
              Entities
            </button>
            <button
              type="button"
              className={tab === "savings" ? "tab active" : "tab"}
              onClick={() => setTab("savings")}
            >
              Savings
            </button>
          </nav>
          <p className="sub" style={{ marginTop: "0.35rem" }}>{daemonLabel}</p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", justifyContent: "flex-end" }}>
          <div className="sync" data-state={sync.state}>
            {sync.label}
          </div>
          {tab === "chat" && messages.length > 0 && (
            <button type="button" className="gear" onClick={() => void endSession()}>
              End &amp; init
            </button>
          )}
          <button type="button" className="gear" onClick={() => setShowSettings(true)} aria-label="Settings">
            Settings
          </button>
        </div>
      </header>

      {tab === "chat" ? (
        <>
          <div className="messages" aria-live="polite">
            {greeting && <div className="bubble assistant">{greeting}</div>}
            {messages.length === 0 && !greeting && (
              <div className="bubble assistant">
                Say anything. Durable facts become life drawers. End &amp; init prepares the next wake.
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`bubble ${m.role}`}>
                {m.content}
              </div>
            ))}
            {busy && <div className="bubble assistant">…</div>}
            <div ref={bottomRef} />
          </div>

          <form className="composer" onSubmit={onSend}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Talk to Atlas…"
              rows={2}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void onSend(e);
                }
              }}
            />
            <button type="submit" disabled={busy || !input.trim()}>
              Send
            </button>
          </form>
        </>
      ) : tab === "mindmap" ? (
        <MindMapView
          graph={graph}
          period={mapPeriod}
          onPeriod={setMapPeriod}
        />
      ) : tab === "entities" ? (
        <EntitiesView lifeRoot={settings.lifeRoot} />
      ) : (
        <SavingsView
          report={benchReport}
          onRun={async () => {
            setSync({ state: "busy", label: "bench…" });
            try {
              const r = await fetchBench();
              setBenchReport(r);
              setSync({
                state: r.ok ? "ok" : "err",
                label: r.ok
                  ? `saved ~${r.avg_savings_pct}% tokens`
                  : "bench failed",
              });
            } catch (e) {
              setSync({
                state: "err",
                label: e instanceof Error ? e.message : "bench failed",
              });
            }
          }}
        />
      )}

      {showSettings && (
        <SettingsModal
          initial={settings}
          onClose={() => setShowSettings(false)}
          onSave={persistSettings}
        />
      )}
    </div>
  );
}

function MindMapView({
  graph,
  period,
  onPeriod,
}: {
  graph: MindmapGraph | null;
  period: string;
  onPeriod: (p: string) => void;
}) {
  const layout = useMemo(() => layoutNodes(graph), [graph]);

  return (
    <div className="mindmap">
      <div className="mindmap-toolbar">
        {(["day", "week", "month", "year", "people"] as const).map((p) => (
          <button
            key={p}
            type="button"
            className={period === p ? "tab active" : "tab"}
            onClick={() => onPeriod(p)}
          >
            {p}
          </button>
        ))}
      </div>
      {!graph && <p className="sub">Loading mind map…</p>}
      {graph && graph.nodes.length === 0 && <p className="sub">No nodes yet — chat first, then refresh this tab.</p>}
      {graph && layout && (
        <svg className="mindmap-svg" viewBox={`0 0 ${layout.w} ${layout.h}`} role="img" aria-label="Atlas mind map">
          {graph.edges.map((e, i) => {
            const a = layout.pos[e.from];
            const b = layout.pos[e.to];
            if (!a || !b) return null;
            return (
              <line
                key={i}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                className="mm-edge"
              />
            );
          })}
          {graph.nodes.map((n) => {
            const p = layout.pos[n.id];
            if (!p) return null;
            return (
              <g key={n.id} transform={`translate(${p.x},${p.y})`}>
                <circle r={n.kind === "period" ? 18 : n.kind === "topic" ? 12 : 14} className={`mm-node mm-${n.kind}`} />
                <text y={28} textAnchor="middle" className="mm-label">
                  {n.label.length > 28 ? n.label.slice(0, 26) + "…" : n.label}
                </text>
              </g>
            );
          })}
        </svg>
      )}
      {graph?.scopes && graph.scopes.length > 0 && (
        <p className="sub">
          Scopes:{" "}
          {graph.scopes.map((s) => `${s.name}${s.status ? ` (${s.status})` : ""}`).join(" · ")}
        </p>
      )}
    </div>
  );
}

function layoutNodes(graph: MindmapGraph | null) {
  if (!graph) return null;
  const w = 720;
  const h = 520;
  const pos: Record<string, { x: number; y: number }> = {};
  const periods = graph.nodes.filter((n) => n.kind === "period");
  const topics = graph.nodes.filter((n) => n.kind === "topic");
  const entityNodes = graph.nodes.filter((n) => n.kind === "entity");
  const drawers = graph.nodes.filter((n) => !["period", "topic", "entity"].includes(n.kind));
  periods.forEach((n, i) => {
    pos[n.id] = { x: 80 + i * 160, y: 60 };
  });
  topics.forEach((n, i) => {
    const angle = (i / Math.max(topics.length, 1)) * Math.PI * 2;
    pos[n.id] = { x: w / 2 + Math.cos(angle) * 90, y: h / 2 + Math.sin(angle) * 70 };
  });
  entityNodes.forEach((n, i) => {
    const angle = ((i + topics.length) / Math.max(entityNodes.length + topics.length, 1)) * Math.PI * 2;
    pos[n.id] = { x: w / 2 + Math.cos(angle) * 130, y: h / 2 + Math.sin(angle) * 100 };
  });
  drawers.forEach((n, i) => {
    const cols = 4;
    const col = i % cols;
    const row = Math.floor(i / cols);
    pos[n.id] = { x: 100 + col * 160, y: 200 + row * 90 };
  });
  return { w, h, pos };
}

function SavingsView({
  report,
  onRun,
}: {
  report: BenchReport | null;
  onRun: () => void | Promise<void>;
}) {
  return (
    <div className="mindmap" style={{ padding: "1rem" }}>
      <h2 style={{ marginTop: 0 }}>Token savings</h2>
      <p className="sub">
        A/B proxy: blind grep vs Atlas route (<code>chars/4</code>). Proves orientation cuts exploration cost.
      </p>
      <button type="button" className="gear" onClick={() => void onRun()}>
        Run atlas bench
      </button>
      {!report && <p className="sub">No report yet.</p>}
      {report && (
        <div style={{ marginTop: "1rem" }}>
          <p>
            Average savings: <strong>{report.avg_savings_pct ?? "—"}%</strong>
            {" · "}
            {report.token_proxy_baseline_total} → {report.token_proxy_atlas_total} tokens
            {" · "}
            {report.passed}/{report.cases} cases
          </p>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {(report.results || []).map((r) => (
              <li key={r.id} style={{ padding: "0.35rem 0", borderBottom: "1px solid #2a2a2a" }}>
                {r.pass ? "PASS" : "FAIL"} {r.id}: {r.savings_pct}%
              </li>
            ))}
          </ul>
          {report.note && <p className="sub">{report.note}</p>}
        </div>
      )}
    </div>
  );
}

function EntitiesView({ lifeRoot }: { lifeRoot: string }) {
  const [list, setList] = useState<EntitySummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<EntityGraph | null>(null);
  const [drawers, setDrawers] = useState<EntityDetail | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchEntities(lifeRoot || undefined).then((r) => {
      if (!cancelled) setList(r.entities || []);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [lifeRoot]);

  useEffect(() => {
    if (!selected) {
      setDetail(null);
      setDrawers(null);
      return;
    }
    let cancelled = false;
    Promise.all([
      fetchEntityGraph(selected, lifeRoot || undefined),
      fetchEntityDetail(selected, lifeRoot || undefined),
    ]).then(([g, d]) => {
      if (!cancelled) {
        setDetail(g);
        setDrawers(d);
      }
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [selected, lifeRoot]);

  const layout = useMemo(() => layoutNodes(detail as MindmapGraph | null), [detail]);

  return (
    <div className="mindmap">
      <div className="mindmap-toolbar" style={{ flexWrap: "wrap" }}>
        <button type="button" className={!selected ? "tab active" : "tab"} onClick={() => setSelected(null)}>
          All
        </button>
        {list.map((e) => (
          <button key={e.slug} type="button" className={selected === e.name ? "tab active" : "tab"} onClick={() => setSelected(e.name)}>
            {e.name} ({e.refs})
          </button>
        ))}
      </div>
      {!selected && (
        <div style={{ padding: "1rem" }}>
          {list.length === 0 && <p className="sub">No entities yet. Chat and mention people/objects to create entities.</p>}
          {list.map((e) => (
            <div key={e.slug} style={{ padding: "0.5rem 0", borderBottom: "1px solid #333", cursor: "pointer" }} onClick={() => setSelected(e.name)}>
              <strong>{e.name}</strong> — {e.refs} ref{e.refs !== 1 ? "s" : ""}
              {e.last_seen && <span style={{ color: "#888", marginLeft: "0.5rem" }}>last: {e.last_seen}</span>}
            </div>
          ))}
        </div>
      )}
      {selected && drawers && (
        <div style={{ padding: "0.75rem 1rem" }}>
          <p className="sub">
            {drawers.name}
            {drawers.aliases && drawers.aliases.length > 0
              ? ` · aliases: ${drawers.aliases.join(", ")}`
              : ""}
            {" · "}
            {drawers.drawers?.length || 0} drawers
          </p>
          <ul style={{ listStyle: "none", padding: 0, margin: "0.5rem 0 1rem" }}>
            {(drawers.drawers || []).map((d, i) => (
              <li key={i} style={{ padding: "0.35rem 0", borderBottom: "1px solid #2a2a2a" }}>
                <strong>[{d.type || "?"}]</strong> {d.summary || d.error || d.path}
                {d.when && <span style={{ color: "#888", marginLeft: "0.5rem" }}>{d.when}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {selected && detail && layout && (
        <svg className="mindmap-svg" viewBox={`0 0 ${layout.w} ${layout.h}`} role="img" aria-label={`Entity graph: ${selected}`}>
          {detail.edges.map((e, i) => {
            const a = layout.pos[e.from];
            const b = layout.pos[e.to];
            if (!a || !b) return null;
            return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} className="mm-edge" />;
          })}
          {detail.nodes.map((n) => {
            const p = layout.pos[n.id];
            if (!p) return null;
            return (
              <g key={n.id} transform={`translate(${p.x},${p.y})`}>
                <circle r={n.kind === "entity" ? 20 : n.kind === "topic" ? 12 : 14} className={`mm-node mm-${n.kind}`} />
                <text y={28} textAnchor="middle" className="mm-label">
                  {n.label.length > 28 ? n.label.slice(0, 26) + "…" : n.label}
                </text>
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}

function SettingsModal({
  initial,
  onClose,
  onSave,
}: {
  initial: Settings;
  onClose: () => void;
  onSave: (s: Settings) => void;
}) {
  const [lifeRoot, setLifeRoot] = useState(initial.lifeRoot);
  const [model, setModel] = useState(initial.model);
  const [autoPush, setAutoPush] = useState(initial.autoPush);

  return (
    <div className="settings" role="dialog" aria-modal="true">
      <div className="panel">
        <h2>Settings</h2>
        <label htmlFor="lifeRoot">Life root (optional)</label>
        <input
          id="lifeRoot"
          type="text"
          value={lifeRoot}
          onChange={(e) => setLifeRoot(e.target.value)}
          placeholder="~/atlas-life or leave empty for ATLAS_LIFE_ROOT"
        />
        <label htmlFor="model">DeepSeek model</label>
        <input id="model" type="text" value={model} onChange={(e) => setModel(e.target.value)} />
        <label>
          <input type="checkbox" checked={autoPush} onChange={(e) => setAutoPush(e.target.checked)} /> Auto commit + push
        </label>
        <p className="hint">
          Set <code>DEEPSEEK_API_KEY</code> in the environment for the sidecar. Never store keys in the life git repo.
          Windows: <code>atlas life autostart install</code> opens the app at login.
        </p>
        <div className="row">
          <button type="button" onClick={() => onSave({ lifeRoot, model, autoPush })}>
            Save
          </button>
          <button type="button" style={{ background: "transparent", color: "inherit", border: "1px solid #ccc" }} onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
