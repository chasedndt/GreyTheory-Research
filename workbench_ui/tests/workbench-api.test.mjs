import assert from "node:assert/strict";
import test from "node:test";

import {
  fetchWorkbenchSnapshot,
  panelsFromSnapshot,
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
