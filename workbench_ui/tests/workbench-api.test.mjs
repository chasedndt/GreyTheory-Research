import assert from "node:assert/strict";
import test from "node:test";

import {
  commandMode,
  createWorkbenchCommand,
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
