export const reflectedXss = {
  id: "reflected-xss",
  trackId: "web-api",
  cardId: "reflected-xss",
  title: "Reflected cross-site scripting",
  level: "Foundation",
  duration: "40 min",
  oneLine: "The server hands your input back to the browser, and the browser does what the document tells it.",

  concept: [
    "A value from the request appears in the response. If it lands somewhere the browser parses as structure rather than text, it stops being content and becomes part of the page. The browser has no way to tell the difference - it receives one document and parses all of it.",
    "This is the injection shape with the browser as the interpreter, and that changes who is harmed. A query flaw affects the database; this one affects whichever person loads the page. That is why the proof must be demonstrated on yourself, and why escalation towards other users is never part of establishing the finding.",
    "Context decides everything. The same value is inert between tags, dangerous inside an attribute, and dangerous in a different way inside a script block or a URL. Encoding is only correct relative to a destination, which is why a filter written for one context routinely fails in another.",
  ],

  traditional: {
    heading: "Locate the reflection before you test it",
    body: [
      "Send a unique, harmless marker and find every place it appears in the response. You are mapping reflection points and their contexts, not attempting anything yet. A single parameter often lands in several contexts at once, and only one of them may be exploitable.",
      "Then read what encoding is applied, character by character, in the context that matters. A response that encodes angle brackets but returns quotes intact tells you precisely where the gap is. That observation is the finding; a working payload is a demonstration of it.",
    ],
  },

  aiNative: {
    heading: "Model output is untrusted content",
    body: [
      "Anywhere a model's output is rendered as rich content - markdown, HTML, a tool result panel - you have the same sink. And model output is untrusted by construction whenever it summarises or quotes something untrusted, so the value crossing into the renderer carries whatever was in the source material.",
      "The second-order version is more interesting: the reader may be another agent. Content rendered into an agent-facing view can carry instructions, and the agent parses the whole view the way a browser parses a whole document. Same failure, different interpreter.",
    ],
  },

  workedExample: {
    heading: "One concrete case",
    scenario: "A search page echoes your query back into the results heading. You are testing your own session, in a programme that permits it.",
    steps: [
      ["Place a unique marker", "Search for a distinctive harmless string. Find every occurrence in the response and note the context each one landed in."],
      ["Read the encoding", "Send the characters that delimit that specific context and observe which come back encoded. This is the measurement; everything after it is demonstration."],
      ["Show it parses as structure", "Introduce a benign element or attribute and confirm the browser created a node rather than displaying text. Parsing is the property that matters, not any particular payload."],
      ["Stop at your own session", "The capability is established. Directing it at another person is neither necessary for the evidence nor permitted by any programme."],
    ],
    lesson: "The finding is complete at 'the response places my value in a parsed context without the encoding that context requires'. A more dramatic payload adds no information and increases the chance of affecting somebody real.",
  },

  proofLooksLike: [
    "The parameter, and the exact place in the response where its value was reflected.",
    "The context named explicitly - HTML body, attribute, script string, URL - since the fix differs by context.",
    "Which characters were encoded and which were not, evidenced by request and response.",
    "Evidence the browser parsed the value as a node rather than rendering it as text.",
    "Demonstrated only in your own session, with no payload that would reach another user.",
  ],

  checks: [
    {
      id: "rx-1",
      kind: "recognise",
      prompt: "A reflected value has `<script>` stripped from it. Why might the page still execute your input?",
      hints: [
        "Ask whether a script tag is the only construct that runs code.",
        "Consider where the value actually lands in the document.",
        "Event-handler attributes and other elements execute without a script tag ever appearing.",
      ],
      options: [
        { id: "a", label: "It cannot — removing the script tag removes the ability to run code", explain: "That treats one tag name as the whole category. Many elements and attributes cause execution, and the value may not even be landing in a context where a tag is the relevant syntax." },
        { id: "b", label: "Many other constructs execute, and the filter addressed one spelling of one of them", correct: true, explain: "Correct. Event-handler attributes, other elements, and various framework sinks all execute without the literal string appearing. Blocklists of this kind describe what someone thought of, not what the context permits." },
        { id: "c", label: "Only if the response has no Content-Security-Policy", explain: "A policy can make exploitation much harder and is worth reporting on, but it is defence in depth. The encoding flaw exists independently, and a policy is frequently weakened elsewhere on the site." },
      ],
    },
    {
      id: "rx-2",
      kind: "decide",
      prompt: "You have confirmed, in your own session, that the value is parsed as markup. Do you now build a payload that captures a session cookie to demonstrate impact?",
      hints: [
        "Ask what question that payload answers which the parsing proof has not.",
        "Consider whose data the payload would reach if anything went wrong.",
        "Capability is established; a credential-stealing payload adds no evidence and can reach real users.",
      ],
      options: [
        { id: "a", label: "Yes — triagers need demonstrated impact to rate the severity", explain: "Impact follows as an argument from demonstrated script execution in a page served to users. Triage teams accept that reasoning; they do not require you to capture anybody's credentials to believe it." },
        { id: "b", label: "No — capability is proven, and such a payload adds no evidence while risking real users", correct: true, explain: "Correct. The evidential question - does the browser parse my value as code - is already answered. Anything beyond it changes risk without changing what is known." },
        { id: "c", label: "Yes, but only capturing your own cookie", explain: "Harmless, and therefore also evidentially empty: you already control that session, so capturing it demonstrates nothing the parsing proof did not. It mostly invites the next step, which is not harmless." },
      ],
    },
    {
      id: "rx-3",
      kind: "prove",
      prompt: "Which evidence most robustly shows the browser parsed your value as markup rather than displaying it as text?",
      hints: [
        "Ask what a reviewer can independently verify from your artifact.",
        "Consider which evidence shows both what was sent and how it was parsed.",
        "The response bytes in context, plus the resulting element in the document tree.",
      ],
      options: [
        { id: "a", label: "A screenshot of the page looking visibly wrong", explain: "Visual difference has many causes, including plain text that merely looks odd. It does not establish that anything was parsed as structure." },
        { id: "b", label: "The response showing the value unencoded in its context, with the resulting element in the document tree", correct: true, explain: "Correct. Together these show what the server returned and what the browser made of it, and a reviewer can re-derive both from the request you supplied." },
        { id: "c", label: "A popup dialog appearing in your browser", explain: "It does demonstrate execution, and many programmes accept it. But as an artifact it is the least inspectable - it shows neither what was sent nor how it was parsed - and some programmes ask for non-disruptive proof. Pair it with the request and the document evidence rather than sending it alone." },
      ],
    },
  ],
};
