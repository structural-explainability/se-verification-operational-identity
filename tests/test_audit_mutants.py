"""Seeded faults are caught.

Each mutant is a deliberate error.
A mutant in the fast checker alone must be caught by the differential.
A fault planted in both checkers at once models a shared misreading of the
paper, which a differential cannot see, so those tests require the
paper-case regressions and property checks to catch it.
"""

from collections.abc import Callable, Hashable, Mapping

import pytest

from se_verification_operational_identity import audit_fast, audit_oracle
from se_verification_operational_identity.audit_cases import cases
from se_verification_operational_identity.audit_generate import (
    generated_sweep,
    partition_sweep,
    random_instances,
)
from se_verification_operational_identity.audit_model import (
    Declared,
    Generated,
    Instance,
    Kind,
    Record,
    Result,
    Surface,
    Verdict,
)
from se_verification_operational_identity.audit_properties import (
    Coverage,
    check_agreement,
    check_edge_characterization,
    check_substitution,
)

_ORIGINAL_COMPARE = audit_fast.compare
_ORIGINAL_ORACLE_COMPARE = audit_oracle.compare


def _pool() -> list[Instance]:
    pool = [c.inst for c in cases()]
    pool += list(partition_sweep(3))
    pool += list(generated_sweep(3))
    pool += list(random_instances(400, seed=11))
    return pool


def _differential_flags(pool: list[Instance]) -> bool:
    return any(check_agreement(inst) for inst in pool)


def _regression_flags() -> bool:
    for case in cases():
        if (
            audit_oracle.audit(case.inst).key() != case.expected()
            or audit_fast.audit(case.inst).key() != case.expected()
        ):
            return True
    return False


def _property_flags(pool: list[Instance]) -> bool:
    cov = Coverage()
    return any(
        check_edge_characterization(i, cov) or check_substitution(i, cov) for i in pool
    )


# --- mutants of the fast checker -------------------------------------------------


def _all_steps_as_edges(
    records: tuple[Record, ...], declared: Declared, counter: audit_fast.OpCounter
) -> dict[Record, Hashable]:
    """Superseded construction: every history step joins its endpoints."""
    if isinstance(declared, Generated):
        uf = audit_fast.UnionFind(records, counter)
        for step in declared.history:
            uf.union(step.source, step.target)
        return {r: uf.find(r) for r in records}
    return _ORIGINAL_DECLARED(records, declared, counter)


_ORIGINAL_DECLARED = audit_fast.declared_labels
_ORIGINAL_SIGNATURES = audit_fast.surface_signatures


def _no_closure(
    records: tuple[Record, ...], declared: Declared, counter: audit_fast.OpCounter
) -> dict[Record, Hashable]:
    """Join only directly adjacent records, with no transitive closure."""
    if isinstance(declared, Generated):
        label: dict[Record, Hashable] = {r: r for r in records}
        for step in declared.history:
            if step in declared.licensed:
                low = min(step.source, step.target)
                label[step.source] = min(str(label[step.source]), low)
                label[step.target] = min(str(label[step.target]), low)
        return label
    return _ORIGINAL_DECLARED(records, declared, counter)


def _first_use_only(
    surface: Surface, records: tuple[Record, ...], counter: audit_fast.OpCounter
) -> dict[Record, tuple[Hashable, ...]]:
    sigs = _ORIGINAL_SIGNATURES(surface, records, counter)
    return {r: sig[:1] for r, sig in sigs.items()}


def _store_by_any(
    inst: Instance, counter: audit_fast.OpCounter | None = None
) -> Result:
    """Wrong composition: the store passes when any surface passes."""
    results = [audit_fast.audit_surface(inst, s, counter) for s in inst.surfaces]
    if any(r.verdict is Verdict.INDETERMINATE for r in results):
        return results[0]
    for r in results:
        if r.verdict is Verdict.PASS:
            return r
    return results[0]


def _reversed_roles(
    records: tuple[Record, ...],
    tau: Mapping[Record, Hashable],
    op: Mapping[Record, Hashable],
    sib: Mapping[Record, Hashable] | None,
) -> Result:
    return _ORIGINAL_COMPARE(records, op, tau, sib)


def _swap_sub_super(
    records: tuple[Record, ...],
    tau: Mapping[Record, Hashable],
    op: Mapping[Record, Hashable],
    sib: Mapping[Record, Hashable] | None,
) -> Result:
    res = _ORIGINAL_COMPARE(records, tau, op, sib)
    swap = {Kind.SUB: Kind.SUPER, Kind.SUPER: Kind.SUB}
    return Result(
        res.verdict, swap.get(res.kind, res.kind), res.substitution, res.witness
    )


def _global_positions(
    records: tuple[Record, ...],
    tau: Mapping[Record, Hashable],
    op: Mapping[Record, Hashable],
    sib: Mapping[Record, Hashable] | None,
) -> Result:
    """Compare operational and alternative globally, not inside declared classes."""
    res = _ORIGINAL_COMPARE(records, tau, op, sib)
    if res.verdict is not Verdict.FAIL or sib is None or res.kind is Kind.UNPOSITIONED:
        return res
    everyone = list(records)
    a = audit_fast.refines_within(everyone, op, sib)
    b = audit_fast.refines_within(everyone, sib, op)
    kind = (
        Kind.ALIGNED
        if a and b
        else Kind.SUB
        if a
        else Kind.SUPER
        if b
        else Kind.INCOMPARABLE
    )
    return Result(res.verdict, kind, res.substitution, res.witness)


