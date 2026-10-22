# Recovered fragments: service.py

Original path: `E:\Projects\GreyTheory\2026-09-01-workbench-read-model-binding\worktree\greytheory_app\service.py`. The whole file was never captured in a transcript, so these are the
recorded edits in time order: each shows the text that was replaced and the text that replaced it.
Append-style logs can usually be reassembled from the 'new text' blocks.

## 1. 2026-09-14T12:16:13.464Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
from greytheory_app.curriculum_section import build_curriculum_section
````

New text:

````
from greytheory_app.campaign_section import build_campaign_section
from greytheory_app.curriculum_section import build_curriculum_section
````

## 2. 2026-09-14T12:16:16.596Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        context = self._context(active, active_journey_id)
        provisional = (
            programmes,
            learning,
            research,
            hypotheses,
            evidence,
            reports,
            approvals,
            capabilities,
            coach,
            curriculum,
        )
````

New text:

````
        campaign = self._safe_section(
            "campaign",
            "Campaign",
            lambda: build_campaign_section(
                self.registry,
                posture=self.posture,
                fixture_receipts=self.fixture_receipts,
            ),
            errors,
        )

        context = self._context(active, active_journey_id)
        provisional = (
            programmes,
            learning,
            research,
            hypotheses,
            evidence,
            reports,
            approvals,
            capabilities,
            coach,
            curriculum,
            campaign,
        )
````

## 3. 2026-09-15T00:14:03.472Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
from greytheory_app.campaign_section import build_campaign_section
from greytheory_app.curriculum_section import build_curriculum_section
````

New text:

````
from greytheory_app.campaign_section import build_campaign_section
from greytheory_app.curriculum_section import build_curriculum_section
from greytheory_app.review_section import build_review_section
````

## 4. 2026-09-15T00:14:06.284Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        context = self._context(active, active_journey_id)
        provisional = (
            programmes,
            learning,
            research,
            hypotheses,
            evidence,
            reports,
            approvals,
            capabilities,
            coach,
            curriculum,
            campaign,
        )
````

New text:

````
        review = self._safe_section(
            "review",
            "Review material",
            lambda: build_review_section(self.registry),
            errors,
        )

        context = self._context(active, active_journey_id)
        provisional = (
            programmes,
            learning,
            research,
            hypotheses,
            evidence,
            reports,
            approvals,
            capabilities,
            coach,
            curriculum,
            campaign,
            review,
        )
````

## 5. 2026-09-15T01:07:26.626Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
            lambda: build_campaign_section(
                self.registry,
                posture=self.posture,
                fixture_receipts=self.fixture_receipts,
            ),
````

New text:

````
            lambda: build_campaign_section(
                self.registry,
                posture=self.posture,
                fixture_receipts=self.fixture_receipts,
                journeys=self.journeys,
                report_store=self.report_store,
                report_drafts=self.report_drafts,
            ),
````

## 6. 2026-09-15T10:01:17.686Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
            elif command.kind is CommandKind.RECORD_MASTERY_ASSESSMENT:
                result = self._record_mastery_assessment(command)
````

New text:

````
            elif command.kind is CommandKind.RECORD_MASTERY_ASSESSMENT:
                result = self._record_mastery_assessment(command)
            elif command.kind is CommandKind.REVIEW_PROGRAMME:
                result = self._review_programme(command)
````

## 7. 2026-09-15T10:01:27.566Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
    def _record_mastery_assessment(
        self, command: WorkbenchCommand
    ) -> CommandResult:
````

New text:

