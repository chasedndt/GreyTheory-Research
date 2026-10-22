export const httpAndSessions = {
  id: "http-and-sessions",
  trackId: "web-api",
  // Claims the session-management card: this lesson already teaches identifier
  // storage, the cookie flags, and lifecycle transitions, so binding it here is
  // linking existing material rather than writing a second copy of it.
  cardId: "session-management",
  title: "HTTP and sessions",
  level: "Beginner",
  duration: "30 min",
  oneLine: "HTTP forgets you between requests. Everything about identity on the web is a workaround for that.",

  concept: [
    "HTTP is stateless. Each request arrives with no memory of the last one, so a server that needs to know who you are must be told again every single time. A session is the mechanism for re-telling it, and every session flaw is a flaw in that re-telling.",
    "A session identifier is a bearer token in the literal sense: whoever bears it is treated as the user. It carries no proof that the holder is the person who logged in. This is why session identifiers leak into the same category as passwords, and why where they are stored matters as much as how they are generated.",
    "Authentication and authorization are different questions and get confused constantly. Authentication asks who you are. Authorization asks whether you may do this specific thing to this specific object. A correctly authenticated user doing something they should not is the most common finding in bug bounty.",
  ],

  traditional: {
    heading: "Where sessions go wrong",
    body: [
      "Predictable identifiers let one be guessed. Identifiers in URLs leak through referrer headers, browser history, and server logs. Missing `Secure` allows transmission over plaintext; missing `HttpOnly` allows script access; missing or weak `SameSite` enables cross-site request forgery.",
      "Lifecycle matters as much as storage. A session that survives logout, does not rotate on privilege change, or never expires converts a one-time capture into indefinite access. Test the transitions, not just the steady state.",
    ],
  },

  aiNative: {
    heading: "Sessions in agent systems",
    body: [
      "An agent acting for a user holds that user's authority for the length of a conversation, which is usually far longer than a considered decision. A grant given for one task tends to persist across many, and the model has no concept of the grant having been spent.",
      "Worse, agent memory can outlive the session that authorised it. If a summary of an earlier authenticated action stays in context after logout, the agent may act on remembered authority that the server has already revoked. Re-bind every sensitive action to current server state, never to remembered context.",
    ],
  },

  workedExample: {
    heading: "One concrete case",
    scenario: "You want to know whether logout actually ends a session.",
    steps: [
      ["Capture an authenticated request", "Record a request that succeeds while logged in, including the session cookie."],
      ["Log out through the interface", "Use the application's own logout, exactly as a user would."],
      ["Replay the original request", "Same cookie, same endpoint. Change nothing else."],
      ["Read the result", "A 401 or 403 means the server invalidated the session. A 200 with your data means logout only cleared the browser, and the identifier still works."],
    ],
    lesson: "The single-variable discipline matters here. If you also cleared cookies or changed browsers, a failure would tell you nothing about the server's behaviour.",
  },

  proofLooksLike: [
    "The authenticated request and response captured before logout.",
    "Evidence that logout was performed through the application's own flow.",
    "The identical replayed request afterwards, with its status and body.",
    "A control showing an invalid identifier is rejected, so the endpoint is checking something.",
  ],

  checks: [
    {
      id: "hs-1",
      kind: "recognise",
      prompt: "A session cookie is set without `HttpOnly`. What does that specifically enable?",
      hints: [
        "Ask which party the flag keeps away from the cookie.",
        "Consider what could read it if a script ran on the page.",
        "Without `HttpOnly`, JavaScript can read the cookie, so any XSS becomes session theft.",
      ],
      options: [
        { id: "a", label: "Transmission over plaintext HTTP", explain: "That is what `Secure` controls. `HttpOnly` is about script access within the page, not the transport the cookie travels over." },
        { id: "b", label: "JavaScript can read it, so any XSS becomes session theft", correct: true, explain: "Correct. `HttpOnly` keeps the cookie out of `document.cookie`. Without it, a single injected script can exfiltrate the session identifier and impersonate the user." },
        { id: "c", label: "The cookie is sent on cross-site requests", explain: "That is `SameSite`. The three flags address different threats and are worth keeping distinct when you write the finding." },
      ],
    },
    {
      id: "hs-2",
      kind: "decide",
      prompt: "A session identifier is long, random, and unpredictable, but it never changes after login. Is that sufficient?",
      hints: [
        "Ask when the identifier was created relative to authentication.",
        "Consider whether an attacker could have known the value beforehand.",
        "If the pre-login identifier survives authentication, an attacker who planted it now holds an authenticated session.",
      ],
      options: [
        { id: "a", label: "Yes — unpredictable identifiers cannot be guessed", explain: "Unpredictability defeats guessing, but not fixation. If an attacker planted the identifier before login, they do not need to guess it — they already have it." },
        { id: "b", label: "No — it must rotate at login, or a planted identifier becomes authenticated", correct: true, explain: "Correct. The missing condition is rotation on privilege change. Issuing a fresh identifier at authentication invalidates anything an attacker set beforehand." },
        { id: "c", label: "Yes, provided the cookie has Secure and HttpOnly", explain: "Those flags protect the cookie in transit and from scripts. Neither prevents an attacker from setting a value before login and reusing it afterwards." },
      ],
    },
    {
      id: "hs-3",
      kind: "prove",
      prompt: "What evidence shows a session survived logout, rather than your test being flawed?",
      hints: [
        "Ask what a sceptic would say caused the request to still succeed.",
        "Which control rules out the endpoint simply not checking sessions at all?",
        "A rejected invalid identifier proves the endpoint does check, so acceptance of the logged-out one is meaningful.",
      ],
      options: [
        { id: "a", label: "The replayed request returned 200 with your data", explain: "Necessary but not sufficient. A sceptic will ask whether the endpoint checks sessions at all, in which case the result says nothing about logout specifically." },
        { id: "b", label: "That, plus a control showing an invalid identifier is rejected", correct: true, explain: "Correct. The control proves the endpoint enforces sessions. Given that, acceptance of the logged-out identifier isolates the failure to logout not invalidating server-side." },
        { id: "c", label: "A screenshot of being logged out in the browser", explain: "It shows the client state changed, which nobody disputes. The finding is about the server, and a browser screenshot says nothing about server-side invalidation." },
      ],
    },
  ],
};
