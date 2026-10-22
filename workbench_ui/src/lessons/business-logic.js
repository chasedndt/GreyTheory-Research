export const businessLogic = {
  id: "business-logic",
  trackId: "web-api",
  cardId: "business-logic-authorization",
  title: "Business logic",
  level: "Applied",
  duration: "55 min",
  oneLine: "Every request is valid. The sequence is not. No scanner will ever find this for you.",

  concept: [
    "Business logic flaws are the ones where nothing is malformed. Each request is well-formed, correctly authenticated, and individually permitted. The vulnerability is in the order, the timing, the quantity, or the state the application assumed but never enforced.",
    "This is the class automated tooling cannot reach, because a scanner has no model of what the application is *for*. It cannot know that a refund should not exceed the payment, that a discount should apply once, or that approval must precede fulfilment. Those are domain facts, and finding them requires understanding the domain.",
    "Which makes this the highest-value skill in the track. The reflected XSS was found by a scanner an hour after deployment. The flaw letting someone apply a discount twice by racing two requests has been there for two years.",
  ],

  traditional: {
    heading: "Where sequence assumptions hide",
    body: [
      "Look for multi-step flows and ask what the application assumes about order. Can you skip step two? Repeat step three? Return to a completed step and change a value the later steps already consumed? Each is a state-machine question the code may never have asked.",
      "Race conditions are the timing form. If a balance is checked and then debited as two operations, two simultaneous requests may both pass the check. The classic test is concurrent identical requests against an operation that should be idempotent or singly-applicable.",
    ],
  },

  aiNative: {
    heading: "Agents as a sequence attack surface",
    body: [
      "An agent executing a multi-step workflow holds intermediate state in context rather than in a server-side state machine. If an attacker can influence that context between steps, they can alter a decision the workflow already made without ever touching the server's record of it.",
      "Agents also retry. A workflow interrupted and resumed may repeat a step that should occur once, and the model has no notion of which side effects already happened. Idempotency has to be enforced server-side, because the agent will happily do it twice.",
    ],
  },

  workedExample: {
    heading: "One concrete case",
    scenario: "Checkout: apply discount, confirm order, capture payment. A discount code is single use.",
    steps: [
      ["Map the state machine", "Draw the intended sequence and note what each step assumes has already happened."],
      ["Ask what enforces single use", "Is the code marked consumed at application time, or at payment capture? The gap between them is the window."],
      ["Test the sequence", "Apply the discount, begin checkout, then apply it again before capture. One request at a time — this is a sequence test, not yet a race."],
      ["Test concurrency separately", "Two simultaneous applications. If consumption is check-then-mark without atomicity, both succeed."],
    ],
    lesson: "Sequence and concurrency are distinct flaws with distinct fixes — a state check versus an atomic operation — and testing them separately keeps the findings attributable.",
  },

  proofLooksLike: [
    "The intended flow documented, with the assumption that was violated named explicitly.",
    "The exact request sequence, in order, with timings where concurrency matters.",
    "Evidence the end state is inconsistent — a discount applied twice, a balance below zero.",
    "A control run of the correct sequence, showing the normal path behaves properly.",
  ],

  checks: [
    {
      id: "bl-1",
      kind: "recognise",
      prompt: "A refund endpoint validates that the amount is positive and the order exists, then refunds. Both checks pass. What might still be wrong?",
      hints: [
        "Ask what the checks compare the amount against.",
        "Consider whether refunding twice would be caught.",
        "Nothing bounds the refund by what was paid, or by what has already been refunded.",
      ],
      options: [
        { id: "a", label: "Nothing — the inputs are validated correctly", explain: "The inputs are individually valid, which is exactly what makes this a logic flaw. Validation checked the shape of the request, not its relationship to the order's history." },
        { id: "b", label: "Nothing bounds the refund by the amount paid or already refunded", correct: true, explain: "Correct. A positive amount against an existing order can still exceed the payment, or be issued repeatedly. The missing check is a domain rule, not an input rule." },
        { id: "c", label: "The endpoint should require admin privileges", explain: "That would be an access control question. Here the flaw persists even for a legitimately authorised caller refunding their own order, which is what makes it logic." },
      ],
    },
    {
      id: "bl-2",
      kind: "decide",
      prompt: "A single-use code is validated, then marked consumed in a separate later step. Two concurrent requests both succeed. What is the missing condition?",
      hints: [
        "Ask what happens between the check and the mark.",
        "Consider whether either request did anything individually wrong.",
        "The check and the mark are not atomic, so both requests observe an unconsumed code.",
      ],
      options: [
        { id: "a", label: "Rate limiting on the endpoint", explain: "Rate limiting narrows the window and makes exploitation noisier, but two requests within it still both succeed. The underlying non-atomicity is untouched." },
        { id: "b", label: "Atomicity: the check and the mark must be one indivisible operation", correct: true, explain: "Correct. Between check and mark the code is still unconsumed, so both requests pass legitimately. A conditional update or a lock closes the window; nothing else does." },
        { id: "c", label: "Better validation of the code format", explain: "The code is valid and correctly formatted. Format validation has no bearing on whether it can be consumed twice." },
      ],
    },
    {
      id: "bl-3",
      kind: "prove",
      prompt: "What demonstrates a business logic flaw to someone who knows the system better than you do?",
      hints: [
        "Ask what a developer would say if you showed only the requests.",
        "Which evidence shows the system reached a state it should not hold?",
        "The intended rule, plus an end state that violates it, plus a control of the correct path.",
      ],
      options: [
        { id: "a", label: "The full sequence of requests you sent", explain: "A developer will ask what is wrong with it — every request was valid. Without naming the violated rule, the sequence looks like ordinary usage." },
        { id: "b", label: "The intended rule, an end state violating it, and a control of the correct path", correct: true, explain: "Correct. Naming the rule makes the violation legible, the end state proves it occurred, and the control shows the normal path holds — so the difference is the flaw." },
        { id: "c", label: "A severity rating explaining the financial impact", explain: "Impact matters for prioritisation but presumes the flaw is accepted. A developer who does not yet see what rule was broken will not get as far as the rating." },
      ],
    },
  ],
};
