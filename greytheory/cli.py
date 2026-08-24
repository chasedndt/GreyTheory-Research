"""Command line surface for the GreyTheory trust kernel.

Deliberately small. It exposes programme compilation and review, source-bundle
registration, gate checks, audit verification, and offline read models without
turning the command line into an execution bypass.

    greytheory compile fixtures/programmes/mock-verified.json -o build/contract.json
    greytheory review build/contract.json --reviewer chase
    greytheory check build/contract.json --asset app.mock-verified.test --level LOCAL_FIXTURE
    greytheory audit-verify audit.jsonl
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from greytheory.audit import AuditLog, AuditVerificationError
from greytheory.authority.compiler import compile_contract, mark_reviewed
from greytheory.authority.gate import AccessRequest, AuthorityLevel, Gate
from greytheory.authority.scope import ScopeContract
from greytheory.learning.domain import MasteryDimension
from greytheory.registry import ProgrammeRegistry, RegistrationResult, RegistryError

DEFAULT_AUDIT = "audit.jsonl"
DEFAULT_REGISTRY = "contracts"


def _load(path: str) -> tuple[dict, str]:
    raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw), raw


def cmd_compile(args: argparse.Namespace) -> int:
    programme, raw = _load(args.programme)
    result = compile_contract(programme, raw_source=raw)
    contract = result.contract

    audit = AuditLog(args.audit)
    audit.append(
        actor=args.actor,
        action="contract.compile",
        detail={
            "programme": args.programme,
            "status": contract.status.value,
            "ambiguities": contract.ambiguities,
            "fingerprint": contract.fingerprint(),
        },
    )

    print(f"contract:    {contract.id}")
    print(f"programme:   {contract.programme_id}")
    print(f"status:      {contract.status.value.upper()}")
    print(f"fingerprint: {contract.fingerprint()[:16]}...")
    print(f"granted:     {contract.max_authority}")
    if contract.ambiguities:
        print(f"\nBLOCKED by {len(contract.ambiguities)} ambiguity/ies:")
        for item in contract.ambiguities:
            print(f"  - {item}")
        print("\nResolve these in the programme source and recompile.")
    else:
        print("\nCompiled clean. Status is PENDING_REVIEW - it grants nothing until")
        print("a human reviews it:  greytheory review <contract> --reviewer <name>")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(contract.to_dict(), indent=2), encoding="utf-8"
        )
        print(f"\nwritten: {args.out}")

    return 1 if result.blocked else 0


def cmd_review(args: argparse.Namespace) -> int:
    data, _ = _load(args.contract)
    contract = ScopeContract.from_dict(data)
    try:
        mark_reviewed(contract, reviewer=args.reviewer)
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    AuditLog(args.audit).append(
        actor=args.reviewer,
        action="contract.review",
        authority_ref=contract.fingerprint(),
        detail={"contract_id": contract.id, "status": contract.status.value},
    )
    Path(args.contract).write_text(
        json.dumps(contract.to_dict(), indent=2), encoding="utf-8"
    )
    print(f"{contract.id} reviewed by {args.reviewer} -> VERIFIED")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    data, _ = _load(args.contract)
    contract = ScopeContract.from_dict(data)
    gate = Gate(
        AuditLog(args.audit),
        posture_ceiling=AuthorityLevel.parse(args.posture),
    )
    decision = gate.evaluate(
        contract,
        AccessRequest(
            asset=args.asset,
            authority_level=AuthorityLevel.parse(args.level),
            actor=args.actor,
            technique=args.technique,
            derived_from=args.derived_from,
            purpose=args.purpose,
        ),
    )
    verdict = "ALLOW" if decision.allowed else "DENY"
    print(f"{verdict}  {args.asset}  [{decision.reason.value}]")
    print(f"  {decision.detail}")
    print(f"  authority_ref: {(decision.authority_ref or '-')[:16]}...")
    print(f"  audit seq:     {decision.audit_seq}")
    return 0 if decision.allowed else 2


def cmd_audit_verify(args: argparse.Namespace) -> int:
    log = AuditLog(args.audit)
    count = len(log.records())
    try:
        log.verify()
    except AuditVerificationError as exc:
        print(f"AUDIT CHAIN BROKEN: {exc}", file=sys.stderr)
        return 1
    print(f"audit chain intact - {count} record(s) verified")
    return 0


def cmd_programme_register(args: argparse.Namespace) -> int:
    programme, raw = _load(args.programme)
    registry = ProgrammeRegistry(args.registry, audit=AuditLog(args.audit))
    try:
        result = registry.register(programme, raw_source=raw)
    except RegistryError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    return _print_registration(result)


def cmd_programme_register_bundle(args: argparse.Namespace) -> int:
    registry = ProgrammeRegistry(args.registry, audit=AuditLog(args.audit))
    try:
        result = registry.register_bundle(args.bundle)
    except RegistryError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return _print_registration(result)


def _print_registration(result: RegistrationResult) -> int:
    contract = result.version.contract
    print(f"programme:   {contract.programme_id}")
    print(f"version:     v{result.version.version}")
    print(f"status:      {contract.status.value.upper()}")
    print(f"granted:     {contract.max_authority}")

    if result.blocked:
        print(f"\nBLOCKED by {len(contract.ambiguities)} ambiguity/ies:")
        for item in contract.ambiguities:
            print(f"  - {item}")

    if result.diff and result.diff.changed:
        label = "NARROWED" if result.diff.is_narrowing else "changed"
        print(f"\nScope {label} since the previous version:")
        for line in result.diff.summary():
            print(f"  - {line}")
        if result.diff.is_narrowing:
            print("\n  Permission shrank. Review any work already done against")
            print("  assets that are no longer authorised.")

    if result.source_changed:
        print("\nThe programme text changed, so the previous review no longer applies.")
    if result.requires_review and not result.blocked:
        print("Awaiting review:  greytheory programme review "
              f"{contract.programme_id} --reviewer <name>")

    return 1 if result.blocked else 0


def cmd_programme_review(args: argparse.Namespace) -> int:
    registry = ProgrammeRegistry(args.registry, audit=AuditLog(args.audit))
    try:
        contract = registry.review(args.programme_id, reviewer=args.reviewer)
    except (RegistryError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    print(f"{contract.programme_id} reviewed by {args.reviewer} -> VERIFIED")
    return 0


def cmd_programme_status(args: argparse.Namespace) -> int:
    registry = ProgrammeRegistry(args.registry)
    programmes = registry.programmes()
    if not programmes:
        print(f"no programmes registered in {args.registry}")
        return 0

    attention = {item.programme_id: item for item in registry.needs_attention()}
    for programme_id in programmes:
        version = registry.latest(programme_id)
        item = attention.get(programme_id)
        marker = "!" if item else " "
        print(
            f"{marker} {programme_id:<24} v{version.version:<3} "
            f"{version.contract.status.value.upper():<15} "
            f"{version.contract.max_authority}"
        )
        if item:
            print(f"    {item.reason}: {item.detail}")

    print(f"\n{len(attention)} of {len(programmes)} need attention.")
    return 2 if attention else 0


def cmd_programme_diff(args: argparse.Namespace) -> int:
    registry = ProgrammeRegistry(args.registry)
    try:
        diff = registry.diff_versions(args.programme_id, args.a, args.b)
    except RegistryError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    if not diff.changed:
        print(f"v{args.a} -> v{args.b}: no substantive change")
        return 0
    label = "NARROWED" if diff.is_narrowing else "changed"
    print(f"v{args.a} -> v{args.b}: {label}")
    for line in diff.summary():
        print(f"  - {line}")
    return 0


def cmd_advisories_import(args: argparse.Namespace) -> int:
    from greytheory.advisories import AdvisorySet

    try:
        advisories = AdvisorySet.load(args.source)
    except (OSError, ValueError) as exc:
        print(f"could not read {args.source}: {exc}", file=sys.stderr)
        return 1

    if not len(advisories):
        print(f"no usable advisories found in {args.source}", file=sys.stderr)
        print("Records with no version range are skipped: an advisory with", file=sys.stderr)
        print("unknown bounds would match every version.", file=sys.stderr)
        return 1

    advisories.write(args.out)
    print(f"imported {len(advisories)} advisory range(s) -> {args.out}")
    print(f"ecosystems: {', '.join(sorted(advisories.ecosystems()))}")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    from pathlib import Path as _Path

    from greytheory.dashboard import (
        build_dashboard,
        render_html,
        render_json,
        render_text,
    )
    from greytheory.evidence import EvidenceVault
    from greytheory.ledger import Ledger

    registry = ledger = vault = audit = None

    if _Path(args.registry).is_dir():
        registry = ProgrammeRegistry(args.registry)
    if _Path(args.audit).is_file():
        audit = AuditLog(args.audit)
    # Absence stays absence. A missing store must read as "unknown" on the
    # dashboard, never as a reassuring zero, so nothing is created here.
    try:
        ledger = Ledger(args.ledger) if args.ledger else None
    except Exception as exc:  # noqa: BLE001 - report, do not fabricate
        print(f"ledger unavailable: {exc}", file=sys.stderr)
    try:
        vault = EvidenceVault(args.evidence) if args.evidence else None
    except Exception as exc:  # noqa: BLE001
        print(f"evidence vault unavailable: {exc}", file=sys.stderr)

    dashboard = build_dashboard(
        registry=registry,
        audit=audit,
        vault=vault,
        ledger=ledger,
        posture_ceiling=AuthorityLevel.parse(args.posture),
        currency=args.currency,
    )

    if args.html:
        _Path(args.html).parent.mkdir(parents=True, exist_ok=True)
        _Path(args.html).write_text(render_html(dashboard), encoding="utf-8")
        print(f"written: {args.html}")
        return 0
    if args.json:
        print(render_json(dashboard))
        return 0
    print(render_text(dashboard))
    return 0


def cmd_demo_local_two_account(args: argparse.Namespace) -> int:
    from greytheory.vertical_slice import (
        DEFAULT_PROGRAMME,
        OperatorStatements,
        VerticalSliceError,
        run_local_two_account_slice,
    )

    try:
        statements, _ = _load(args.attestations)
        programme, _ = _load(DEFAULT_PROGRAMME)
        fixture_time = datetime.fromisoformat(str(programme["verified_at"]))
        result = run_local_two_account_slice(
            args.root,
            statements=OperatorStatements.from_dict(statements),
            # The bundled demonstration is a historical synthetic proof, not
            # live authority. Freeze its clock to its declared fixture time so
            # the reproducible demo remains runnable while real contracts still
            # fail closed when stale.
            clock=lambda: fixture_time,
        )
    except (OSError, ValueError, VerticalSliceError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("GreyTheory local two-account slice: COMPLETE")
        print(f"  posture:       {result.operating_posture}")
        print(f"  finding:       {result.finding_id} ({result.finding_state})")
        print(f"  check receipt: {result.check_receipt_id}")
        print(f"  report:        {result.report_path}")
        print("  submission:    not performed")
    return 0


def cmd_learning_catalogue(args: argparse.Namespace) -> int:
    from greytheory.learning import LearningError, load_builtin_catalogue

    try:
        catalogue = load_builtin_catalogue()
        payload = (
            catalogue.card(args.card).to_dict()
            if args.card
            else {
                "catalogue_digest": catalogue.digest(),
                "card_count": len(catalogue.card_ids),
                "cards": [catalogue.card(item).to_dict() for item in catalogue.card_ids],
                "skill_graph": catalogue.graph.to_dict(),
            }
        )
    except LearningError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2))
    elif args.card:
        print(f"{payload['name']} ({payload['id']} v{payload['version']})")
        print(f"  fixture: {payload['local_fixture']['id']}")
        print(f"  review:  {payload['review_date']}")
    else:
        print(f"GreyTheory vulnerability catalogue: {payload['card_count']} cards")
        print(f"  digest: {payload['catalogue_digest']}")
        for card in payload["cards"]:
            print(f"  - {card['id']}: {card['name']}")
    return 0


def cmd_learning_verify(args: argparse.Namespace) -> int:
    from greytheory.learning import LearningError, load_builtin_catalogue

    try:
        catalogue = load_builtin_catalogue()
        receipts = catalogue.run_all_fixtures()
    except LearningError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    payload = {
        "status": "complete",
        "operating_posture": "LOCAL_FIXTURE",
        "catalogue_digest": catalogue.digest(),
        "card_count": len(catalogue.card_ids),
        "fixture_count": len(receipts),
        "controls_passed": all(item.controls_passed for item in receipts),
        "vulnerable_cases_demonstrated": all(
            item.vulnerable_case_demonstrated for item in receipts
        ),
        "real_vulnerabilities_proven": 0,
        "mastery_credits_awarded": 0,
        "network_actions": 0,
        "receipts": [item.to_dict() for item in receipts],
    }
    if not payload["controls_passed"] or not payload["vulnerable_cases_demonstrated"]:
        payload["status"] = "failed"
    if args.out:
        output_path = Path(args.out).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"GreyTheory Milestone 5 fixture verification: {payload['status'].upper()}")
        print(f"  cards/fixtures: {payload['card_count']}/{payload['fixture_count']}")
        print(f"  posture:        {payload['operating_posture']}")
        print("  real findings:  none")
        print("  mastery credit: none")
        if args.out:
            print(f"  written:        {output_path}")
    return 0 if payload["status"] == "complete" else 1


def cmd_learning_status(args: argparse.Namespace) -> int:
    from greytheory.learning import (
        LearningError,
        MasteryStore,
        load_builtin_catalogue,
    )

    try:
        catalogue = load_builtin_catalogue()
        store = MasteryStore(args.root, catalogue=catalogue)
        assessments = store.assessments()
        credited = catalogue.graph.mastery_states(assessments)
        all_states = catalogue.graph.mastery_states(
            assessments, include_non_crediting=True
        )
    except (OSError, LearningError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    payload = {
        "catalogue_digest": catalogue.digest(),
        "assessment_count": len(assessments),
        "credited_assessment_count": sum(item.credits_mastery for item in assessments),
        "non_crediting_assessment_count": sum(
            not item.credits_mastery for item in assessments
        ),
        "mastery": [item.to_dict() for item in credited],
        "all_recorded_states": [item.to_dict() for item in all_states],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        assessed = sum(item["level"] != "not_assessed" for item in payload["mastery"])
        total = len(payload["mastery"])
        print(f"GreyTheory mastery status: {assessed}/{total} dimensions assessed")
        print(f"  evidence-bound human records: {payload['credited_assessment_count']}")
        print(f"  non-crediting fixture records: {payload['non_crediting_assessment_count']}")
    return 0


def cmd_learning_assess(args: argparse.Namespace) -> int:
    from greytheory.learning import (
        AssessorKind,
        LearningError,
        MasteryAssessment,
        MasteryDimension,
        MasteryLevel,
        MasteryStore,
        load_builtin_catalogue,
        resolve_learning_root,
    )

    try:
        catalogue = load_builtin_catalogue()
        root = resolve_learning_root(args.root)
        assessment = MasteryAssessment(
            id=args.assessment_id,
            card_id=args.card,
            dimension=MasteryDimension(args.dimension),
            level=MasteryLevel.parse(args.level),
            assessor=args.assessor,
            assessor_kind=AssessorKind(args.assessor_kind),
            evidence_refs=tuple(args.evidence_ref),
            rationale=args.rationale,
            assessed_at=(
                datetime.fromisoformat(args.assessed_at)
                if args.assessed_at
                else datetime.now(timezone.utc)
            ),
            review_due=date.fromisoformat(args.review_due),
        )
        store = MasteryStore(root, catalogue=catalogue)
        store.audit = AuditLog(root / "audit.jsonl")
        store.record(assessment)
        store.verify()
    except (OSError, LearningError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    payload = assessment.to_dict()
    payload["credits_mastery"] = assessment.credits_mastery
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"recorded: {assessment.id}")
        print(f"  card/dimension: {assessment.card_id}/{assessment.dimension.value}")
        print(f"  level:          {assessment.level.name.lower()}")
        print(f"  credits mastery: {'yes' if assessment.credits_mastery else 'no'}")
    return 0


def cmd_learning_plan(args: argparse.Namespace) -> int:
    from greytheory.learning import (
        GuidedLearningPlanner,
        LearningError,
        MasteryDimension,
        MasteryStore,
        ReviewPolicy,
        load_builtin_catalogue,
    )

    try:
        catalogue = load_builtin_catalogue()
        store = MasteryStore(args.root, catalogue=catalogue)
        assessments = store.assessments()
        recommendation = GuidedLearningPlanner(catalogue).recommend(
            assessments,
            today=date.fromisoformat(args.today) if args.today else date.today(),
            preferred_card_id=args.card,
            preferred_dimension=(
                MasteryDimension(args.dimension) if args.dimension else None
            ),
        )
    except (OSError, LearningError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    payload = {
        "catalogue_digest": catalogue.digest(),
        "assessment_count": len(assessments),
        "review_policy_days": ReviewPolicy().to_dict(),
        "recommendation": recommendation.to_dict(),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        item = payload["recommendation"]
        print(f"GreyTheory learning plan: {item['card_name']}")
        print(f"  focus:   {item['card_id']}/{item['dimension']}")
        print(f"  mode:    {item['mode']}")
        print(f"  reason:  {item['reason']}")
        print("  posture: LOCAL_FIXTURE")
    return 0


def cmd_learning_journey_start(args: argparse.Namespace) -> int:
    from greytheory.learning import (
        GuidedLearningPlanner,
        LearningError,
        LearningJourneyStore,
        MasteryDimension,
        MasteryStore,
        load_builtin_catalogue,
        resolve_learning_root,
        start_learning_journey,
    )

    try:
        catalogue = load_builtin_catalogue()
        root = resolve_learning_root(args.root)
        mastery = MasteryStore(root, catalogue=catalogue)
        recommendation = GuidedLearningPlanner(catalogue).recommend(
            mastery.assessments(),
            today=date.fromisoformat(args.today) if args.today else date.today(),
            preferred_card_id=args.card,
            preferred_dimension=(
                MasteryDimension(args.dimension) if args.dimension else None
            ),
        )
        started_at = (
            datetime.fromisoformat(args.at)
            if args.at
            else datetime.now(timezone.utc)
        )
        journey = start_learning_journey(
            recommendation,
            journey_id=args.journey_id,
            now=started_at,
            objective=args.objective,
        )
        journeys = LearningJourneyStore(
            root,
            catalogue=catalogue,
            audit=AuditLog(root / "audit.jsonl"),
        )
        journeys.save(journey)
        journeys.verify()
    except (OSError, LearningError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    payload = {
        "journey": journey.to_dict(),
        "recommendation": recommendation.to_dict(),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"started: {journey.id}")
        print(f"  card/dimension: {journey.card_id}/{journey.dimension.value}")
        print(f"  stage:          {journey.current_stage.value}")
        print("  mastery credit: none")
    return 0


def cmd_learning_journey_status(args: argparse.Namespace) -> int:
    from greytheory.learning import (
        LearningError,
        LearningJourneyStore,
        load_builtin_catalogue,
    )

    try:
        catalogue = load_builtin_catalogue()
        store = LearningJourneyStore(args.root, catalogue=catalogue)
        journeys = (
            (store.get(args.journey_id),)
            if args.journey_id
            else store.journeys()
        )
        store.verify()
    except (OSError, LearningError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    payload = {
        "catalogue_digest": catalogue.digest(),
        "journey_count": len(journeys),
        "journeys": [item.to_dict() for item in journeys],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"GreyTheory learning journeys: {len(journeys)}")
        for item in journeys:
            print(
                f"  - {item.id}: {item.card_id}/{item.dimension.value} "
                f"{item.status.value} at {item.current_stage.value} r{item.revision}"
            )
    return 0


def cmd_learning_journey_advance(args: argparse.Namespace) -> int:
    from greytheory.learning import (
        LearningError,
        LearningJourneyStore,
        MasteryStore,
        advance_learning_journey,
        load_builtin_catalogue,
        resolve_learning_root,
    )

    try:
        catalogue = load_builtin_catalogue()
        root = resolve_learning_root(args.root)
        journeys = LearningJourneyStore(
            root,
            catalogue=catalogue,
            audit=AuditLog(root / "audit.jsonl"),
        )
        mastery = MasteryStore(root, catalogue=catalogue)
        current = journeys.get(args.journey_id)
        assessments = mastery.assessments()
        selected = next(
            (item for item in assessments if item.id == args.assessment_id), None
        )
        if args.assessment_id and selected is None:
            raise LearningError(
                f"unknown persisted mastery assessment {args.assessment_id!r}"
            )
        updated = advance_learning_journey(
            current,
            at=(
                datetime.fromisoformat(args.at)
                if args.at
                else datetime.now(timezone.utc)
            ),
            fixture_receipt_ref=args.fixture_receipt_ref,
            evidence_refs=tuple(args.evidence_ref or ()),
            reflection=args.reflection,
            assessment=selected,
            recorded_assessment_ids=tuple(item.id for item in assessments),
        )
        journeys.save(updated, expected_revision=current.revision)
        journeys.verify()
    except (OSError, LearningError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(updated.to_dict(), indent=2))
    else:
        print(f"advanced: {updated.id}")
        print(f"  stage:    {updated.current_stage.value}")
        print(f"  status:   {updated.status.value}")
        print(f"  revision: {updated.revision}")
    return 0


def cmd_learning_journey_abandon(args: argparse.Namespace) -> int:
    from greytheory.learning import (
        LearningError,
        LearningJourneyStore,
        abandon_learning_journey,
        load_builtin_catalogue,
        resolve_learning_root,
    )

    try:
        catalogue = load_builtin_catalogue()
        root = resolve_learning_root(args.root)
        store = LearningJourneyStore(
            root,
            catalogue=catalogue,
            audit=AuditLog(root / "audit.jsonl"),
        )
        current = store.get(args.journey_id)
        updated = abandon_learning_journey(
            current,
            at=(
                datetime.fromisoformat(args.at)
                if args.at
                else datetime.now(timezone.utc)
            ),
            reason=args.reason,
        )
        store.save(updated, expected_revision=current.revision)
        store.verify()
    except (OSError, LearningError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(updated.to_dict(), indent=2))
    else:
        print(f"abandoned: {updated.id}")
        print(f"  stage:  {updated.current_stage.value}")
        print("  mastery credit: none")
    return 0


def cmd_hypothesis_verify(args: argparse.Namespace) -> int:
    from greytheory.hypothesis import (
        HypothesisRankingError,
        run_local_ranking_fixture,
        write_ranking_payload,
    )

    try:
        payload = run_local_ranking_fixture()
        output_path = write_ranking_payload(args.out, payload) if args.out else None
    except (OSError, HypothesisRankingError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("GreyTheory Milestone 6 hypothesis ranking: COMPLETE")
        print(f"  ranked theories: {payload['ranked_hypotheses']}")
        print("  factor explanations: nine per item")
        print("  claim state: unproven")
        print("  execution: not requested")
        print("  network/model calls: none")
        if output_path is not None:
            print(f"  written: {output_path}")
    return 0


def cmd_hypothesis_rank(args: argparse.Namespace) -> int:
    from greytheory.hypothesis import (
        HypothesisRanker,
        HypothesisRankingError,
        parse_ranking_inputs,
        write_research_queue,
    )
    from greytheory.learning import load_builtin_catalogue
    from greytheory.research import ResearchStore, ResearchStoreError

    try:
        contract_data, _ = _load(args.contract)
        contract = ScopeContract.from_dict(contract_data)
        ranking_data, _ = _load(args.assessments)
        ranking_inputs = parse_ranking_inputs(ranking_data)
        as_of = (
            datetime.fromisoformat(args.as_of)
            if args.as_of
            else datetime.now(timezone.utc)
        )
        store = ResearchStore(args.root)
        snapshot = store.snapshot(args.workspace)
        queue = HypothesisRanker(clock=lambda: as_of).rank(
            snapshot=snapshot,
            contract=contract,
            ranking_inputs=ranking_inputs,
            catalogue=load_builtin_catalogue(),
        )
        AuditLog(store.root / "ranking-audit.jsonl").append(
            actor=args.actor,
            action="hypothesis.queue.rank",
            authority_ref=queue.contract_fingerprint,
            detail={
                "queue_id": queue.id,
                "queue_digest": queue.queue_digest,
                "workspace_id": queue.workspace_id,
                "item_count": len(queue.items),
                "decision_support_only": True,
                "execution_requests_created": 0,
                "action_receipts_created": 0,
            },
        )
        output_path = write_research_queue(args.out, queue) if args.out else None
    except (
        OSError,
        ValueError,
        HypothesisRankingError,
        ResearchStoreError,
    ) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1

    payload = queue.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"GreyTheory research queue: {len(queue.items)} unproven hypotheses")
        print(f"  policy: {queue.policy.id} v{queue.policy.version}")
        print(f"  digest: {queue.queue_digest}")
        for item in queue.items:
            print(
                f"  {item.rank}. {item.hypothesis_id} - {item.score_bps}/10000 "
                f"[{item.queue_partition.value}]"
            )
        print("  execution: not requested")
        if output_path is not None:
            print(f"  written: {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greytheory",
        description=(
            "GreyTheory - local-first Security Research Operating System. "
            "No authorisation, no execution."
        ),
    )
    parser.add_argument("--audit", default=DEFAULT_AUDIT, help="audit log path")
    parser.add_argument("--actor", default="operator", help="who is acting")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("compile", help="compile a programme record into a contract")
    p.add_argument("programme")
    p.add_argument("-o", "--out", help="write the compiled contract here")
    p.set_defaults(func=cmd_compile)

    p = sub.add_parser("review", help="human-review a clean contract into VERIFIED")
    p.add_argument("contract")
    p.add_argument("--reviewer", required=True)
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("check", help="ask the gate whether an action is permitted")
    p.add_argument("contract")
    p.add_argument("--asset", required=True)
    p.add_argument("--level", default="LOCAL_FIXTURE")
    p.add_argument("--technique")
    p.add_argument("--derived-from")
    p.add_argument("--purpose", default="")
    p.add_argument(
        "--posture",
        default="LOCAL_FIXTURE",
        help="system-wide authority ceiling (current posture is LOCAL_FIXTURE)",
    )
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("audit-verify", help="verify the audit hash chain")
    p.set_defaults(func=cmd_audit_verify)

    p = sub.add_parser(
        "advisories", help="import advisory data offline (OSV or native format)"
    )
    p.add_argument("source", help="a JSON file or a directory of them")
    p.add_argument("-o", "--out", default="advisories.json")
    p.set_defaults(func=cmd_advisories_import)

    p = sub.add_parser("dashboard", help="operator dashboard")
    p.add_argument("--registry", default=DEFAULT_REGISTRY)
    p.add_argument("--ledger", help="ledger root (omit to report as unknown)")
    p.add_argument("--evidence", help="evidence root (omit to report as unknown)")
    p.add_argument("--posture", default="LOCAL_FIXTURE")
    p.add_argument("--currency", default="GBP")
    p.add_argument("--html", help="write a self-contained HTML page here")
    p.add_argument("--json", action="store_true", help="emit the read model as JSON")
    p.set_defaults(func=cmd_dashboard)

    demo = sub.add_parser(
        "demo", help="run bounded local demonstrations (never a network target)"
    )
    dsub = demo.add_subparsers(dest="demo_command", required=True)
    q = dsub.add_parser(
        "local-two-account",
        help="run the complete LOCAL_FIXTURE authorization research slice",
    )
    q.add_argument("--root", required=True, help="new private run directory outside Git")
    q.add_argument(
        "--attestations",
        required=True,
        help="explicit operator review/attestation JSON (may be labelled test_fixture)",
    )
    q.add_argument("--json", action="store_true", help="emit the result as JSON")
    q.set_defaults(func=cmd_demo_local_two_account)

    learning = sub.add_parser(
        "learning", help="offline vulnerability cards, fixtures, and mastery state"
    )
    lsub = learning.add_subparsers(dest="learning_command", required=True)

    q = lsub.add_parser("catalogue", help="inspect the built-in card catalogue")
    q.add_argument("--card", help="show one card by id")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_catalogue)

    q = lsub.add_parser(
        "verify", help="run all synthetic, network-free local card fixtures"
    )
    q.add_argument("--out", help="write the structured fixture receipts to JSON")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_verify)

    q = lsub.add_parser("status", help="show six-dimensional mastery state")
    q.add_argument("--root", help="private mastery-state directory outside Git")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_status)

    q = lsub.add_parser(
        "assess", help="record one explicit evidence-bound mastery assessment"
    )
    q.add_argument("--root", help="private mastery-state directory outside Git")
    q.add_argument("--assessment-id", required=True)
    q.add_argument("--card", required=True)
    q.add_argument(
        "--dimension", required=True, choices=[item.value for item in MasteryDimension]
    )
    q.add_argument(
        "--level",
        required=True,
        choices=["introductory", "assisted", "independent", "transferable"],
    )
    q.add_argument("--assessor", required=True)
    q.add_argument(
        "--assessor-kind", choices=["human", "test_fixture"], default="human"
    )
    q.add_argument("--evidence-ref", action="append", required=True)
    q.add_argument("--rationale", required=True)
    q.add_argument("--assessed-at", help="timezone-aware ISO-8601 timestamp")
    q.add_argument("--review-due", required=True, help="ISO date")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_assess)

    q = lsub.add_parser(
        "plan", help="recommend one deterministic evidence-bound learning path"
    )
    q.add_argument("--root", help="private learning-state directory outside Git")
    q.add_argument("--card", help="prefer one card; unmet prerequisites win")
    q.add_argument(
        "--dimension", choices=[item.value for item in MasteryDimension]
    )
    q.add_argument("--today", help="ISO date for deterministic planning")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_plan)

    q = lsub.add_parser(
        "journey-start", help="persist a guided LOCAL_FIXTURE learning journey"
    )
    q.add_argument("--root", help="private learning-state directory outside Git")
    q.add_argument("--journey-id", required=True)
    q.add_argument("--card", help="prefer one card; unmet prerequisites win")
    q.add_argument(
        "--dimension", choices=[item.value for item in MasteryDimension]
    )
    q.add_argument("--objective", help="operator-owned learning objective")
    q.add_argument("--today", help="ISO date for deterministic planning")
    q.add_argument("--at", help="timezone-aware ISO-8601 start timestamp")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_journey_start)

    q = lsub.add_parser(
        "journey-status", help="show integrity-checked guided learning journeys"
    )
    q.add_argument("--root", help="private learning-state directory outside Git")
    q.add_argument("--journey-id", help="show one journey")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_journey_status)

    q = lsub.add_parser(
        "journey-advance", help="advance one learning stage after its evidence exists"
    )
    q.add_argument("--root", help="private learning-state directory outside Git")
    q.add_argument("--journey-id", required=True)
    q.add_argument("--fixture-receipt-ref")
    q.add_argument("--evidence-ref", action="append")
    q.add_argument("--reflection")
    q.add_argument("--assessment-id", help="already persisted human assessment")
    q.add_argument("--at", help="timezone-aware ISO-8601 checkpoint timestamp")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_journey_advance)

    q = lsub.add_parser(
        "journey-abandon", help="stop a journey with a reusable operator reason"
    )
    q.add_argument("--root", help="private learning-state directory outside Git")
    q.add_argument("--journey-id", required=True)
    q.add_argument("--reason", required=True)
    q.add_argument("--at", help="timezone-aware ISO-8601 timestamp")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_learning_journey_abandon)

    hypothesis = sub.add_parser(
        "hypothesis",
        help="rank unproven research hypotheses with transparent factors",
    )
    hsub = hypothesis.add_subparsers(dest="hypothesis_command", required=True)

    q = hsub.add_parser(
        "verify",
        help="run the synthetic, network-free Milestone 6 ranking proof",
    )
    q.add_argument("--out", help="write the private structured proof outside Git")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_hypothesis_verify)

    q = hsub.add_parser(
        "rank",
        help="rank selected hypotheses from a private research workspace",
    )
    q.add_argument("--root", required=True, help="private research-store root outside Git")
    q.add_argument("--workspace", required=True, help="workspace id")
    q.add_argument("--contract", required=True, help="current contract JSON")
    q.add_argument(
        "--assessments",
        required=True,
        help="JSON with five explicit assessed factors per hypothesis",
    )
    q.add_argument("--as-of", help="timezone-aware ISO-8601 ranking time")
    q.add_argument("--out", help="write the private ranked queue outside Git")
    q.add_argument("--json", action="store_true", help="emit structured JSON")
    q.set_defaults(func=cmd_hypothesis_rank)

    programme = sub.add_parser(
        "programme", help="the programme registry: versions, drift, what needs you"
    )
    programme.add_argument(
        "--registry", default=DEFAULT_REGISTRY, help="registry root directory"
    )
    psub = programme.add_subparsers(dest="programme_command", required=True)

    q = psub.add_parser("register", help="register or re-register a programme")
    q.add_argument("programme")
    q.set_defaults(func=cmd_programme_register)

    q = psub.add_parser(
        "register-bundle",
        help="register a saved multi-source programme bundle offline",
    )
    q.add_argument("bundle", help="bundle directory or manifest.json path")
    q.set_defaults(func=cmd_programme_register_bundle)

    q = psub.add_parser("review", help="human-review the latest version")
    q.add_argument("programme_id")
    q.add_argument("--reviewer", required=True)
    q.set_defaults(func=cmd_programme_review)

    q = psub.add_parser("status", help="what needs attention before testing anything")
    q.set_defaults(func=cmd_programme_status)

    q = psub.add_parser("diff", help="compare two versions of a programme's scope")
    q.add_argument("programme_id")
    q.add_argument("a", type=int)
    q.add_argument("b", type=int)
    q.set_defaults(func=cmd_programme_diff)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