````
    def _review_programme(self, command: WorkbenchCommand) -> CommandResult:
        """Record that a named person read this compiled contract.

        The registry does the refusing, and its reasons are the right ones to
        show: `mark_reviewed` rejects a blocked contract because review
        confirms a clean compile was read, it does not resolve ambiguity. Those
        raise and are turned into an honest refusal by the dispatch, so this
        handler does not second-guess them.
        """

        if self.registry is None:
            raise WorkbenchContractError("no programme registry is configured")
        _require_command_fields(command, required={"programme_id", "reviewer"})

        # Same freshness bounds as a mastery assessment: an approval that sat in
        # a queue must not land long after the person meant it.
        now = self.clock().astimezone(timezone.utc)
        issued = command.issued_at.astimezone(timezone.utc)
        if issued > now + timedelta(seconds=30):
            raise WorkbenchContractError("programme review command is future-dated")
        if now - issued > timedelta(minutes=10):
            raise WorkbenchContractError("programme review command is stale")

        programme_id = _command_text(command, "programme_id") or ""
        reviewer = (_command_text(command, "reviewer") or "").strip()
        if not reviewer:
            raise WorkbenchContractError("a review must name the person who made it")
        # A model may prepare the material; it cannot be the reviewer. Mirrors
        # the same refusal in validation.Attestation.
        if any(
            marker in reviewer.lower()
            for marker in ("model", "llm", "assistant", "claude", "openai", "gpt", "bot")
        ):
            raise WorkbenchContractError(
                "a model may present a contract for review but cannot be its reviewer"
            )

        contract = self.registry.review(programme_id, reviewer=reviewer)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "programme_reviewed",
            (
                f"{programme_id} reviewed by {reviewer}; contract is now "
                f"{contract.status.value} and still capped at {contract.max_authority}"
            ),
            (f"programme:{programme_id}", f"authority:{contract.fingerprint()}"),
        )

    def _record_mastery_assessment(
        self, command: WorkbenchCommand
    ) -> CommandResult:
````

## 8. 2026-09-15T10:06:59.695Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
from greytheory.authority.gate import AuthorityLevel
````

New text:

````
from greytheory.authority.gate import AuthorityLevel
from greytheory.authority.live_authority import _NOT_A_PERSON
````

## 9. 2026-09-15T10:07:03.163Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        reviewer = (_command_text(command, "reviewer") or "").strip()
        if not reviewer:
            raise WorkbenchContractError("a review must name the person who made it")
        # A model may prepare the material; it cannot be the reviewer. Mirrors
        # the same refusal in validation.Attestation.
        if any(
            marker in reviewer.lower()
            for marker in ("model", "llm", "assistant", "claude", "openai", "gpt", "bot")
        ):
````

New text:

````
        # _command_text already strips and refuses a blank value with its own
        # message, so there is no second emptiness check worth writing here.
        reviewer = _command_text(command, "reviewer") or ""
        # A model may prepare a contract for review but cannot be its reviewer.
        # Shared with live_authority rather than copied, so the two lists cannot
        # drift apart.
        if any(marker in reviewer.lower() for marker in _NOT_A_PERSON):
````

## 10. 2026-09-15T15:28:06.879Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
from greytheory_app.review_section import build_review_section
````

New text:

````
from greytheory_app.review_section import build_review_section
from greytheory_app.shortlist_section import build_shortlist_section
````

## 11. 2026-09-15T15:28:08.590Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        registry: ProgrammeRegistry | None = None,
        audit: AuditLog | None = None,
````

New text:

````
        registry: ProgrammeRegistry | None = None,
        shortlist: Any | None = None,
        audit: AuditLog | None = None,
````

## 12. 2026-09-15T15:28:09.943Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        self.registry = registry
        self.audit = audit
````

New text:

````
        self.registry = registry
        self.shortlist = shortlist
        self.audit = audit
````

## 13. 2026-09-15T15:28:12.120Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        review = self._safe_section(
            "review",
            "Review material",
            lambda: build_review_section(self.registry),
            errors,
        )
````

New text:

````
        review = self._safe_section(
            "review",
            "Review material",
            lambda: build_review_section(self.registry),
            errors,
        )

        shortlist = self._safe_section(
            "shortlist",
            "Shortlist",
            lambda: build_shortlist_section(self.shortlist),
            errors,
        )
````

## 14. 2026-09-15T15:28:13.592Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
            curriculum,
            campaign,
            review,
        )
````

New text:

````
            curriculum,
            campaign,
            review,
            shortlist,
        )
````

## 15. 2026-09-15T15:28:16.199Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
            elif command.kind is CommandKind.REVIEW_PROGRAMME:
                result = self._review_programme(command)
````

