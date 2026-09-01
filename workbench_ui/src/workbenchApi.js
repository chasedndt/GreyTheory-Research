const statusLabels = {
  ready: "Ready",
  attention: "Needs review",
  blocked: "Blocked",
  empty: "Empty",
  unknown: "Unknown",
};

const panelSections = {
  Overview: "overview",
  Hypotheses: "hypotheses",
  Knowledge: "learning",
  Artifacts: "evidence",
  Claims: "reports",
  Governance: "capabilities",
  Workspaces: "research",
};

function toneFor(status) {
  if (status === "blocked") return "blocked";
  if (status === "ready") return "verified";
  return "observed";
}

export function validateLocalConnection(baseUrl, token) {
  let url;
  try {
    url = new URL(baseUrl);
  } catch {
    throw new Error("Enter a valid local API URL.");
  }
  if (
    url.protocol !== "http:" ||
    url.hostname !== "127.0.0.1" ||
    !url.port ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error("The API must be an exact numeric-loopback URL such as http://127.0.0.1:8765.");
  }
  if (typeof token !== "string" || token.length < 32 || /\s/.test(token)) {
    throw new Error("Enter the one-process session token printed by GreyTheory.");
  }
  return url.origin;
}

export async function fetchWorkbenchSnapshot({ baseUrl, token, workspaceId, fetchImpl = fetch, signal }) {
  const origin = validateLocalConnection(baseUrl, token);
  const url = new URL("/api/v1/snapshot", `${origin}/`);
  if (workspaceId) url.searchParams.set("workspace_id", workspaceId);
  const response = await fetchImpl(url, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
    credentials: "omit",
    signal,
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.error?.message || `Local API returned ${response.status}.`;
    throw new Error(message);
  }
  if (payload?.schema_version !== "greytheory.workbench.v1" || payload?.live_target_available !== false) {
    throw new Error("The local API returned an unsupported or unsafe snapshot contract.");
  }
  return payload;
}

function sectionToPanel(section, fallback) {
  const metrics = Array.isArray(section?.metrics) ? section.metrics : [];
  const records = Array.isArray(section?.records) ? section.records : [];
  return {
    ...fallback,
    subtitle: section?.note || fallback.subtitle,
    stats: metrics.length
      ? metrics.slice(0, 4).map((metric) => [metric.label, metric.value])
      : [["State", statusLabels[section?.status] || "Unknown"]],
    rows: records.map((record) => ({
      id: record.id,
      title: record.title,
      detail: record.detail || record.subtitle || "No further local detail is available.",
      status: statusLabels[record.status] || record.status || "Unknown",
      tone: toneFor(record.status),
      kind: record.subtitle || "Local record",
    })),
    boundary: section?.note || fallback.boundary,
    dataSource: "Authenticated local API",
  };
}

export function panelsFromSnapshot(snapshot, fallbackPanels) {
  const byId = new Map((snapshot.sections || []).map((section) => [section.id, section]));
  return Object.fromEntries(
    Object.entries(fallbackPanels).map(([name, fallback]) => {
      const section = byId.get(panelSections[name]);
      return [name, section ? sectionToPanel(section, fallback) : { ...fallback, dataSource: "Prototype exemplar" }];
    }),
  );
}
