import assert from "node:assert/strict";
import test from "node:test";

import {
  coachHistoryFromSnapshot,
  commandMode,
  createWorkbenchCommand,
  curriculumFromSnapshot,
  fetchWorkbenchSnapshot,
  learningStateFromSnapshot,
  panelsFromSnapshot,
  sendWorkbenchCommand,
  validateLocalConnection,
} from "../src/workbenchApi.js";

const token = "t".repeat(32);

test("connection accepts only exact numeric IPv4 loopback", () => {
  assert.equal(validateLocalConnection("http://127.0.0.1:8765", token), "http://127.0.0.1:8765");
  for (const value of ["http://localhost:8765", "https://127.0.0.1:8765", "http://127.0.0.1", "http://127.0.0.1:8765/path"])
    assert.throws(() => validateLocalConnection(value, token), /numeric-loopback/);
});

test("snapshot client authenticates and refuses unsafe contracts", async () => {
  let seen;
  const fetchImpl = async (url, init) => {
    seen = { url: String(url), init };
    return { ok: true, json: async () => ({ schema_version: "greytheory.workbench.v1", live_target_available: false, sections: [] }) };
  };
  await fetchWorkbenchSnapshot({ baseUrl: "http://127.0.0.1:8765", token, fetchImpl });
  assert.equal(seen.url, "http://127.0.0.1:8765/api/v1/snapshot");
  assert.equal(seen.init.headers.Authorization, `Bearer ${token}`);
  await assert.rejects(
    fetchWorkbenchSnapshot({
      baseUrl: "http://127.0.0.1:8765",
      token,
      fetchImpl: async () => ({ ok: true, json: async () => ({ schema_version: "greytheory.workbench.v1", live_target_available: true }) }),
    }),
    /unsafe snapshot/,
  );
});

test("snapshot records replace only panels with server-owned sections", () => {
  const fallback = { Overview: { title: "Fallback", subtitle: "fixture", stats: [], rows: [], boundary: "fixture" }, Experiments: { title: "Experiments", subtitle: "fixture", stats: [], rows: [], boundary: "fixture" } };
  const panels = panelsFromSnapshot({ sections: [{ id: "overview", status: "ready", note: "Measured locally.", metrics: [{ label: "Open", value: "2" }], records: [{ id: "one", title: "One", detail: "Measured", status: "ready", subtitle: "local" }] }] }, fallback);
  assert.equal(panels.Overview.dataSource, "Authenticated local API");
  assert.equal(panels.Overview.rows[0].status, "Ready");
  assert.equal(panels.Experiments.dataSource, "Prototype exemplar");
});

test("commands are schema-bound and refused away from the same application origin", async () => {
  const command = createWorkbenchCommand({
    kind: "start_learning_journey",
    fields: { journey_id: "journey-one" },
    now: new Date("2026-09-02T00:00:00Z"),
    randomId: "test-command",
  });
  assert.equal(command.executable, false);
  assert.equal(command.id, "ui-start_learning_journey-test-command");
  assert.equal(commandMode("http://127.0.0.1:8765", "http://127.0.0.1:4174"), "read_only");
  await assert.rejects(
    sendWorkbenchCommand({
      baseUrl: "http://127.0.0.1:8765",
      token,
      command,
      pageOrigin: "http://127.0.0.1:4174",
      fetchImpl: async () => { throw new Error("must not fetch"); },
    }),
    /same numeric-loopback origin/,
  );
});

test("same-origin command client authenticates and validates non-executing results", async () => {
  let seen;
  const command = createWorkbenchCommand({
    kind: "advance_learning_journey",
    fields: { journey_id: "journey-one" },
    expectedRevision: 0,
    now: new Date("2026-09-02T00:01:00Z"),
    randomId: "advance-one",
  });
  const result = await sendWorkbenchCommand({
    baseUrl: "http://127.0.0.1:8765",
    token,
    command,
    pageOrigin: "http://127.0.0.1:8765",
    fetchImpl: async (url, init) => {
      seen = { url: String(url), init };
      return { ok: true, json: async () => ({ disposition: "accepted", executed: false, record_refs: [] }) };
    },
  });
  assert.equal(result.disposition, "accepted");
  assert.equal(seen.url, "http://127.0.0.1:8765/api/v1/commands");
  assert.equal(JSON.parse(seen.init.body).expected_revision, 0);
});

async function sendWith(payload) {
  return sendWorkbenchCommand({
    baseUrl: "http://127.0.0.1:8765",
    token,
    command: createWorkbenchCommand({
      kind: "review_programme",
      fields: { programme_id: "p", reviewer: "chase" },
      humanAcknowledged: true,
      now: new Date("2026-09-15T12:00:00Z"),
      randomId: "review-one",
    }),
    pageOrigin: "http://127.0.0.1:8765",
    fetchImpl: async () => ({ ok: true, json: async () => payload }),
  });
}

test("a refusal reaches the operator in the server's own words", async () => {
  // Governance refusals are the whole point of these gates; flattening them
  // into a generic error would say nothing about what to do next.
  await assert.rejects(
    sendWith({
      disposition: "invalid",
      executed: false,
      code: "command_refused",
      message: "a blocked contract cannot be reviewed into verification; resolve its 2 ambiguity/ies and recompile",
    }),
    /resolve its 2 ambiguity\/ies and recompile/,
  );
});