New text:

````
            elif command.kind is CommandKind.REVIEW_PROGRAMME:
                result = self._review_programme(command)
            elif command.kind is CommandKind.SHORTLIST_PROGRAMME:
                result = self._shortlist_programme(command)
            elif command.kind is CommandKind.ARCHIVE_PROGRAMME:
                result = self._archive_programme(command)
            elif command.kind is CommandKind.RESTORE_PROGRAMME:
                result = self._restore_programme(command)
````

## 16. 2026-09-15T15:28:28.021Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
    def _review_programme(self, command: WorkbenchCommand) -> CommandResult:
````

New text:

````
    def _shortlist_store(self):
        """The store, or a refusal that names what is missing.

        Shared by the three curation handlers so a missing store reads the same
        way whichever one the operator reached for.
        """

        if self.shortlist is None:
            raise WorkbenchContractError("no shortlist store is configured")
        return self.shortlist

    def _shortlist_programme(self, command: WorkbenchCommand) -> CommandResult:
        """Record an intention to work a programme.

        Deliberately does not require the programme to be registered, let alone
        reviewed. Shortlisting is what leads someone to review a programme, so
        demanding the outcome as a precondition of the intent would make the
        front door unreachable.
        """

        store = self._shortlist_store()
        _require_command_fields(command, required={"programme_id"})
        programme_id = _command_text(command, "programme_id") or ""
        entry = store.shortlist(programme_id, actor=command.operator_ref)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "programme_shortlisted",
            f"{programme_id} is on your active list; this records an intention "
            f"and grants no authority",
            (f"shortlist:{programme_id}",),
        )

    def _archive_programme(self, command: WorkbenchCommand) -> CommandResult:
        """Set a programme aside. Reversible, and nothing is deleted."""

        store = self._shortlist_store()
        _require_command_fields(
            command,
            required={"programme_id"},
            optional={"outcome", "note"},
        )
        programme_id = _command_text(command, "programme_id") or ""
        note = _command_text(command, "note", optional=True) or ""
        outcome_name = _command_text(command, "outcome", optional=True) or "unset"
        try:
            outcome = ShortlistOutcome(outcome_name)
        except ValueError as exc:
            permitted = ", ".join(item.value for item in ShortlistOutcome)
            raise WorkbenchContractError(
                f"unknown shortlist outcome {outcome_name!r}; expected one of: {permitted}"
            ) from exc

        entry = store.archive(
            programme_id,
            actor=command.operator_ref,
            outcome=outcome,
            note=note,
            expected_revision=command.expected_revision,
        )
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "programme_archived",
            f"{programme_id} was set aside at revision {entry.revision}; nothing "
            f"was deleted and it can be restored at any time",
            (f"shortlist:{programme_id}",),
        )

    def _restore_programme(self, command: WorkbenchCommand) -> CommandResult:
        """Bring a programme back to the active list."""

        store = self._shortlist_store()
        _require_command_fields(command, required={"programme_id"})
        programme_id = _command_text(command, "programme_id") or ""
        entry = store.restore(
            programme_id,
            actor=command.operator_ref,
            expected_revision=command.expected_revision,
        )
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "programme_restored",
            f"{programme_id} is back on your active list at revision {entry.revision}; "
            f"its earlier reason for being set aside was cleared",
            (f"shortlist:{programme_id}",),
        )

    def _review_programme(self, command: WorkbenchCommand) -> CommandResult:
````

## 17. 2026-09-15T15:28:29.470Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
from greytheory.registry import ProgrammeRegistry
````

New text:

````
from greytheory.registry import ProgrammeRegistry
from greytheory.shortlist import ShortlistOutcome
````

## 18. 2026-09-15T15:29:18.573Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        entry = store.shortlist(programme_id, actor=command.operator_ref)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "programme_shortlisted",
            f"{programme_id} is on your active list; this records an intention "
            f"and grants no authority",
            (f"shortlist:{programme_id}",),
        )
````

New text:

````
        entry = store.shortlist(programme_id, actor=command.operator_ref)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "programme_shortlisted",
            f"{programme_id} is on your active list at revision {entry.revision}; "
            f"this records an intention and grants no authority",
            (f"shortlist:{programme_id}",),
        )
