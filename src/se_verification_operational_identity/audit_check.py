"""audit_check.py - Run every verification layer and print a report.

Usage:
    python -m se_verification_operational_identity.audit_check
        [--random N] [--seed S] [--deep] [--emit-lean PATH]

The exit status is nonzero when any check fails, so this doubles as a gate.

What a pass means.
The oracle and the fast checker are two derivations of the audit from the same
raw data, with no shared licence, signature, or relation code.
Their agreement, together with the paper-case regressions, the property
checks, and the Lean vectors, is evidence that the implementations match the
paper's definitions.
It is not a proof.
The operation counts are supporting evidence about how the fast checker
scales, and they do not certify the asymptotic bound of Theorem
``oi.thm.decidable``.
"""

import argparse
from pathlib import Path
import random
import sys

from . import audit_fast, audit_oracle
from .audit_cases import (
    cases,
    nonmonotone_pair,
    omitted_surface_example,
)
from .audit_generate import (
    generated_sweep,
    partition_sweep,
    random_instances,
)
from .audit_lean import emit_vectors
from .audit_model import Generated, Instance, Step, Verdict
from .audit_properties import (
    Coverage,
    check_agreement,
    check_edge_characterization,
    check_history_extension,
    check_omitted_use,
    check_positions,
    check_record_surface,
    check_store_composition,
    check_substitution,
)
from .audit_scaling import scaling_rows


def check_instance(inst: Instance, cov: Coverage, rng: random.Random) -> list[str]:
    """Run every per-instance check on one instance."""
    problems = check_agreement(inst)
    problems += check_positions(inst, cov)
    problems += check_edge_characterization(inst, cov)
    problems += check_store_composition(inst, cov)
    problems += check_substitution(inst, cov)
    problems += check_record_surface(inst, cov)
    problems += check_omitted_use(inst, cov)
    records = inst.records
    extra = tuple(
        Step("f", rng.choice(records), rng.choice(records))
        for _ in range(rng.randint(1, 3))
    )
    problems += check_history_extension(inst, extra, cov)
    return problems


def _paper_cases() -> tuple[list[str], int]:
    """Check every paper case against both checkers."""
    problems: list[str] = []
    ok = 0
    for case in cases():
        expected = case.expected()
        o = audit_oracle.audit(case.inst).key()
        f = audit_fast.audit(case.inst).key()
        if o != expected or f != expected:
            problems.append(
                f"CASE {case.inst.label!r} ({case.paper}): oracle={o} fast={f} want={expected}"
            )
        else:
            ok += 1
    return problems, ok


def _nonmonotone() -> list[str]:
    """Check that a pass is lost under extension and that an edge already witnesses it."""
    before, after = nonmonotone_pair()
    problems: list[str] = []
    b = audit_oracle.audit(before)
    a = audit_oracle.audit(after)
    if b.verdict is not Verdict.PASS or a.verdict is not Verdict.FAIL:
        problems.append(f"NONMONOTONE: before={b.verdict} after={a.verdict}")
    declared = after.declared
    if isinstance(declared, Generated):
        surface = after.surfaces[0]
        edge_pairs = {(s.source, s.target) for s in declared.history}
        if not any(surface.value[x] != surface.value[y] for x, y in edge_pairs):
            problems.append("NONMONOTONE: no licensed edge is itself a witness")
    return problems


def _omitted_surface() -> list[str]:
    """Check ``oi.prop.refutes-family`` on the exclusive-or example."""
    inst, joint = omitted_surface_example()
    problems: list[str] = []
    for surface in inst.surfaces:
        if audit_oracle.audit_surface(inst, surface).verdict is not Verdict.PASS:
            problems.append(f"OMITTED SURFACE: {surface.name} should pass")
    if audit_oracle.audit_store(inst).verdict is not Verdict.PASS:
        problems.append("OMITTED SURFACE: the store of singletons should pass")
    if audit_oracle.audit_surface(inst, joint).verdict is not Verdict.FAIL:
        problems.append("OMITTED SURFACE: the joint surface should fail")
    from dataclasses import replace

    wider = replace(inst, surfaces=(*inst.surfaces, joint))
    for name, res in (
        ("oracle", audit_oracle.audit_store(wider)),
        ("fast", audit_fast.audit_store(wider)),
    ):
        if res.verdict is not Verdict.FAIL:
            problems.append(f"OMITTED SURFACE: {name} store with the joint should fail")
    return problems


def run(random_n: int, seed: int, deep: bool, emit_lean: Path | None) -> int:
    """Run all layers and print a report."""
    problems: list[str] = []
    cov = Coverage()
    rng = random.Random(seed)

    case_problems, case_ok = _paper_cases()
    problems += case_problems
    for inst in cases():
        problems += check_instance(inst.inst, cov, rng)
    problems += _nonmonotone()
    problems += _omitted_surface()

    sweep_counts: dict[str, int] = {}
    sizes = (3, 4, 5) if deep else (3, 4)
    for n in sizes:
        count = 0
        for inst in partition_sweep(n):
            count += 1
            problems += check_agreement(inst)
            problems += check_positions(inst, cov)
            problems += check_substitution(inst, cov)
        sweep_counts[f"partitions n={n}"] = count
    for n in (3, 4) if deep else (3,):
        count = 0
        for inst in generated_sweep(n):
            count += 1
            problems += check_agreement(inst)
            problems += check_edge_characterization(inst, cov)
            problems += check_history_extension(
                inst, (Step("f", inst.records[0], inst.records[-1]),), cov
            )
        sweep_counts[f"generated n={n}"] = count

    for inst in random_instances(random_n, seed=seed):
        problems += check_instance(inst, cov, rng)

    if emit_lean is not None:
        emit_lean.write_text(emit_vectors(), encoding="utf-8")

    _report(case_ok, sweep_counts, random_n, seed, cov, problems)
    return 1 if problems else 0


def _report(
    case_ok: int,
    sweeps: dict[str, int],
    random_n: int,
    seed: int,
    cov: Coverage,
    problems: list[str],
) -> None:
    """Print the verification report."""
    print("=" * 70)
    print("SE-210 finite audit verification")
    print("=" * 70)
    print(f"paper cases             : {case_ok}/{len(cases())} as asserted")
    for name, count in sweeps.items():
        print(f"sweep {name:<17}: {count} instances, all checks")
    print(f"randomized              : {random_n} instances (seed {seed})")
    print("-" * 70)
    print("branch coverage (a property never exercised proves nothing):")
    for name in sorted(cov.counts):
        print(f"  {name:<32}: {cov.counts[name]}")
    print("-" * 70)
    print("operation counts (supporting evidence, not a proof of the bound):")
    for n, h, steps, unions in scaling_rows():
        print(f"  n={n:<7} h={h:<7} parent-steps={steps:<8} unions={unions}")
    print("-" * 70)
    if problems:
        print(f"RESULT: {len(problems)} problem(s) found\n")
        for p in problems[:40]:
            print("  -", p)
    else:
        print("RESULT: all checks passed")


def main() -> int:
    """Command-line entry point."""
    ap = argparse.ArgumentParser(description="SE-210 finite audit verification")
    ap.add_argument("--random", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--deep", action="store_true", help="larger exhaustive sweeps")
    ap.add_argument("--emit-lean", type=Path, default=None)
    args = ap.parse_args()
    return run(args.random, args.seed, args.deep, args.emit_lean)


if __name__ == "__main__":
    sys.exit(main())
