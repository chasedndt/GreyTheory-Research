"""Command line surface for the Authority Plane.

Deliberately small. It exposes the four things an operator needs to do without
writing Python: compile a programme, review a clean contract, ask the gate a
question, and verify the audit chain.

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
from pathlib import Path

from greytheory.audit import AuditLog, AuditVerificationError
from greytheory.authority.compiler import compile_contract, mark_reviewed
from greytheory.authority.gate import AccessRequest, AuthorityLevel, Gate
from greytheory.authority.scope import ScopeContract
from greytheory.registry import ProgrammeRegistry, RegistryError

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greytheory",
        description="GreyTheory AI - Authority Plane. No authorisation, no execution.",
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
