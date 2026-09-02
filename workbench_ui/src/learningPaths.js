export const LEARNING_TOPICS = [
  {
    id: "prompt-boundaries",
    title: "Prompt-injection boundaries",
    duration: "10 min",
    level: "Intro",
    copy: "Separate untrusted instructions from trusted system and tool context.",
    lede: "Prompt injection is an instruction-origin problem. Treat retrieved pages, files, messages, and tool output as data until a trusted policy and current user intent say otherwise.",
    principles: [
      ["Instruction provenance", "Record where every instruction came from before it can influence an action."],
      ["Trust separation", "Keep untrusted content outside system rules, credentials, and authority-bearing context."],
      ["Data minimisation", "Expose only the information needed to complete the approved learning task."],
      ["Fail-closed handling", "Pause or deny when instruction origin, purpose, or authority is ambiguous."],
    ],
    traditional: ["Input trust boundaries", "Treat externally supplied content as hostile input and validate where it crosses a boundary.", "Injection prerequisite"],
    ai: ["Instruction hierarchy", "Ask whether retrieved content is trying to become a command, override policy, or steer a tool call.", "Indirect injection aware"],
    checkpoints: [
      "Untrusted content is data, not authority.",
      "Instruction origin must remain inspectable.",
      "A boundary test changes one trust variable at a time.",
      "A denial proves only the tested fixture and policy.",
    ],
    lessons: [
      ["01", "Spot the boundary", "Beginner", "Identify trusted and untrusted instruction sources."],
      ["02", "Map instruction flow", "Foundation", "Trace how content reaches a model, memory, and tools."],
      ["03", "Run paired controls", "Applied", "Compare a direct request with the same text inside a document."],
      ["04", "Explain the limit", "Transfer", "State what the evidence proves and what remains unknown."],
    ],
    resources: [
      ["OWASP", "Prompt Injection", "https://genai.owasp.org/llmrisk/llm01-prompt-injection/"],
      ["PortSwigger Academy", "Web LLM attacks", "https://portswigger.net/web-security/llm-attacks"],
    ],
  },
  {
    id: "tool-authorization",
    title: "Agent tool authorization",
    duration: "15 min",
    level: "Core",
    copy: "Decide which tools an agent may use, under which conditions, and with what scope.",
    lede: "A tool being available is not authority to use it. A defensible decision joins identity, current consent, allowed purpose, minimal scope, trusted instruction origin, and an auditable result.",
    principles: [
      ["Least privilege", "Grant only the capability needed for the current approved purpose."],
      ["Explicit consent", "Require clear, current human intent before sensitive or external actions."],
      ["Purpose binding", "Reject a technically valid tool call when it does not match the authorised task."],
      ["Audit and observe", "Bind the decision, inputs, and result to an inspectable evidence receipt."],
    ],
    traditional: ["Access control", "Ask who is acting, what resource is requested, and whether policy permits it.", "IDOR / BOLA prerequisite"],
    ai: ["Delegated agency", "Also ask where the instruction came from and whether tool output could expand authority.", "Tool-use aware"],
    checkpoints: [
      "A tool grant is capability, not authority.",
      "Consent must be current and purpose-specific.",
      "A negative control tests the authorization boundary.",
      "A receipt proves integrity, not real-world impact.",
    ],
    lessons: [
      ["01", "Capability vs authority", "Beginner", "Separate what a tool can do from what it may do now."],
      ["02", "Build the decision", "Foundation", "Join identity, intent, purpose, scope, and origin."],
      ["03", "Test the gate", "Applied", "Run allowed and denied local-fixture controls."],
      ["04", "Review the receipt", "Transfer", "Defend the decision using evidence and limitations."],
    ],
    resources: [
      ["PortSwigger Academy", "Access control", "https://portswigger.net/web-security/access-control"],
      ["MCP", "Security best practices", "https://modelcontextprotocol.io/specification/draft/basic/security_best_practices"],
    ],
  },
  {
    id: "mcp-abuse",
    title: "MCP tool abuse patterns",
    duration: "10 min",
    level: "Applied",
    copy: "Recognize risky tool schemas, broad grants, and confused-deputy behavior.",
    lede: "Tool protocols make capabilities composable, but composition also creates new trust paths. Review descriptions, parameters, credentials, output handling, and confirmation gates as one system.",
    principles: [
      ["Narrow schemas", "Prefer explicit, constrained parameters over free-form commands or broad file access."],
      ["Credential separation", "Keep secrets outside model-visible context and bind them to one intended service."],
      ["Confused-deputy defence", "Do not let a lower-trust caller borrow a tool's higher-trust identity."],
      ["Result containment", "Treat tool output as untrusted until it is validated for its next destination."],
    ],
    traditional: ["API threat modelling", "Review authentication, authorization, validation, data flow, and side effects at each interface.", "API security lens"],
    ai: ["Tool-chain reasoning", "Trace how model decisions, tool metadata, credentials, and returned content can combine into excess agency.", "MCP-aware"],
    checkpoints: [
      "A broad schema expands both capability and ambiguity.",
      "Tool descriptions are not a security policy.",
      "Credentials must not inherit model context trust.",
      "Tool output can become the next injection source.",
    ],
    lessons: [
      ["01", "Read the schema", "Beginner", "Mark every parameter, resource, and possible side effect."],
      ["02", "Trace delegated trust", "Foundation", "Map identities and credentials across the tool chain."],
      ["03", "Find abuse paths", "Applied", "Test confused-deputy and output-injection cases locally."],
      ["04", "Design a safer contract", "Transfer", "Constrain input, authority, confirmation, and evidence."],
    ],
    resources: [
      ["MCP", "Security best practices", "https://modelcontextprotocol.io/specification/draft/basic/security_best_practices"],
      ["OWASP", "Agentic AI threats", "https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/"],
    ],
  },
];

export const SKILL_TRACKS = [
  {
    id: "foundations",
    title: "Foundations",
    completed: 3,
    lessons: [
      ["Security ethics", "Beginner", "20 min"], ["Scope and authority", "Beginner", "25 min"], ["Evidence basics", "Beginner", "30 min"], ["Trust boundaries", "Foundation", "30 min"],
      ["Threat modelling", "Foundation", "40 min"], ["Safe experiments", "Applied", "40 min"], ["Probability language", "Applied", "25 min"], ["Independent case", "Transfer", "60 min"],
    ],
  },
  {
    id: "web-api",
    title: "Web & API Security",
    completed: 4,
    lessons: [
      ["HTTP and sessions", "Beginner", "30 min"], ["Access control", "Beginner", "35 min"], ["IDOR / BOLA", "Foundation", "45 min"], ["Input handling", "Foundation", "40 min"],
      ["API authorization", "Applied", "50 min"], ["Business logic", "Applied", "55 min"], ["Evidence quality", "Applied", "40 min"], ["Independent report", "Transfer", "75 min"],
    ],
  },
  {
    id: "agent-security",
    title: "Agent Security",
    completed: 1,
    lessons: [
      ["AI trust boundaries", "Beginner", "25 min"], ["Prompt injection", "Foundation", "35 min"], ["Tool authorization", "Foundation", "40 min"], ["Context isolation", "Applied", "40 min"],
      ["MCP abuse patterns", "Applied", "50 min"], ["Memory poisoning", "Applied", "45 min"], ["Agent evidence", "Applied", "45 min"], ["Independent agent case", "Transfer", "90 min"],
    ],
  },
];

export function topicById(id) {
  return LEARNING_TOPICS.find((topic) => topic.id === id) || LEARNING_TOPICS[0];
}