````

## 19. 2026-09-15T21:57:48.940Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
            elif command.kind is CommandKind.SHORTLIST_PROGRAMME:
                result = self._shortlist_programme(command)
````

New text:

````
            elif command.kind is CommandKind.LOOK_UP_PROGRAMME:
                result = self._look_up_programme(command)
            elif command.kind is CommandKind.SHORTLIST_PROGRAMME:
                result = self._shortlist_programme(command)
````

## 20. 2026-09-15T21:57:56.875Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
    def _shortlist_store(self):
````

New text:

````
    def _look_up_programme(self, command: WorkbenchCommand) -> CommandResult:
        """Read what a platform publishes about one named programme.

        The only command in this service that opens an outbound connection. It
        is deliberately narrow: a platform and a handle you already know, read
        anonymously over HTTPS with redirects refused. It cannot enumerate
        programmes, cannot reach a programme's assets, and what comes back is
        PUBLIC and UNTRUSTED source material - not a scope contract, and not
        permission to test anything.
        """

        if self.directory_lookups is None:
            raise WorkbenchContractError("no directory lookup store is configured")
        _require_command_fields(command, required={"platform", "handle"})

        platform = (_command_text(command, "platform") or "").lower()
        handle = (_command_text(command, "handle") or "").lower()
        # Resolved here rather than taken from the command, so a caller cannot
        # name a provider that does not match the platform it claims.
        plan = build_intelligence_plan(f"{platform}-directory", f"{platform}:{handle}")

        # Injected in tests so the suite never reaches a third party; None in
        # the running application, where a real request is the point.
        evidence = fetch_directory(plan, connection_factory=self.directory_connection)
        lookup = self.directory_lookups.record(evidence, actor=command.operator_ref)

        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "programme_looked_up",
            f"Read {lookup.url} - {lookup.body_bytes} bytes, sha256 "
            f"{lookup.body_sha256[:12]}. This is public, untrusted material and "
            f"grants no authority to test {handle}",
            (f"lookup:{lookup.identifier}",),
        )

    def _shortlist_store(self):
````

## 21. 2026-09-15T21:57:59.115Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        registry: ProgrammeRegistry | None = None,
        shortlist: Any | None = None,
````

New text:

````
        registry: ProgrammeRegistry | None = None,
        shortlist: Any | None = None,
        directory_lookups: Any | None = None,
        #: Injected only by tests, so the suite performs no network I/O.
        directory_connection: Any | None = None,
````

## 22. 2026-09-15T21:58:00.707Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        self.registry = registry
        self.shortlist = shortlist
````

New text:

````
        self.registry = registry
        self.shortlist = shortlist
        self.directory_lookups = directory_lookups
        self.directory_connection = directory_connection
````

## 23. 2026-09-15T21:58:02.406Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
from greytheory.shortlist import ShortlistOutcome
````

New text:

````
from greytheory.shortlist import ShortlistOutcome
from greytheory_intelligence.directory_fetcher import fetch_directory
from greytheory_intelligence.registry import build_intelligence_plan
````

## 24. 2026-09-15T22:00:40.399Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
from greytheory_app.shortlist_section import build_shortlist_section
````

New text:

````
from greytheory_app.directory_section import build_directory_section
from greytheory_app.shortlist_section import build_shortlist_section
````

## 25. 2026-09-15T22:00:42.718Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        shortlist = self._safe_section(
            "shortlist",
            "Shortlist",
            lambda: build_shortlist_section(self.shortlist),
            errors,
        )
````

New text:

````
        shortlist = self._safe_section(
            "shortlist",
            "Shortlist",
            lambda: build_shortlist_section(self.shortlist),
            errors,
        )

        directory = self._safe_section(
            "directory",
            "Directory lookups",
            lambda: build_directory_section(self.directory_lookups),
            errors,
        )
````

## 26. 2026-09-15T22:00:43.962Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
            review,
            shortlist,
        )
````

New text:

````
            review,
            shortlist,
            directory,
        )
````
