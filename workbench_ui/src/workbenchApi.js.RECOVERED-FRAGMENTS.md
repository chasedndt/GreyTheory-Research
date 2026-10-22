# Recovered fragments: workbenchApi.js

Original path: `E:\Projects\GreyTheory\2026-09-01-workbench-read-model-binding\worktree\workbench_ui\src\workbenchApi.js`. The whole file was never captured in a transcript, so these are the
recorded edits in time order: each shows the text that was replaced and the text that replaced it.
Append-style logs can usually be reassembled from the 'new text' blocks.

## 1. 2026-09-14T22:39:48.718Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
export function curriculumFromSnapshot(snapshot) {
````

New text:

````
export function campaignFromSnapshot(snapshot) {
  const section = (snapshot?.sections || []).find((item) => item.id === "campaign");
  const records = Array.isArray(section?.records) ? section.records : [];

  const campaigns = records.map((record) => {
    const attributes = record.attributes || {};
    // "programme=ok,curriculum=ok,study=todo,..." - compact on the wire so one
    // record carries the whole journey rather than one record per stage.
    const stages = String(attributes.stages || "")
      .split(",")
      .filter(Boolean)
      .map((pair) => {
        const [name, marker] = pair.split("=");
        return { name, marker: marker || "todo" };
      });

    return {
      programmeId: record.title,
      currentStage: attributes.current_stage || "",
      because: record.detail || "",
      nextAction: attributes.next_action || "",
      // The server sends strings; only the exact string means blocked.
      blockedByGovernance: attributes.blocked_by_governance === "true",
      practisedTopics: Number.parseInt(attributes.practised_topics || "0", 10),
      posture: attributes.posture || "",
      stages,
    };
  });

  return { available: Boolean(section) && campaigns.length > 0, campaigns };
}

export function curriculumFromSnapshot(snapshot) {
````

## 2. 2026-09-15T00:14:14.756Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
export function campaignFromSnapshot(snapshot) {
````

New text:

````
const SCOPE_KINDS = [
  ["in-scope", "In scope"],
  ["out-of-scope", "Out of scope"],
  ["prohibited", "Prohibited techniques"],
];

export function reviewFromSnapshot(snapshot) {
  const section = (snapshot?.sections || []).find((item) => item.id === "review");
  const records = Array.isArray(section?.records) ? section.records : [];

  const byProgramme = new Map();
  const entryFor = (programmeId) => {
    if (!byProgramme.has(programmeId)) {
      byProgramme.set(programmeId, {
        programmeId,
        scope: SCOPE_KINDS.map(([kind, title]) => ({ kind, title, count: 0, values: [] })),
        documents: [],
        resolutions: [],
      });
    }
    return byProgramme.get(programmeId);
  };

  for (const record of records) {
    const attributes = record.attributes || {};
    const programmeId = attributes.programme_id;
    if (!programmeId) continue;
    const entry = entryFor(programmeId);
    const kind = attributes.kind;

    if (kind === "source_document") {
      entry.documents.push({
        id: record.id,
        title: record.title,
        captureMode: attributes.capture_mode || "unknown",
        // Only the exact string means the hashes agreed.
        hashAgrees: attributes.hash_agrees === "true",
        truncated: attributes.truncated === "true",
        bytes: Number.parseInt(attributes.bytes || "0", 10),
        content: record.detail || "",
      });
      continue;
    }
    if (kind === "human_resolution") {
      entry.resolutions.push({
        id: record.id,
        title: record.title,
        resolved: attributes.resolved === "true",
      });
      continue;
    }
    const group = entry.scope.find((item) => item.kind === kind);
    if (group) {
      const count = Number.parseInt(attributes.count || "0", 10);
      group.count = count;
      // The server writes "none recorded" when a list is empty; that is a
      // message, not an asset, and must never be rendered as one.
      group.values = count > 0 ? String(record.detail || "").split("\n").filter(Boolean) : [];
    }
  }

  const programmes = [...byProgramme.values()];
  return { available: Boolean(section) && programmes.length > 0, programmes };
}

export function campaignFromSnapshot(snapshot) {
````

## 3. 2026-09-15T10:14:07.874Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        scope: SCOPE_KINDS.map(([kind, title]) => ({ kind, title, count: 0, values: [] })),
        documents: [],
        resolutions: [],
      });
````

New text:

````
        scope: SCOPE_KINDS.map(([kind, title]) => ({ kind, title, count: 0, values: [] })),
        documents: [],
        resolutions: [],
        // Assume unreviewed until the server says otherwise: the safe default
        // is the one that offers the gate, not the one that skips it.
        humanReviewed: false,
        contractStatus: "unknown",
      });
````

## 4. 2026-09-15T10:14:10.674Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
    if (kind === "human_resolution") {
      entry.resolutions.push({
        id: record.id,
        title: record.title,
        resolved: attributes.resolved === "true",
      });
      continue;
    }
````

New text:

````
    if (kind === "human_resolution") {
      entry.resolutions.push({
        id: record.id,
        title: record.title,
        resolved: attributes.resolved === "true",
      });
      continue;
    }
    if (kind === "programme_state") {
      // Only the exact string means a person recorded reading it.
      entry.humanReviewed = attributes.human_reviewed === "true";
      entry.contractStatus = attributes.contract_status || "unknown";
      continue;
    }
````

## 5. 2026-09-15T10:17:31.809Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  if (!payload || payload.executed !== false || payload.disposition !== "accepted") {
    throw new Error("The local API returned an unsupported command result.");
  }
  return payload;
````

New text:

````
  // A result claiming execution is a protocol fault whatever its disposition:
  // this application routes bounded commands and never runs anything.
  if (!payload || payload.executed !== false || typeof payload.disposition !== "string") {
    throw new Error("The local API returned an unsupported command result.");
  }
  if (payload.disposition !== "accepted") {
    // A refusal is a legitimate outcome, not a fault. The server's own words say
    // which governance rule applied - "resolve its 2 ambiguity/ies and
    // recompile" tells the operator what to do next, where a generic error
    // would imply a bug rather than a decision.
    throw new Error(
      payload.message || `The local application refused this command (${payload.disposition}).`,
    );
  }
  return payload;
````