def _substitution_is_alignment(
    records: tuple[Record, ...],
    tau: Mapping[Record, Hashable],
    op: Mapping[Record, Hashable],
    sib: Mapping[Record, Hashable] | None,
) -> Result:
    res = _ORIGINAL_COMPARE(records, tau, op, sib)
    return Result(res.verdict, res.kind, res.kind is Kind.ALIGNED, res.witness)


def _substitution_false_on_pass(
    records: tuple[Record, ...],
    tau: Mapping[Record, Hashable],
    op: Mapping[Record, Hashable],
    sib: Mapping[Record, Hashable] | None,
) -> Result:
    res = _ORIGINAL_COMPARE(records, tau, op, sib)
    return Result(
        res.verdict,
        res.kind,
        res.substitution and res.verdict is Verdict.FAIL,
        res.witness,
    )


def _substitution_ignores_difference(
    records: tuple[Record, ...],
    tau: Mapping[Record, Hashable],
    op: Mapping[Record, Hashable],
    sib: Mapping[Record, Hashable] | None,
) -> Result:
    res = _ORIGINAL_COMPARE(records, tau, op, sib)
    equal = sib is not None and audit_fast.same_partition(op, sib, list(records))
    return Result(res.verdict, res.kind, equal, res.witness)


def _bad_witness(
    records: tuple[Record, ...],
    tau: Mapping[Record, Hashable],
    op: Mapping[Record, Hashable],
    sib: Mapping[Record, Hashable] | None,
) -> Result:
    res = _ORIGINAL_COMPARE(records, tau, op, sib)
    if res.witness is None:
        return res
    return Result(res.verdict, res.kind, res.substitution, (records[0], records[0]))


def _always_warranted(_inst: Instance) -> bool:
    return True


def _ready_skips_control(surface: Surface, records: tuple[Record, ...]) -> bool:
    return all(r in use for use in surface.uses for r in records)


FAST_MUTANTS: dict[str, tuple[str, object]] = {
    "superseded construction (every step joins)": (
        "declared_labels",
        _all_steps_as_edges,
    ),
    "no transitive closure": ("declared_labels", _no_closure),
    "only the first use is read": ("surface_signatures", _first_use_only),
    "store passes when any surface passes": ("audit_store", _store_by_any),
    "faithfulness direction reversed": ("compare", _reversed_roles),
    "sub and super swapped": ("compare", _swap_sub_super),
    "positions compared globally": ("compare", _global_positions),
    "substitution := alignment": ("compare", _substitution_is_alignment),
    "substitution false on a pass": ("compare", _substitution_false_on_pass),
    "substitution ignores regime difference": (
        "compare",
        _substitution_ignores_difference,
    ),
    "witness is not a witness": ("compare", _bad_witness),
    "warrant ignored": ("is_warranted", _always_warranted),
    "surface control not tested": ("surface_ready", _ready_skips_control),
}


@pytest.mark.parametrize("name", sorted(FAST_MUTANTS))
def test_fast_mutant_is_caught_by_the_differential(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, mutant = FAST_MUTANTS[name]
    monkeypatch.setattr(audit_fast, target, mutant)
    assert _differential_flags(_pool()), f"mutant survived: {name}"


# --- faults planted in both checkers at once -------------------------------------


def _oracle_all_steps(declared: Generated) -> list[tuple[Record, Record]]:
    return [(s.source, s.target) for s in declared.history]


def _both_false_on_pass(orig: Callable[..., Result]) -> Callable[..., Result]:
    def wrapped(*args: object) -> Result:
        res = orig(*args)
        return Result(
            res.verdict,
            res.kind,
            res.substitution and res.verdict is Verdict.FAIL,
            res.witness,
        )

    return wrapped


def test_shared_misreading_of_licences_is_invisible_to_the_differential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both checkers read every step as an edge, as the superseded paper did."""
    monkeypatch.setattr(audit_oracle, "licensed_edges", _oracle_all_steps)
    monkeypatch.setattr(audit_fast, "declared_labels", _all_steps_as_edges)
    pool = _pool()
    assert not _differential_flags(pool), "the two checkers should still agree"
    assert _regression_flags(), "paper cases must catch the shared misreading"
    assert _property_flags(pool), "the edge derivation must disagree with both"


def test_shared_misreading_of_substitution_is_caught_by_cases_and_properties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both checkers report no substitution on a pass, as the old model did."""
    monkeypatch.setattr(
        audit_oracle, "compare", _both_false_on_pass(_ORIGINAL_ORACLE_COMPARE)
    )
    monkeypatch.setattr(audit_fast, "compare", _both_false_on_pass(_ORIGINAL_COMPARE))
    pool = _pool()
    assert not _differential_flags(pool)
    assert _regression_flags()
    assert _property_flags(pool)
