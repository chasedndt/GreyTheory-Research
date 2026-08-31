const commonBoundary = "Synthetic local-fixture data only. No target action is available from this panel.";

export const panelData = {
  Overview: {
    title: "Research overview",
    subtitle: "Current local research state, evidence health, and next governed actions.",
    action: "Review open work",
    stats: [["Active hypotheses", "3"], ["Executed experiments", "2"], ["Verified receipts", "4"], ["Claims ready", "0"]],
    rows: [
      { id: "OV-01", title: "IDOR/BOLA evidence review", detail: "Three minimum-evidence checks remain before this claim can advance.", status: "Needs review", tone: "observed", kind: "Next safe action" },
      { id: "OV-02", title: "Authentication learning track", detail: "Reflection recorded; independent transfer evidence is still required.", status: "In progress", tone: "observed", kind: "Learning" },
      { id: "OV-03", title: "Local authority package", detail: "Scope and rules verified for LOCAL_FIXTURE only.", status: "Verified", tone: "verified", kind: "Governance" },
    ],
    boundary: commonBoundary,
  },
  Hypotheses: {
    title: "Hypotheses",
    subtitle: "Ranked research questions remain proposals until evidence and human review support them.",
    action: "Draft hypothesis",
    stats: [["Total", "3"], ["Unproven", "2"], ["Review due", "1"], ["Promoted", "0"]],
    rows: [
      { id: "GT-2026-08-27-0001", title: "IDOR/BOLA in document access", detail: "Identifier substitution may cross the synthetic account boundary.", status: "Unproven", tone: "observed", kind: "IDOR/BOLA" },
      { id: "GT-2026-08-27-0002", title: "Session state after local role change", detail: "Existing fixture session may retain a previous synthetic role.", status: "Draft", tone: "observed", kind: "Authentication" },
      { id: "GT-2026-08-27-0003", title: "Fixture export field minimisation", detail: "Private export may include a field not needed by the review package.", status: "Queued", tone: "verified", kind: "Data exposure" },
    ],
    boundary: "Ranking is decision support, not probability, severity, proof, or authority to execute.",
  },
  Experiments: {
    title: "Experiments",
    subtitle: "Controlled local procedures with explicit budgets, expected evidence, and stop conditions.",
    action: "Plan experiment",
    stats: [["Planned", "1"], ["Executed", "2"], ["Stopped", "0"], ["External", "0"]],
    rows: [
      { id: "EXP-0001", title: "Cross-account document request", detail: "Manual request through the local proxy using two fixture identities.", status: "Executed", tone: "verified", kind: "Manual" },
      { id: "EXP-0002", title: "Negative ownership control", detail: "Confirm denial when the second fixture identity lacks document ownership.", status: "Planned", tone: "observed", kind: "Control" },
      { id: "EXP-0003", title: "Session-role refresh", detail: "Replay a role change entirely inside the deterministic fixture.", status: "Executed", tone: "verified", kind: "Fixture" },
    ],
    boundary: commonBoundary,
  },
  Receipts: {
    title: "Check receipts",
    subtitle: "Integrity records bind local artifacts to validators without claiming real-world truth.",
    action: "Verify receipts",
    stats: [["Recorded", "4"], ["Verified", "4"], ["Mismatch", "0"], ["Exported", "0"]],
    rows: [
      { id: "RCP-0001", title: "experiment_0001 artifact binding", detail: "Request, response, and SHA-256 metadata recorded at 14:10:02.", status: "Verified", tone: "verified", kind: "Experiment" },
      { id: "RCP-0002", title: "authority_v1.0.0 validation", detail: "Fixture scope and posture ceiling validated before the session.", status: "Verified", tone: "verified", kind: "Authority" },
      { id: "RCP-0003", title: "private report package", detail: "Redacted evidence package remains local and immutable.", status: "Recorded", tone: "verified", kind: "Report" },
    ],
    boundary: "A valid receipt proves record integrity only; it does not prove a vulnerability or authorise disclosure.",
  },
  Claims: {
    title: "Claims",
    subtitle: "Evidence-derived researcher statements with explicit confidence and lifecycle gates.",
    action: "Review claim",
    stats: [["Unproven", "2"], ["Checked", "1"], ["Report ready", "0"], ["Submitted", "0"]],
    rows: [
      { id: "CLM-0001", title: "Possible IDOR/BOLA in document access", detail: "Minimum positive and negative controls are still missing.", status: "Unproven", tone: "observed", kind: "Low confidence" },
      { id: "CLM-0002", title: "Fixture role state refreshed correctly", detail: "Deterministic observation is bound to the local session receipt.", status: "Checked", tone: "verified", kind: "Local only" },
      { id: "CLM-0003", title: "Export minimises private fields", detail: "Requires a second validation pass against the stored package.", status: "Unproven", tone: "observed", kind: "Low confidence" },
    ],
    boundary: "Submission and programme-owned outcomes are unavailable. Human acknowledgement cannot replace missing evidence.",
  },
  Reflections: {
    title: "Reflections",
    subtitle: "Private learning notes separate what changed from what remains uncertain.",
    action: "Add reflection",
    stats: [["This session", "1"], ["Linked", "1"], ["Private", "100%"], ["Shared", "0"]],
    rows: [
      { id: "REF-0001", title: "Object ownership needs paired controls", detail: "The observed response is useful, but one path cannot distinguish fixture setup from boundary failure.", status: "Saved", tone: "verified", kind: "IDOR/BOLA" },
      { id: "REF-0002", title: "Transfer evidence remains independent", detail: "Guided completion must not automatically award mastery.", status: "Draft", tone: "observed", kind: "Learning" },
    ],
    boundary: "Reflections are private learning records and never promote claims or mastery by themselves.",
  },
  Knowledge: {
    title: "Knowledge",
    subtitle: "Versioned vulnerability cards, skill relationships, and evidence-bound mastery guidance.",
    action: "Open learning queue",
    stats: [["Cards", "12"], ["Skills", "18"], ["Due reviews", "2"], ["Mastered", "0"]],
    rows: [
      { id: "CARD-IDOR-1.0.0", title: "IDOR/BOLA", detail: "Ownership boundaries, paired identities, controls, and evidence expectations.", status: "Current", tone: "verified", kind: "Access control" },
      { id: "CARD-AUTH-1.0.0", title: "Session and role transitions", detail: "State changes, invalidation, and deterministic verification patterns.", status: "Review due", tone: "observed", kind: "Authentication" },
      { id: "CARD-EVID-1.0.0", title: "Evidence integrity", detail: "Artifact binding, receipts, provenance, and limitations of proof.", status: "Current", tone: "verified", kind: "Method" },
    ],
    boundary: "Guidance is inspectable and deterministic; completion still requires explicit human assessment.",
  },
  Artifacts: {
    title: "Artifacts",
    subtitle: "Local evidence files with provenance, integrity state, and retention visibility.",
    action: "Review retention",
    stats: [["Files", "7"], ["Bound", "7"], ["Unverified", "0"], ["External", "0"]],
    rows: [
      { id: "ART-0001", title: "experiment_0001.har", detail: "Synthetic request/response capture bound to RCP-0001.", status: "Bound", tone: "verified", kind: "HAR · 18 KB" },
      { id: "ART-0002", title: "authority_v1.0.0.json", detail: "Local rules, scope, posture ceiling, and operator requirement.", status: "Bound", tone: "verified", kind: "JSON · 3 KB" },
      { id: "ART-0003", title: "report_private_v2.json", detail: "Private redacted report package; not a disclosure artifact.", status: "Local only", tone: "verified", kind: "JSON · 11 KB" },
    ],
    boundary: "Artifact names and sizes are realistic prototype data; no repository evidence file is exposed by this UI.",
  },
  Templates: {
    title: "Templates",
    subtitle: "Governed structures for hypotheses, experiments, reflections, and private reports.",
    action: "Preview template",
    stats: [["Available", "4"], ["Current", "4"], ["Draft", "0"], ["External", "0"]],
    rows: [
      { id: "TPL-HYP-1", title: "Hypothesis proposal", detail: "Question, rationale, falsifier, evidence needs, and authority reference.", status: "Current", tone: "verified", kind: "Research" },
      { id: "TPL-EXP-1", title: "Controlled experiment plan", detail: "Budget, procedure, expected evidence, stop conditions, and review gate.", status: "Current", tone: "verified", kind: "Experiment" },
      { id: "TPL-RPT-1", title: "Private report draft", detail: "Claim/evidence matrix, validation history, limits, and redaction state.", status: "Current", tone: "verified", kind: "Reporting" },
    ],
    boundary: "Templates structure human work; they do not create authority or bypass application gates.",
  },
  Governance: {
    title: "Governance",
    subtitle: "Posture, authority, gate, and capability truth remain visible before any research decision.",
    action: "Inspect capability truth",
    stats: [["Posture", "LOCAL"], ["Authority", "Verified"], ["Live actions", "0"], ["Open gates", "0"]],
    rows: [
      { id: "GOV-POSTURE", title: "Operating posture", detail: "LOCAL_FIXTURE is the current ceiling for this workspace.", status: "Enforced", tone: "verified", kind: "Policy" },
      { id: "GOV-AUTH", title: "Authority package", detail: "Synthetic fixture scope confirmed; external systems excluded.", status: "Verified", tone: "verified", kind: "Authority" },
      { id: "GOV-PASSIVE", title: "PASSIVE_HTTP capability", detail: "Unavailable pending accepted worker, egress, secret-provider, and host proof.", status: "Blocked", tone: "blocked", kind: "Capability" },
    ],
    boundary: "The UI displays policy state but cannot grant authority or execute a broker action directly.",
  },
  Workspaces: {
    title: "Workspaces",
    subtitle: "Local research contexts remain isolated by posture, data location, and authority package.",
    action: "Inspect workspace",
    stats: [["Available", "1"], ["Active", "1"], ["Cloud", "0"], ["Live", "0"]],
    rows: [
      { id: "WS-LOCAL", title: "LOCAL_FIXTURE", detail: "Synthetic two-account workspace with local evidence and no external network.", status: "Active", tone: "verified", kind: "Local" },
      { id: "WS-PASSIVE", title: "Passive research pilot", detail: "Reserved until Ubuntu worker/service acceptance and operator posture approval.", status: "Unavailable", tone: "blocked", kind: "Future" },
    ],
    boundary: "Only LOCAL_FIXTURE can be selected. A workspace label never raises the operating posture.",
  },
  Settings: {
    title: "Settings",
    subtitle: "Local display and review preferences; security boundaries are not user-adjustable here.",
    action: "Confirm local settings",
    stats: [["Storage", "Local"], ["Telemetry", "Off"], ["Sharing", "Off"], ["Theme", "Dark"]],
    rows: [
      { id: "SET-PRIVACY", title: "Private local storage", detail: "Prototype session data stays inside the current browser session.", status: "On", tone: "verified", kind: "Privacy" },
      { id: "SET-TELEMETRY", title: "Product telemetry", detail: "No analytics or remote product telemetry is connected.", status: "Off", tone: "verified", kind: "Privacy" },
      { id: "SET-MOTION", title: "Reduced motion", detail: "The interface follows the operating-system motion preference.", status: "System", tone: "verified", kind: "Accessibility" },
    ],
    boundary: "Posture, gates, authority, and external-network capability cannot be changed from Settings.",
  },
};

export const defaultPanelData = panelData.Overview;