test("a refusal with no message still names its disposition", async () => {
  await assert.rejects(
    sendWith({ disposition: "conflict", executed: false }),
    /refused this command \(conflict\)/,
  );
});

test("a result claiming execution is refused whatever its disposition", async () => {
  // This application routes bounded commands and never runs anything, so a
  // result that claims otherwise is a protocol fault, not a refusal.
  await assert.rejects(
    sendWith({ disposition: "accepted", executed: true, message: "ran it" }),
    /unsupported command result/,
  );
  await assert.rejects(
    sendWith({ disposition: "invalid", executed: true, message: "ran it" }),
    /unsupported command result/,
  );
});

test("a payload with no disposition at all is unsupported rather than a refusal", async () => {
  await assert.rejects(sendWith({ executed: false }), /unsupported command result/);
  await assert.rejects(sendWith(null), /unsupported command result/);
});

test("learning snapshot projection restores active journey and case-pack metadata", () => {
  const state = learningStateFromSnapshot({
    context: { learning_journey_id: "journey-one" },
    sections: [{
      id: "learning",
      metrics: [{ label: "Fixture receipts", value: "2" }],
      records: [
        { id: "recommendation:idor-bola:test", title: "IDOR" },
        { id: "journey-one", attributes: { stage: "practise", revision: "1", track: "standard" } },
        { id: "case-pack:agent-authorization-boundary:1.0.0", attributes: { current_posture: "LOCAL_FIXTURE" } },
      ],
    }],
  });
  assert.equal(state.journey.stage, "practise");
  assert.equal(state.journey.revision, 1);
  assert.equal(state.packs.length, 1);
  assert.equal(state.fixtureReceiptCount, 2);
});

test("coach snapshot projection restores only bounded public inferred history for the active pack", () => {
  const safe = {
    id: "coach-turn:one",
    attributes: {
      turn_id: "one",
      case_pack_id: "session-role-transition",
      question: "What evidence is enough?",
      answer: "Preserve both controls.",
      claim_tag: "inferred",
      provider_id: "local.tutor",
      model: "deterministic-tutor-1",
      cost: "0",
      data_class: "PUBLIC",
      external_action: "false",
      awards_mastery: "false",
      created_at: "2026-09-04T17:30:00+00:00",
      source_1_title: "OWASP · Session Management",
      source_1_url: "https://cheatsheetseries.owasp.org/",
    },
  };
  const wrongPack = { ...safe, id: "coach-turn:two", attributes: { ...safe.attributes, turn_id: "two", case_pack_id: "agent-authorization-boundary" } };
  const unsafe = { ...safe, id: "coach-turn:three", attributes: { ...safe.attributes, turn_id: "three", external_action: "true" } };
  const turns = coachHistoryFromSnapshot({ sections: [{ id: "coach", records: [safe, wrongPack, unsafe] }] }, "session-role-transition");

  assert.equal(turns.length, 1);
  assert.equal(turns[0].id, "one");
  assert.equal(turns[0].persisted, true);
  assert.equal(turns[0].guidance.dataClass, "PUBLIC");
  assert.deepEqual(turns[0].guidance.sources, [{ title: "OWASP · Session Management", url: "https://cheatsheetseries.owasp.org/" }]);
});

test("curriculum topics arrive ranked, per programme, with their reasons", () => {
  const snapshot = {
    sections: [
      {
        id: "curriculum",
        note: "teaching aid, not a test plan",
        records: [
          {
            id: "curriculum:acme:bfla",
            detail: "the scope names an API surface",
            attributes: {
              programme_id: "acme", card_id: "bfla", rank: "2", score: "1",
              matched_assets: "api.acme.com", matched_context: "",
            },
          },
          {
            id: "curriculum:acme:idor-bola",
            detail: "the scope names an API surface",
            attributes: {
              programme_id: "acme", card_id: "idor-bola", rank: "1", score: "2",
              matched_assets: "api.acme.com,www.acme.com", matched_context: "",
            },
          },
          {
            id: "study-note:acme:1",
            detail: "Availability testing is prohibited.",
            attributes: { programme_id: "acme", kind: "prohibited_technique_note" },
          },
        ],
      },
    ],
  };

  const curriculum = curriculumFromSnapshot(snapshot);
  assert.equal(curriculum.available, true);
  assert.equal(curriculum.programmes.length, 1);

  const [acme] = curriculum.programmes;
  assert.deepEqual(acme.topics.map((topic) => topic.cardId), ["idor-bola", "bfla"]);
  assert.equal(acme.topics[0].matchedAssets.length, 2);
  assert.equal(acme.notes.length, 1);
  // Every topic must explain itself.
  assert.ok(acme.topics.every((topic) => topic.reason.length > 0));
});

test("an absent curriculum section reports unavailable rather than empty topics", () => {
  const curriculum = curriculumFromSnapshot({ sections: [] });
  assert.equal(curriculum.available, false);
  assert.deepEqual(curriculum.programmes, []);
  assert.deepEqual(curriculumFromSnapshot(null).programmes, []);
});
