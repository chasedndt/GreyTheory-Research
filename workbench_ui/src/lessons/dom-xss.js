export const domXss = {
  id: "dom-xss",
  trackId: "web-api",
  cardId: "dom-xss",
  title: "DOM-based cross-site scripting",
  level: "Applied",
  duration: "45 min",
  oneLine: "Nothing reached the server. The flaw is entirely in the code already running on the page.",

  concept: [
    "A value read by client-side script - from the URL fragment, the query string, the referrer, a postMessage, or browser storage - flows into a sink that treats strings as markup or code. The page rewrites itself using a value the page itself chose to trust. No response from the server was ever involved.",
    "The fragment case is the sharp one: everything after `#` is not transmitted. The server never receives it, never logs it, and cannot encode it. So server-side output encoding, a web application firewall, and the access log are all structurally blind to this class - not badly configured, but looking at traffic that does not contain the value.",
    "That moves the work from request-and-response to reading code. You are tracing a path from a source to a sink through the page's own script, which is why this class survives so long in applications whose server-side handling is otherwise careful.",
  ],

  traditional: {
    heading: "Tracing source to sink",
    body: [
      "Enumerate the sources a page reads - `location` and its parts, `document.referrer`, `postMessage` handlers, `localStorage` - and the sinks that interpret strings, such as `innerHTML`, `document.write`, `eval`, the `Function` constructor, and event-handler assignment. The bug is a path between the two, and either end alone is unremarkable.",
      "Frameworks add their own sinks with reassuring names, and those are worth searching for by name. A deliberate escape hatch is still a sink, and it is usually reached by a value somebody assumed was internal.",
    ],
  },

  aiNative: {
    heading: "Rendering what a model returned",
    body: [
      "An agent interface that renders model output as rich content is a sink reached by a source nobody controls. When the model has read untrusted material, its output carries that material's influence, so the path from source to sink runs straight through the model.",
      "Message channels between an embedded agent and its host page deserve the same treatment as any other source. A handler that accepts a message without checking the origin, and then renders or evaluates its contents, is the same flaw with an extra hop.",
    ],
  },

  workedExample: {
    heading: "One concrete case",
    scenario: "A page restores the previously selected tab by reading the URL fragment, in your own session.",
    steps: [
      ["Find the source", "Search the page's script for the source APIs. Note exactly which part of the URL is read and whether anything validates it."],
      ["Follow it to a sink", "Trace the value through assignments until it reaches something that interprets strings. Quote both ends with enough surrounding code to locate them again."],
      ["Demonstrate with a benign marker", "Put a distinctive harmless value in the fragment and confirm the document contains an element built from it, rather than text."],
      ["Show the server never saw it", "Check the network activity for the load. The fragment does not appear in any request - and that absence is the evidence that distinguishes this from reflected scripting."],
    ],
    lesson: "The last step is the one people omit, and it is what makes the report unambiguous: it proves the flaw is client-side and tells the team that server-side encoding will not fix it.",
  },

  proofLooksLike: [
    "The source API the page reads, quoted from its own script.",
    "The sink it reaches, with the path between them.",
    "The benign value used, and the resulting element in the document tree.",
    "Evidence the value was never transmitted - no request carries it - which distinguishes this from a reflected flaw.",
    "Demonstrated only in your own session.",
  ],

  checks: [
    {
      id: "dx-1",
      kind: "recognise",
      prompt: "Why can a server-side web application firewall not detect a fragment-based DOM flaw?",
      hints: [
        "Ask which parts of a URL the browser actually transmits.",
        "Consider what the firewall has available to inspect.",
        "Everything after the `#` stays in the browser and is never sent.",
      ],
      options: [
        { id: "a", label: "Firewalls only inspect POST bodies, not URLs", explain: "They inspect request lines and query strings routinely. The problem is not which part of the request is examined, but that this value is in no part of the request at all." },
        { id: "b", label: "The fragment is never transmitted, so it is absent from the traffic the firewall sees", correct: true, explain: "Correct. The browser strips the fragment before sending. There is nothing to match on, which is why this class is invisible to server-side inspection and logging rather than merely difficult for it." },
        { id: "c", label: "The payload is usually encoded in a way firewalls cannot decode", explain: "Encoding tricks are a real evasion technique for traffic that is inspected. Here no evasion is required, because the value never enters the traffic." },
      ],
    },
    {
      id: "dx-2",
      kind: "decide",
      prompt: "The team responds by adding output encoding on the server. Does that fix a fragment-based DOM flaw?",
      hints: [
        "Ask what the server would be encoding.",
        "Consider where the value comes from and where it is consumed.",
        "The server never handles the value, so it has nothing to encode.",
      ],
      options: [
        { id: "a", label: "Yes — output encoding is the standard remedy for scripting flaws", explain: "It is the right remedy when the server emits the value. Here the server never receives it, so the encoding runs over content that does not contain the input." },
        { id: "b", label: "No — the value never passes through the server, so there is nothing for it to encode", correct: true, explain: "Correct, and saying so explicitly in the report matters: without it a team can reasonably believe they have fixed the issue, close it, and remain exposed. The fix belongs at the sink, in client code." },
        { id: "c", label: "Yes, provided the encoding is applied to every response", explain: "Applying a correct-but-irrelevant control more widely does not make it relevant. No response contains the fragment, however many responses are encoded." },
      ],
    },
    {
      id: "dx-3",
      kind: "prove",
      prompt: "What evidence distinguishes this from reflected cross-site scripting?",
      hints: [
        "Ask what would appear in a request if the flaw were reflected.",
        "Consider which observation rules the server out entirely.",
        "No request carries the value, and the source-to-sink path lives in the page's own script.",
      ],
      options: [
        { id: "a", label: "The value appears in the rendered page", explain: "True of both classes, so it separates nothing. Reflected flaws also end with the value in the page - the difference is the route it took to get there." },
        { id: "b", label: "No request carries the value, and the path from source to sink is in the page's own script", correct: true, explain: "Correct. The absence in the traffic rules out the server, and the quoted path shows where it is actually consumed - which is also what tells the team where the fix belongs." },
        { id: "c", label: "The page was loaded over a URL you typed directly", explain: "How you arrived says nothing about which component interpreted the value. A reflected flaw is equally reachable from a typed URL." },
      ],
    },
  ],
};
