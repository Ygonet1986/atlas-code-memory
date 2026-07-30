export type ChatMessage = { role: "user" | "assistant"; content: string };

export type Settings = {
  lifeRoot: string;
  model: string;
  autoPush: boolean;
};

export type MindmapNode = {
  id: string;
  label: string;
  kind: string;
  period?: string;
  topics?: string[];
};

export type MindmapEdge = { from: string; to: string; rel: string };

export type MindmapGraph = {
  ok: boolean;
  period: string;
  keys: Record<string, string>;
  nodes: MindmapNode[];
  edges: MindmapEdge[];
  scopes?: { name: string; status?: string }[];
};

const SETTINGS_KEY = "atlas-chat-settings";

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...defaultSettings(), ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return defaultSettings();
}

export function saveSettings(s: Settings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
}

function defaultSettings(): Settings {
  return {
    lifeRoot: "",
    model: "deepseek-chat",
    autoPush: true,
  };
}

const TOKEN_KEY = "atlas-daemon-token";

/**
 * The daemon requires a token so that no other page in the browser can reach it.
 * Accept it once from `?token=...` (printed by `atlas daemon`) and keep it.
 */
export function daemonToken(): string {
  const fromUrl = new URLSearchParams(location.search).get("token");
  if (fromUrl) localStorage.setItem(TOKEN_KEY, fromUrl);
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setDaemonToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token.trim());
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = daemonToken();
  const res = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-Atlas-Token": token } : {}),
      ...(init?.headers || {}),
    },
    ...init,
  });
  const data = await res.json();
  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      throw new Error(`${data.error || "unauthorized"} — run 'atlas token' and paste it in Settings`);
    }
    throw new Error(data.error || data.detail || res.statusText);
  }
  return data as T;
}

export function pull(lifeRoot?: string) {
  return api("/api/pull", {
    method: "POST",
    body: JSON.stringify({ life_root: lifeRoot || undefined }),
  });
}

export function wake(lifeRoot?: string) {
  const q = lifeRoot ? `?life_root=${encodeURIComponent(lifeRoot)}` : "";
  return api<{
    prompt: string;
    keys: Record<string, string>;
    ok: boolean;
    session_init?: { summary?: string; greeting?: string } | null;
  }>(`/api/wake${q}`);
}

export function mindmap(period: string, lifeRoot?: string) {
  const q = new URLSearchParams({ period });
  if (lifeRoot) q.set("life_root", lifeRoot);
  return api<MindmapGraph>(`/api/mindmap?${q.toString()}`);
}

export function sessionEnd(
  messages: ChatMessage[],
  settings: Settings,
  extras?: { summary?: string; topics?: string[] },
) {
  return api("/api/session-end", {
    method: "POST",
    body: JSON.stringify({
      messages,
      summary: extras?.summary,
      topics: extras?.topics,
      push: settings.autoPush,
      life_root: settings.lifeRoot || undefined,
    }),
  });
}

export type EntitySummary = { slug: string; name: string; refs: number; last_seen?: string };
export type EntityDetail = {
  ok: boolean;
  slug: string;
  name: string;
  aliases?: string[];
  last_seen?: string;
  drawers: { path: string; summary?: string; type?: string; when?: string; topics?: string[]; entities?: string[]; error?: string }[];
  ref_count: number;
};
export type EntityGraph = {
  ok: boolean;
  slug: string;
  name: string;
  nodes: MindmapNode[];
  edges: MindmapEdge[];
};

export function entities(lifeRoot?: string) {
  const q = lifeRoot ? `?life_root=${encodeURIComponent(lifeRoot)}` : "";
  return api<{ ok: boolean; count: number; entities: EntitySummary[] }>(`/api/entities${q}`);
}

export function entityDetail(name: string, lifeRoot?: string) {
  const q = new URLSearchParams({ name });
  if (lifeRoot) q.set("life_root", lifeRoot);
  return api<EntityDetail>(`/api/entity?${q.toString()}`);
}

export function recall(question: string, lifeRoot?: string, limit = 10) {
  const q = new URLSearchParams({ q: question, limit: String(limit) });
  if (lifeRoot) q.set("life_root", lifeRoot);
  return api<{ ok: boolean; hits: { summary?: string; score?: number; type?: string; path?: string }[] }>(
    `/api/recall?${q.toString()}`,
  );
}

export function entityGraph(name: string, lifeRoot?: string) {
  const q = new URLSearchParams({ name });
  if (lifeRoot) q.set("life_root", lifeRoot);
  return api<EntityGraph>(`/api/entity-graph?${q.toString()}`);
}

export type DaemonHealth = {
  ok: boolean;
  service?: string;
  version?: string;
  life_root?: string;
};

export type BenchReport = {
  ok: boolean;
  avg_savings_pct?: number;
  token_proxy_baseline_total?: number;
  token_proxy_atlas_total?: number;
  passed?: number;
  cases?: number;
  results?: { id: string; savings_pct: number; pass: boolean }[];
  note?: string;
};

export function health() {
  return api<DaemonHealth>("/api/health");
}

export function bench(project?: string) {
  const q = project ? `?project=${encodeURIComponent(project)}` : "";
  return api<BenchReport>(`/api/bench${q}`);
}

export function chat(messages: ChatMessage[], settings: Settings) {
  return api<{
    ok: boolean;
    reply: string;
    memories: unknown[];
    git?: unknown;
    error?: string;
  }>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      messages,
      model: settings.model,
      push: settings.autoPush,
      life_root: settings.lifeRoot || undefined,
    }),
  });
}
