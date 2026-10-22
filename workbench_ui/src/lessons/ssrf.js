export const ssrf = {
  id: "ssrf",
  trackId: "web-api",
  cardId: "ssrf",
  title: "Server-side request forgery",
  level: "Applied",
  duration: "45 min",
  oneLine: "The request is ordinary. The thing making it is standing somewhere you are not.",

  concept: [
    "Somewhere in most applications a server fetches a URL on your behalf - a webhook, an image preview, a registry pull, a PDF renderer, a document import. When you influence that URL, you are not making the request. The server is, from its own network position.",
    "That position is the vulnerability. The identical request from your machine reaches nothing interesting; from inside the network it may reach an admin service on loopback, a database with no external listener, an internal API that trusts its callers, or a cloud metadata endpoint that hands out credentials to anything that asks. Nothing about the request is malformed - it is simply being made by the wrong party.",
    "This is the same confused-deputy shape as cross-site request forgery, inverted. There, the browser lends the user's credentials to another site's intent. Here, the server lends its network position to yours. Recognising the shape is worth more than the individual technique, because it tells you where to look: anywhere authority is exercised on someone else's say-so.",
  ],

  traditional: {
    heading: "Finding the fetcher, and what it trusts",
    body: [
      "Enumerate every place a URL, hostname, or file reference reaches the server and might be retrieved. Import-by-URL, avatar-from-link, webhook registration, callback parameters, XML with external entities, and anything described as a preview are the usual candidates. The parameter is often not obviously a URL.",
      "Then ask what validation stands in front of it, and test that specifically. Deny-lists are the common failure: they must anticipate every spelling of an address - decimal, octal, IPv6-mapped, a hostname that resolves to a private range, a redirect to one - and validation usually happens before resolution, so the name checked is not necessarily the address connected to.",
    ],
  },

  aiNative: {
    heading: "An agent with a fetch tool is a fetcher",
    body: [
      "Give a model a browsing or retrieval tool and you have built exactly this pattern, with the URL chosen by whatever the model just read. Content in a page can therefore direct the agent's next fetch, and the agent makes it from wherever it runs - which in practice is often a machine with internal reachability and credentials in its environment.",
      "The defence is not a better-behaved model. It is the same as the traditional one, moved outward: constrain what the fetcher may reach, and make the network position boring. An agent that can only egress through a controlled, fail-closed path cannot be talked into reaching something it has no route to.",
    ],
  },

  workedExample: {
    heading: "One concrete case",
    scenario: "A feature accepts a URL and renders a preview of it. You want to know whether the server retrieves it, and what it will accept - using a host you control as the target throughout.",
    steps: [
      ["Point it at yourself", "Supply a URL on a host you own, with a unique path for this single test. Watch that host's logs. A hit proves the server fetches, and the source address tells you who fetched."],
      ["Read the request it made", "The user agent, headers, and source address describe the fetcher. This alone establishes the capability, and it never touches anyone else's infrastructure."],
      ["Test one piece of validation", "If a scheme or host appears to be restricted, probe that specific rule - for example whether a redirect from your own permitted host is followed. Change one thing at a time."],
      ["Decide whether it is blind", "If the response body comes back to you, say so. If nothing returns but your log shows the hit, it is blind - still a finding, and the distinction belongs in the report because it changes the impact argument."],
    ],
    lesson: "The finding is complete at 'the server makes requests I control, from its own position'. Aiming the next request at internal infrastructure would prove nothing further about the flaw and would reach systems no programme authorised you to touch.",
  },

  proofLooksLike: [
    "The feature and the exact parameter whose value became the fetched URL.",
    "A request log from a host you control, with a unique per-test path, showing the connection arriving from the server rather than your browser.",
    "Whether the response was returned to you or the fetch was blind, stated explicitly.",
    "What validation exists, evidenced by one probe against it - not a list of everything you tried.",
    "No requests directed at internal, third-party, or cloud-metadata endpoints.",
  ],

  checks: [
    {
      id: "ssrf-1",
      kind: "recognise",
      prompt: "An endpoint fetches a URL you supply but returns nothing to you. Why might this still be a finding?",
      hints: [
        "Ask whether reading the response is the only thing the capability is good for.",
        "Consider where the server sits relative to you.",
        "The server's network position reaches hosts you cannot, and out-of-band evidence proves the request happened.",
      ],
      options: [
        { id: "a", label: "It is not — without a response there is nothing to demonstrate", explain: "The demonstration is that the server made a request you controlled. A log on a host you own evidences that directly, with no response body required." },
        { id: "b", label: "The server's position reaches hosts you cannot, and out-of-band evidence proves the request", correct: true, explain: "Correct. This is blind SSRF. The capability - the server making attacker-influenced requests from inside the network - exists whether or not the body comes back, and the log entry is the evidence." },
        { id: "c", label: "Only if you can make it return the response through an error message", explain: "That would be one escalation route, but it is not required for the finding. Treating it as required understates a real flaw and tempts you into pushing further than the evidence needs." },
      ],
    },
    {
      id: "ssrf-2",
      kind: "decide",
      prompt: "The application rejects URLs containing `127.0.0.1` and `169.254.169.254`. Is that sufficient?",
      hints: [
        "Ask how many ways one address can be written.",
        "Consider what happens between validating a name and connecting to it.",
        "A deny-list must anticipate every spelling and every redirect, and the name is resolved after it is checked.",
      ],
      options: [
        { id: "a", label: "Yes — the dangerous destinations are blocked", explain: "Only those two literal strings are blocked. The same destinations are reachable by decimal or octal notation, IPv6 forms, a hostname that resolves there, or a redirect from a permitted host." },
        { id: "b", label: "No — a deny-list must anticipate every spelling and every redirect, and resolution happens after validation", correct: true, explain: "Correct, and the second half is the subtle part: the string is checked, then the name is resolved, so what was validated is not necessarily what is connected to. An allow-list plus resolve-then-verify-then-connect is the shape that holds." },
        { id: "c", label: "Yes, provided all private address ranges are blocked as well", explain: "Still a deny-list, just a longer one. It remains vulnerable to redirects, to a name that resolves to a permitted address at check time and a private one at connect time, and to whichever notation was not enumerated." },
      ],
    },
    {
      id: "ssrf-3",
      kind: "prove",
      prompt: "What shows the server made the request, rather than your own browser?",
      hints: [
        "Ask what a sceptic would say produced the network traffic.",
        "Which observation identifies the party that connected?",
        "A log on a host you control records the source address and a path unique to that test.",
      ],
      options: [
        { id: "a", label: "The application displayed the content of the fetched page", explain: "Suggestive, but a sceptic will note your browser could have loaded it. Rendering alone does not identify which party made the outbound connection." },
        { id: "b", label: "A log on a host you control showing the connection, its source address, and a unique per-test path", correct: true, explain: "Correct. The source address names the fetcher, and the unique path ties that specific hit to that specific submission, so the evidence cannot be confused with unrelated traffic." },
        { id: "c", label: "The response took noticeably longer when pointed at an unreachable host", explain: "Timing hints that something attempted a connection, but it is circumstantial and attributable to several causes. It is worth recording alongside proof, never instead of it." },
      ],
    },
  ],
};
