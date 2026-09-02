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

export function commandMode(baseUrl, pageOrigin = globalThis.location?.origin) {
  const url = new URL(baseUrl);
  return url.origin === pageOrigin ? "interactive" : "read_only";
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

function safeCommandId(kind, now, randomId) {
  const suffix = String(randomId || globalThis.crypto?.randomUUID?.() || now.getTime())
    .replace(/[^a-zA-Z0-9_.:-]/g, "-")
    .slice(0, 80);
  return `ui-${kind}-${suffix}`;
}

export function createWorkbenchCommand({
  kind,
  fields = {},
  expectedRevision = null,
  requestedAuthority = "NONE",
  humanAcknowledged = false,
  workspaceId = null,
  operatorRef = "operator-local",
  now = new Date(),
  randomId,
}) {
  if (!(now instanceof Date) || Number.isNaN(now.getTime())) throw new Error("Command time must be valid.");
  const id = safeCommandId(kind, now, randomId);
  return {
    schema_version: "greytheory.workbench.v1",
    id,
    kind,
    operator_ref: operatorRef,
    issued_at: now.toISOString(),
    idempotency_key: id,
    workspace_id: workspaceId,
    expected_revision: expectedRevision,
    requested_authority: requestedAuthority,
    human_acknowledged: humanAcknowledged,
    fields,
    executable: false,
  };
}

export async function sendWorkbenchCommand({
  baseUrl,
  token,
  command,
  pageOrigin = globalThis.location?.origin,
  fetchImpl = fetch,
  signal,
}) {
  const origin = validateLocalConnection(baseUrl, token);
  if (commandMode(origin, pageOrigin) !== "interactive") {
    throw new Error("State-changing commands require the same numeric-loopback origin as the GreyTheory application.");
  }
  const response = await fetchImpl(new URL("/api/v1/commands", `${origin}/`), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(command),
    cache: "no-store",
    credentials: "omit",
    signal,
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.error?.message || payload?.message || `Local API returned ${response.status}.`;
    throw new Error(message);
  }
  if (!payload || payload.executed !== false || payload.disposition !== "accepted") {
    throw new Error("The local API returned an unsupported command result.");
  }
  return payload;
}

export function learningStateFromSnapshot(snapshot) {
  const section = (snapshot?.sections || []).find((item) => item.id === "learning");
  const records = section?.records || [];
  const recommendation = records.find((item) => item.id?.startsWith("recommendation:"));
  const activeId = snapshot?.context?.learning_journey_id || null;
  const journey = activeId ? records.find((item) => item.id === activeId) : null;
  const packs = records.filter((item) => item.id?.startsWith("case-pack:"));
  const receipts = records.filter((item) => item.id?.startsWith("fixture-receipt:"));
  return {
    recommendation,
    journey: journey ? {
      ...journey,
      stage: journey.attributes?.stage || "unknown",
      revision: Number.parseInt(journey.attributes?.revision || "0", 10),
      track: journey.attributes?.track || "standard",
      cardId: journey.attributes?.card_id || null,
      dimension: journey.attributes?.dimension || null,
    } : null,
    packs,
    receipts,
    latestReceiptRef: receipts[0]?.id || null,
    fixtureReceiptCount: Number.parseInt(
      (section?.metrics || []).find((item) => item.label === "Fixture receipts")?.value || "0",
      10,
    ),
  };
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
