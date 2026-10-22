export const csrf = {
  id: "csrf",
  trackId: "web-api",
  cardId: "csrf",
  title: "Cross-site request forgery",
  level: "Foundation",
  duration: "35 min",
  oneLine: "The browser proves who you are on every request. Nothing in that proves you meant to send it.",

  concept: [
    "A browser attaches cookies to a request based on where the request is going, not on where it came from. So a request your session authorises looks identical whether you clicked a button on the application or a page on another site caused your browser to send it. The credentials are real either way.",
    "This makes cross-site request forgery an authorisation-of-intent problem, not an authentication problem. The server correctly knows who you are; what it does not know is whether you meant this. Checking the session harder will never close it, because the session was never the thing in doubt.",
    "It is the classic confused deputy: a party with legitimate authority is persuaded to use it on someone else's behalf. Recognising that shape matters more than memorising the defences, because the same shape reappears wherever ambient authority is attached automatically.",
  ],

  traditional: {
    heading: "Where intent goes unverified",
    body: [
      "Look for state-changing operations and ask what distinguishes a genuine submission from a forged one. A synchroniser token does it by requiring a value the other site cannot read. An origin or referer check does it by reading where the request came from. If neither is present, only the cookie is being checked, and the cookie is attached automatically.",
      "Then test whether the defence is actually enforced rather than merely present. A token that is issued but never validated, validated only when supplied, or shared across every user's session, is decoration. The interesting result is usually not a missing token but a token nobody checks.",
    ],
  },

  aiNative: {
    heading: "The agent-era confused deputy",
    body: [
      "An agent holding a user's credentials is a deputy in exactly this sense. When it reads a web page, a document, or a tool result and then acts, the question is identical: did the person ask for this, or did content the agent merely read cause it? Prompt injection is the same failure with a different transport.",
      "The defence generalises too. You cannot ask the model to check its own intent, any more than a server can ask a cookie whether the user meant it. Intent must be established outside the channel the untrusted content travels in - a human confirmation bound to the specific action, which is what an approval gate is for.",
    ],
  },

  workedExample: {
    heading: "One concrete case",
    scenario: "An account-settings endpoint changes an email address by POST, on an application where you control the account.",
    steps: [
      ["Capture the genuine request", "Submit the change normally and record the full request: method, headers, body, and which values it carries beyond the session cookie."],
      ["Identify the candidate defence", "Is there a token in the body or a custom header? Does the server appear to read Origin? Name what you are about to test before you test it."],
      ["Remove exactly one thing", "Replay the request with the token absent, changing nothing else. Acceptance means the token was never validated; rejection means it was."],
      ["Run the negative control", "Replay with no session cookie at all. It must be rejected - that proves the endpoint does authenticate, so the earlier acceptance isolates the failure to intent, not to an endpoint that checks nothing."],
    ],
    lesson: "The finding is complete at 'the server accepts a state change without any evidence of intent'. Hosting it on a third-party page adds nothing evidentially and moves you outside the account you were authorised to use.",
  },

  proofLooksLike: [
    "The genuine state-changing request in full, with the defence it appeared to carry named explicitly.",
    "The same request with one element removed, and the server's response accepting it.",
    "A negative control with no session, rejected - showing the endpoint authenticates and the gap is intent.",
    "Evidence the state actually changed, on an account you control, with the change reversed afterwards.",
  ],

  checks: [
    {
      id: "csrf-1",
      kind: "recognise",
      prompt: "A state-changing endpoint requires a valid session cookie and nothing else. Why is that insufficient?",
      hints: [
        "Ask what decides whether the browser attaches the cookie.",
        "Consider whether the server can distinguish the two ways that request might arise.",
        "The cookie is attached automatically by destination, so another site can cause an authenticated request.",
      ],
      options: [
        { id: "a", label: "Nothing — a valid session proves the request is legitimate", explain: "It proves the request came from an authenticated browser, which nobody disputes. It says nothing about whether the person intended it, and that is the whole question." },
        { id: "b", label: "The browser attaches the cookie automatically, so another site can cause the request", correct: true, explain: "Correct. Cookies are attached based on where the request is going. A forged request and a genuine one are indistinguishable at the server, because the credential is identical in both." },
        { id: "c", label: "The endpoint should require HTTPS", explain: "Transport security protects the request in transit from a network observer. It has no bearing on who or what caused the browser to send it." },
      ],
    },
    {
      id: "csrf-2",
      kind: "decide",
      prompt: "The application sets `SameSite=Lax` on its session cookie. Is cross-site request forgery eliminated?",
      hints: [
        "Ask which kinds of cross-site request Lax still permits the cookie on.",
        "Consider an operation that changes state but is reachable by a link.",
        "Lax still sends the cookie on top-level navigations, so a state change reachable by GET remains exposed.",
      ],
      options: [
        { id: "a", label: "Yes — Lax blocks cookies on cross-site requests", explain: "Lax blocks them on most, not all. It deliberately permits top-level navigations so that following an ordinary link does not log you out, and that exemption is the gap." },
        { id: "b", label: "No — Lax still permits top-level navigations, so any state change reachable by GET remains exposed", correct: true, explain: "Correct. Lax narrows the surface considerably but does not close it, and it is why state-changing operations should not be reachable by GET in the first place. Sibling subdomains are a second caveat, since same-site is broader than same-origin." },
        { id: "c", label: "Yes, provided tokens are also validated", explain: "If tokens are validated then the tokens are doing the work, and the question of what Lax alone guarantees is still worth answering correctly - defences should be understood individually, not as an undifferentiated pile." },
      ],
    },
    {
      id: "csrf-3",
      kind: "prove",
      prompt: "What shows the server fails to verify intent, rather than your test being flawed?",
      hints: [
        "Ask what a sceptic would say if the request simply succeeded.",
        "Which control rules out an endpoint that checks nothing at all?",
        "A request with no session must be rejected, or acceptance proves nothing about intent specifically.",
      ],
      options: [
        { id: "a", label: "The request succeeded when the anti-forgery token was removed", explain: "Necessary but not sufficient. A sceptic will ask whether the endpoint validates anything, in which case the result is about a broken endpoint rather than about intent verification." },
        { id: "b", label: "That, plus a control with no session at all being rejected", correct: true, explain: "Correct. The control proves the endpoint does authenticate. Given that, accepting a request with the token removed isolates the failure precisely: identity is checked, intent is not." },
        { id: "c", label: "A page on another origin that triggers the request automatically", explain: "It adds no evidence the removed-token result did not already give, and it moves your testing outside the account you were authorised to use. Capability is established; staging it is escalation." },
      ],
    },
  ],
};
