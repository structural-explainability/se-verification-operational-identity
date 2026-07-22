"""check.py - Run every verification layer and print a report.

Usage:  python -m se_verification_operational_identity.check [--random N] [--seed S]

Exit status is nonzero if any check fails,
so this doubles as a pre-publication gate.

A failure means the oracle and the optimized checker disagree,
a paper example does not classify as asserted,
an extracted witness does not satisfy Definition 4.3,
or the monotonicity property does not hold.
"""

import argparse
import sys

from . import fast, oracle
from .generate import exhaustive_small, random_instances
from .model import Instance, Result, Verdict
from .oracle import declared_relation, treatment_relation
from .paper_cases import cases, monotonicity_pair


def witness_valid(inst: Instance, res: Result) -> bool:
    """A returned witness must satisfy Definition 4.3: r ~_tau s and split."""
    if res.witness is None:
        return res.verdict is Verdict.PASS
    r, s = res.witness
    tau_rel = declared_relation(inst, inst.tau)
    treat = treatment_relation(inst)
    return (r, s) in tau_rel and (r, s) not in treat


def _diff(inst: Instance) -> list[str]:
    problems: list[str] = []
    o = oracle.audit(inst)
    f = fast.audit(inst)
    if o.key() != f.key():
        problems.append(
            f"oracle/fast disagree on {inst.label!r}: oracle={o.key()} fast={f.key()}"
        )
    for name, res in (("oracle", o), ("fast", f)):
        if not witness_valid(inst, res):
            problems.append(
                f"{name} returned an invalid witness {res.witness} on {inst.label!r}"
            )
    return problems


def run(random_n: int, seed: int) -> int:
    """Run all verification layers and print a report."""
    failures: list[str] = []

    # 1. Regression: the paper's own examples classify as asserted (oracle).
    reg_ok = 0
    for inst, want_v, want_k, want_sub in cases():
        res = oracle.audit(inst)
        if (res.verdict, res.kind, res.substitution) != (want_v, want_k, want_sub):
            failures.append(
                f"REGRESSION {inst.label!r}: got "
                f"({res.verdict.value}, {res.kind.value}, sub={res.substitution}); "
                f"want ({want_v.value}, {want_k.value}, sub={want_sub})"
            )
        else:
            reg_ok += 1
        failures.extend(_diff(inst))  # and oracle==fast on each

    # 2. Proposition 5.5: extending history can change pass to fail.
    before, after = monotonicity_pair()
    b_res, a_res = oracle.audit(before), oracle.audit(after)
    mono_ok = b_res.verdict is Verdict.PASS and a_res.verdict is Verdict.FAIL
    if not mono_ok:
        failures.append(
            f"MONOTONICITY: before={b_res.verdict.value} after={a_res.verdict.value}; "
            "want pass then fail"
        )
    failures.extend(_diff(before))
    failures.extend(_diff(after))

    # 3. Exhaustive small differential sweep.
    ex_n = 0
    for inst in exhaustive_small():
        ex_n += 1
        failures.extend(_diff(inst))

    # 4. Randomized differential.
    for inst in random_instances(random_n, seed=seed):
        failures.extend(_diff(inst))

    # 5. Randomized history-extension property: extending history never turns
    #    a fail back into a pass.
    #    Failure is monotone under history extension,
    #    and an existing divergence witness remains valid.
    mono_prop_ok = _check_monotone_property(random_n, seed)
    if not mono_prop_ok:
        failures.append(
            "MONOTONICITY PROPERTY: a fail reverted to pass under extension"
        )

    print("=" * 68)
    print("SE-210 finite-core verification")
    print("=" * 68)
    print(f"regression cases        : {reg_ok}/{len(cases())} classified as asserted")
    print(f"monotonicity (Prop 5.5) : {'ok' if mono_ok else 'FAIL'}")
    print(f"exhaustive-small diffs  : {ex_n} instances, oracle vs fast")
    print(f"randomized diffs        : {random_n} instances (seed {seed})")
    print(f"monotone property       : {'ok' if mono_prop_ok else 'FAIL'}")
    print("-" * 68)
    if failures:
        print(f"RESULT: {len(failures)} problem(s) found\n")
        for p in failures[:40]:
            print("  -", p)
        return 1
    print("RESULT: all checks passed")
    return 0


def _check_monotone_property(count: int, seed: int) -> bool:
    import random as _random

    rng = _random.Random(seed + 1)  # noqa: S311
    for _ in range(count):
        base = next(random_instances(1, seed=rng.randint(0, 10**9)))
        # Extend the history by appending edges over the same records.
        extra = tuple(
            (
                rng.choice(("a", "b", "c")),
                rng.choice(base.records),
                rng.choice(base.records),
            )
            for _ in range(rng.randint(1, 3))
        )
        ext = Instance(
            records=base.records,
            history=base.history + extra,
            tau=base.tau,
            sib=base.sib,
            surface=base.surface,
            label="extended",
        )
        if (
            oracle.audit(base).verdict is Verdict.FAIL
            and oracle.audit(ext).verdict is Verdict.PASS
        ):
            return False
    return True


def main() -> int:
    """Main entry point for command-line execution."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--random", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    return run(args.random, args.seed)


if __name__ == "__main__":
    sys.exit(main())