## 6. 2026-09-15T15:31:18.475Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
export function campaignFromSnapshot(snapshot) {
````

New text:

````
/**
 * Which programmes are being worked, and which are set aside.
 *
 * Unlike the review adapter, this reports available whenever the section
 * exists, even with no entries: an empty shortlist is a real state that must
 * render its own empty state rather than disappear, and a panel that vanishes
 * when you archive your last programme is a dead end.
 */
export function shortlistFromSnapshot(snapshot) {
  const section = (snapshot?.sections || []).find((item) => item.id === "shortlist");
  const records = Array.isArray(section?.records) ? section.records : [];

  const entries = records
    .filter((record) => (record.attributes || {}).kind === "shortlist_entry")
    .map((record) => {
      const attributes = record.attributes || {};
      return {
        programmeId: attributes.programme_id || record.title,
        // Only the exact string means archived; anything else stays active,
        // because showing something as set aside when it is not would hide
        // work the operator still has open.
        isArchived: attributes.status === "archived",
        outcome: attributes.outcome || "unset",
        // The server writes a self-describing fallback when no reason was
        // given, so this line reads correctly either way.
        detail: record.detail || "",
        shortlistedAt: attributes.shortlisted_at || "",
        updatedAt: attributes.updated_at || "",
        // Carried so a command can pin its write to the state that was shown,
        // and refuse if it changed underneath.
        revision: Number.parseInt(attributes.revision || "0", 10),
      };
    });

  const active = entries.filter((entry) => !entry.isArchived);
  const archived = entries.filter((entry) => entry.isArchived);
  return {
    available: Boolean(section),
    active,
    archived,
    counts: { active: active.length, archived: archived.length },
    note: section?.note || "",
  };
}

export function campaignFromSnapshot(snapshot) {
````

## 7. 2026-09-15T16:27:59.072Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
export function campaignFromSnapshot(snapshot) {
````

New text:

````
/**
 * Research workspaces from the snapshot.
 *
 * The server has always published this section; nothing rendered it. Note the
 * two distinct absences it can report, which must not be collapsed: `configured
 * === false` means no private store is set up at all, while an empty list means
 * the store is healthy and simply holds no workspaces yet. One is a setup
 * problem and the other is a normal starting point.
 */
export function researchFromSnapshot(snapshot) {
  const section = (snapshot?.sections || []).find((item) => item.id === "research");
  const records = Array.isArray(section?.records) ? section.records : [];
  const metrics = Array.isArray(section?.metrics) ? section.metrics : [];
  const activeMetric = metrics.find((item) => item.label === "Active");

  const workspaces = records.map((record) => {
    const attributes = record.attributes || {};
    // A workspace that failed to load carries no attributes at all, so it must
    // not be rendered as though its counts were genuinely zero.
    const unreadable = record.status === "blocked";
    return {
      id: record.id,
      title: record.title,
      goal: record.detail || "",
      // The server writes the lifecycle here rather than in the status field.
      status: record.subtitle || (unreadable ? "unreadable" : "unknown"),
      unreadable,
      error: unreadable ? record.detail || "" : "",
      programmeId: attributes.programme_id || "",
      posture: attributes.posture || "",
      authorityRef: (record.references || [])
        .find((ref) => String(ref).startsWith("authority:")) || "",
      counts: {
        sessions: Number.parseInt(attributes.sessions || "0", 10),
        activeSessions: Number.parseInt(attributes.active_sessions || "0", 10),
        hypotheses: Number.parseInt(attributes.hypotheses || "0", 10),
        actionRequests: Number.parseInt(attributes.action_requests || "0", 10),
        actionReceipts: Number.parseInt(attributes.action_receipts || "0", 10),
        lessons: Number.parseInt(attributes.lessons || "0", 10),
      },
    };
  });

  return {
    available: Boolean(section),
    configured: Boolean(section) && section.status !== "unknown",
    blocked: section?.status === "blocked",
    workspaces,
    activeId: activeMetric && activeMetric.value !== "unknown" ? activeMetric.value : null,
    note: section?.note || "",
  };
}

export function campaignFromSnapshot(snapshot) {
````

## 8. 2026-09-15T16:28:43.412Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
      counts: {
        sessions: Number.parseInt(attributes.sessions || "0", 10),
        activeSessions: Number.parseInt(attributes.active_sessions || "0", 10),
        hypotheses: Number.parseInt(attributes.hypotheses || "0", 10),
        actionRequests: Number.parseInt(attributes.action_requests || "0", 10),
        actionReceipts: Number.parseInt(attributes.action_receipts || "0", 10),
        lessons: Number.parseInt(attributes.lessons || "0", 10),
      },
````

New text:

````
      // Null, not zeroes. A workspace that failed to load has no attributes,
      // and "0 hypotheses" would be a confident claim about something the
      // server could not read at all.
      counts: unreadable ? null : {
        sessions: Number.parseInt(attributes.sessions || "0", 10),
        activeSessions: Number.parseInt(attributes.active_sessions || "0", 10),
        hypotheses: Number.parseInt(attributes.hypotheses || "0", 10),
        actionRequests: Number.parseInt(attributes.action_requests || "0", 10),
        actionReceipts: Number.parseInt(attributes.action_receipts || "0", 10),
        lessons: Number.parseInt(attributes.lessons || "0", 10),
      },
````

## 9. 2026-09-15T18:05:44.890Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
export function campaignFromSnapshot(snapshot) {
````

New text:

````
/**
 * The programmes actually in your local registry.
 *
 * The server has published this section all along and the UI rendered
 * hardcoded prototype content beside it instead. Everything here comes from
 * compiled contracts on disk: no programme appears that was not registered
 * from saved sources, and none is invented to fill the panel.
 */
export function programmesFromSnapshot(snapshot) {
  const section = (snapshot?.sections || []).find((item) => item.id === "programmes");
  const records = Array.isArray(section?.records) ? section.records : [];

  const programmes = records.map((record) => {
    const attributes = record.attributes || {};
    return {
      id: record.id,
      // The contract's own state, which is not the same question as whether
      // the record needs attention.
      contractStatus: record.subtitle || "unknown",
      // Only the exact string means a person reviewed it.
      humanReviewed: attributes.human_reviewed === "true",
      maxAuthority: attributes.max_authority || "",
      version: Number.parseInt(attributes.version || "0", 10),
      needsAttention: record.status === "attention" || record.status === "blocked",
    };
  });

  const metric = (label) => {
    const found = (section?.metrics || []).find((item) => item.label === label);
    return found ? Number.parseInt(found.value || "0", 10) : programmes.length;
  };

  return {
    available: Boolean(section),
    programmes,
    counts: {
      registered: metric("Registered"),
      needingAttention: metric("Need attention"),
    },
  };
}

export function campaignFromSnapshot(snapshot) {
````

## 10. 2026-09-15T22:00:06.694Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
export function campaignFromSnapshot(snapshot) {
````

New text:

````
/**
 * Public programme pages that have been read and kept.
 *
 * Every field here describes material retrieved from the open internet. The
 * adapter carries `dataClass` and `trust` through rather than dropping them,
 * because a panel that forgets what this content is would present a saved copy
 * of a marketing page with the same authority as a reviewed contract.
 */
export function directoryFromSnapshot(snapshot) {
  const section = (snapshot?.sections || []).find((item) => item.id === "directory");
  const records = Array.isArray(section?.records) ? section.records : [];

  const lookups = records
    .filter((record) => (record.attributes || {}).kind === "directory_lookup")
    .map((record) => {
      const attributes = record.attributes || {};
      return {
        identifier: attributes.identifier || record.title,
        platform: attributes.platform || "",
        handle: attributes.handle || "",
        url: attributes.url || record.detail || "",
        status: Number.parseInt(attributes.status || "0", 10),
        contentType: attributes.content_type || "",
        bodySha256: attributes.body_sha256 || "",
        bodyBytes: Number.parseInt(attributes.body_bytes || "0", 10),
        retrievedAt: attributes.retrieved_at || "",
        dataClass: attributes.data_class || "PUBLIC",
        trust: attributes.trust || "UNTRUSTED",
      };
    });

  const metric = (label) => {
    const found = (section?.metrics || []).find((item) => item.label === label);
    return found ? Number.parseInt(found.value || "0", 10) : 0;
  };

  return {
    available: Boolean(section),
    // A store that could not be opened is not a store holding nothing.
    configured: Boolean(section) && section.status !== "unknown",
    blocked: section?.status === "blocked",
    lookups,
    counts: { read: metric("Programmes read"), bytes: metric("Bytes retrieved") },
    note: section?.note || "",
  };
}

export function campaignFromSnapshot(snapshot) {
````
