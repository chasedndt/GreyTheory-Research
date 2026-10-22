export const inputHandling = {
  id: "input-handling",
  trackId: "web-api",
  // Claims the sql-injection card. The lesson teaches the general shape first -
  // a value reaching a context that reads it as structure - and its worked
  // example is already a SQL boolean-pair probe, which is the better way to
  // learn it than a lesson that treats SQL as a special case.
  cardId: "sql-injection",
  title: "Input handling",
  level: "Foundation",
  duration: "40 min",
  oneLine: "Injection is not about bad characters. It is about data arriving somewhere that reads it as instructions.",

  concept: [
    "Every injection class shares one shape: a value crosses into a context that interprets some of its characters as structure rather than content. SQL, HTML, shell, LDAP, template engines — different syntax, identical failure.",
    "This is why 'sanitise input' is poor advice. There is no universally safe string. A value harmless in HTML can be catastrophic in a shell, and stripping quotes to protect a query can corrupt legitimate data while missing the real vector.",
    "The reliable fix is separation, not filtering. A parameterised query sends structure and data down different channels, so the database never parses user content as SQL. Where separation is impossible, encoding must match the destination context exactly.",
  ],

  traditional: {
    heading: "Finding the interpreter",
    body: [
      "Trace where a value ends up. A search term might reach a query, a log line, a rendered page, and a downstream API. Each destination has a different interpreter and needs its own treatment, and the interesting bugs live in the destinations nobody enumerated.",
      "Test for interpretation rather than for errors. An error message is a convenience, not a requirement. A value that produces a different response time, a changed row count, or a subtly altered page has been interpreted just as surely as one that throws.",
    ],
  },

  aiNative: {
    heading: "The interpreter that cannot be parameterised",
    body: [
      "A language model is an interpreter with no structural separation between instruction and data. There is no parameterised prompt in the sense there is a parameterised query — the model sees one token stream and infers intent from content.",
      "So the classical fix is unavailable. Control has to move outward: constrain what the model can *do* rather than what it can be told. Injection may still succeed at influencing the text; it must not succeed at causing an action, because actions are gated elsewhere.",
    ],
  },

  workedExample: {
    heading: "One concrete case",
    scenario: "A search field returns results. You want to know whether input reaches a query interpreter.",
    steps: [
      ["Establish a baseline", "Send an ordinary term. Record the status, response time, and result count. Everything is compared against this."],
      ["Send a structurally neutral probe", "A value containing a quote. You are asking whether the parser notices, not trying to extract anything."],
      ["Read the difference", "An error, a changed row count, or a timing shift all indicate interpretation. An identical response suggests the value was treated as data."],
      ["Confirm with a paired logic probe", "Two values differing only in a condition that is true versus false. Diverging responses confirm interpretation without extracting a single record."],
    ],
    lesson: "The finding is complete at 'input reaches the query parser'. Extracting data is escalation, not evidence, and the boolean pair proves the point without touching anyone's records.",
  },

  proofLooksLike: [
    "A baseline response for an ordinary input.",
    "The probe and its response, showing a difference attributable to interpretation.",
    "A true/false logic pair producing divergent responses, demonstrating parsing without extraction.",
    "No extracted data beyond what is needed to show the difference.",
  ],

  checks: [
    {
      id: "ih-1",
      kind: "recognise",
      prompt: "A value is stripped of `<` and `>` then inserted into an HTML attribute. What did the filter miss?",
      hints: [
        "Ask what syntax matters inside an attribute, as opposed to between tags.",
        "Consider how an attribute value ends.",
        "A quote closes the attribute, so a new one can be introduced without any angle bracket.",
      ],
      options: [
        { id: "a", label: "Nothing — without angle brackets no tag can be injected", explain: "No new tag, but none is needed. Inside an attribute the value is already in a context where a quote can terminate it and introduce another attribute, such as an event handler." },
        { id: "b", label: "The quote character, which terminates the attribute", correct: true, explain: "Correct. Breaking out of an attribute needs a matching quote, not an angle bracket. The filter defended a different context from the one the value landed in." },
        { id: "c", label: "Encoded forms of the angle brackets", explain: "Worth checking, but it accepts the framing that angle brackets are the risk. In an attribute context the quote is the delimiter that matters." },
      ],
    },
    {
      id: "ih-2",
      kind: "decide",
      prompt: "You confirm input reaches a SQL parser using a boolean pair. Do you now extract table names to show impact?",
      hints: [
        "Ask what question extraction would answer that the pair has not.",
        "Consider who owns the schema you would be reading.",
        "Capability is proven; extraction is escalation and reads data you have no permission to read.",
      ],
      options: [
        { id: "a", label: "Yes — triagers need concrete impact to rate severity", explain: "Impact follows as an argument from proven query execution. Triagers accept a demonstrated boolean-difference primitive; they do not require you to breach the database to believe it." },
        { id: "b", label: "No — capability is proven, and extraction is escalation", correct: true, explain: "Correct. The boolean pair already demonstrates the parser interprets your input. Schema contents are data you have no authority to read, and the finding stands without them." },
        { id: "c", label: "Yes, but only the database version string", explain: "Still extraction, just smaller. It adds nothing the boolean pair has not established, and it crosses the same line for no evidential gain." },
      ],
    },
    {
      id: "ih-3",
      kind: "prove",
      prompt: "Which result most convincingly shows input is being interpreted rather than merely echoed?",
      hints: [
        "Ask which observation requires the value to have been parsed, not just stored.",
        "Consider what an echo alone could produce.",
        "Two inputs differing only by a true/false condition producing different responses requires evaluation.",
      ],
      options: [
        { id: "a", label: "The application returned a database error message", explain: "Strong evidence when present, but errors are often suppressed in production, and a verbose error can also come from input validation rather than the query parser." },
        { id: "b", label: "Two inputs differing only in a true/false condition returned different results", correct: true, explain: "Correct. Divergence requires the condition to have been evaluated, which means the value was parsed as structure. It also works where errors are suppressed." },
        { id: "c", label: "The input appeared unmodified in the response", explain: "Echoing shows the value survived a round trip, which is about output encoding. It says nothing about whether any interpreter parsed it on the way." },
      ],
    },
  ],
};
