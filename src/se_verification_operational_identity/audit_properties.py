"""audit_properties.py - Property checks for results stated in the revised paper.

Each function takes an instance and returns a list of problem descriptions.
An empty list means the property held on that instance.

The properties are statements of the paper, not statements the checkers were
built from:

- agreement of the oracle and fast checkers, and validity of witnesses,
- exhaustiveness and exclusivity of the four positions,
- the edge characterization of faithfulness (``oi.prop.edges``),
- store composition (``oi.prop.compose``) and the joint surface,
- substitution and its two consequences (``oi.prop.substitution-witness`` and
  ``oi.rem.merging-substitution``),
- the record-identity surface (``oi.rem.registry``),
- an omitted use overturning a pass (``oi.prop.refutes-use``), and
- history extension (``oi.prop.nonmonotone``).
"""

from collections.abc import Hashable
from dataclasses import dataclass, field, replace

from . import audit_edges, audit_fast, audit_oracle
from .audit_model import (
    Generated,
    Instance,
    Kind,
    Record,
    Result,
    Step,
    Surface,
    Verdict,
    Warrant,
)


@dataclass
class Coverage:
    """Count how often each branch of a property was actually exercised.

    A property that is never exercised proves nothing, so the harness reports
    these counts.
    """

    counts: dict[str, int] = field(default_factory=dict)

    def hit(self, name: str) -> None:
        """Record one exercise of the named branch."""
        self.counts[name] = self.counts.get(name, 0) + 1


def _witness_valid(
    inst: Instance, result: Result, surfaces: tuple[Surface, ...]
) -> bool:
    """Return whether a result's witness fits its verdict, using oracle relations."""
    if result.verdict is not Verdict.FAIL:
        return result.witness is None
    if result.witness is None:
        return False
    tau = audit_oracle.declared_relation(inst, inst.declared)
    treat = audit_oracle.store_relation(surfaces, inst.records)
    return result.witness in tau and result.witness not in treat


def check_agreement(inst: Instance) -> list[str]:
    """Check that the two checkers agree and that witnesses are valid.

    Every surface is audited alone and the family is audited as a store.
    """
    problems: list[str] = []
    for surface in inst.surfaces:
        o = audit_oracle.audit_surface(inst, surface)
        f = audit_fast.audit_surface(inst, surface)
        if o.key() != f.key():
            problems.append(
                f"{inst.label}: surface {surface.name} oracle={o.key()} fast={f.key()}"
            )
        for name, res in (("oracle", o), ("fast", f)):
            if not _witness_valid(inst, res, (surface,)):
                problems.append(f"{inst.label}: {name} witness invalid {res.witness}")
    so = audit_oracle.audit_store(inst)
    sf = audit_fast.audit_store(inst)
    if so.key() != sf.key():
        problems.append(f"{inst.label}: store oracle={so.key()} fast={sf.key()}")
    for name, res in (("oracle", so), ("fast", sf)):
        if not _witness_valid(inst, res, inst.surfaces):
            problems.append(f"{inst.label}: {name} store witness invalid {res.witness}")
    return problems


def check_positions(inst: Instance, cov: Coverage) -> list[str]:
    """Check that exactly one of the four positions holds and matches the kind."""
    problems: list[str] = []
    if inst.sibling is None:
        return problems
    tau = audit_oracle.declared_relation(inst, inst.declared)
    sib = audit_oracle.declared_relation(inst, inst.sibling)
    for surface in inst.surfaces:
        result = audit_oracle.audit_surface(inst, surface)
        if result.verdict is not Verdict.FAIL or (sib & tau) == tau:
            continue
        treat = audit_oracle.surface_relation(surface, inst.records)
        flags = audit_oracle.position_flags(tau, treat, sib)
        if sum(flags) != 1:
            problems.append(f"{inst.label}: positions not exclusive {flags}")
        names = (Kind.ALIGNED, Kind.SUB, Kind.SUPER, Kind.INCOMPARABLE)
        chosen = names[flags.index(True)]
        if chosen is not result.kind:
            problems.append(
                f"{inst.label}: kind {result.kind} but positions say {chosen}"
            )
        cov.hit(f"position:{result.kind.value}")
    return problems


def check_edge_characterization(inst: Instance, cov: Coverage) -> list[str]:
    """Check ``oi.prop.edges`` for a generated declared relation."""
    problems: list[str] = []
    if not isinstance(inst.declared, Generated):
        return problems
    for surface in inst.surfaces:
        result = audit_oracle.audit_surface(inst, surface)
        if result.verdict is Verdict.INDETERMINATE:
            continue
        faithful, edge = audit_edges.edge_faithfulness(inst, surface)
        if faithful != (result.verdict is Verdict.PASS):
            problems.append(
                f"{inst.label}: edge faithfulness {faithful} vs {result.verdict}"
            )
            continue
        cov.hit("edges:faithful" if faithful else "edges:unfaithful")
        if edge is None:
            continue
        x, y = edge
        tau = audit_oracle.declared_relation(inst, inst.declared)
        treat = audit_oracle.surface_relation(surface, inst.records)
        if (x, y) not in tau or (x, y) in treat:
            problems.append(f"{inst.label}: edge {edge} is not a witness")
        if surface.value[x] == surface.value[y]:
            problems.append(f"{inst.label}: edge {edge} has equal mechanism values")
    return problems


def joint_surface(
    surfaces: tuple[Surface, ...], records: tuple[Record, ...]
) -> Surface:
    """Return the joint surface: pair of mechanisms, concatenated uses."""
    value: dict[Record, Hashable] = {
        r: tuple(s.value[r] for s in surfaces) for r in records
    }
    uses = tuple(use for s in surfaces for use in s.uses)
    return Surface("joint", value, uses)


def check_store_composition(inst: Instance, cov: Coverage) -> list[str]:
    """Check ``oi.prop.compose`` and that the joint surface has the store relation."""
    problems: list[str] = []
    singles = [audit_oracle.audit_surface(inst, s) for s in inst.surfaces]
    store = audit_oracle.audit_store(inst)
    if any(r.verdict is Verdict.INDETERMINATE for r in singles):
        if store.verdict is not Verdict.INDETERMINATE:
            problems.append(f"{inst.label}: store determinate but a surface is not")
        return problems
    if store.verdict is Verdict.INDETERMINATE:
        problems.append(
            f"{inst.label}: store indeterminate but every surface determinate"
        )
        return problems
    all_pass = all(r.verdict is Verdict.PASS for r in singles)
    if all_pass != (store.verdict is Verdict.PASS):
        problems.append(f"{inst.label}: store verdict {store.verdict} vs surfaces")
    tau = audit_oracle.declared_relation(inst, inst.declared)
    store_rel = audit_oracle.store_relation(inst.surfaces, inst.records)
    for res in singles:
        if res.witness is not None and res.witness in store_rel:
            problems.append(f"{inst.label}: surface witness is not a store witness")
    joint = joint_surface(inst.surfaces, inst.records)
    joint_result = audit_oracle.audit_surface(inst, joint)
    if joint_result.key() != store.key():
        problems.append(
            f"{inst.label}: joint {joint_result.key()} vs store {store.key()}"
        )
    if tau <= store_rel:
        cov.hit("store:pass")
    else:
        cov.hit("store:fail")
    return problems


def check_substitution(inst: Instance, cov: Coverage) -> list[str]:
    """Check both consequences of substitution.

    When the declared relation has a pair the alternative separates,
    substitution forces a sibling-aligned failure whose witnesses include
    every such pair.
    When the declared relation is contained in the alternative,
    substitution forces a pass.
    """
    problems: list[str] = []
    if inst.sibling is None:
        return problems
    tau = audit_oracle.declared_relation(inst, inst.declared)
    sib = audit_oracle.declared_relation(inst, inst.sibling)
    for surface in inst.surfaces:
        result = audit_oracle.audit_surface(inst, surface)
        if result.verdict is Verdict.INDETERMINATE:
            if result.substitution:
                problems.append(
                    f"{inst.label}: indeterminate result claims substitution"
                )
            continue
        treat = audit_oracle.surface_relation(surface, inst.records)
        expected = treat == sib and tau != sib
        if result.substitution != expected:
            problems.append(f"{inst.label}: substitution flag {result.substitution}")
        if not result.substitution:
            continue
        if tau <= sib:
            cov.hit("substitution:with-pass")
            if result.verdict is not Verdict.PASS:
                problems.append(
                    f"{inst.label}: substitution inside the alternative must pass"
                )
        else:
            cov.hit("substitution:with-witness")
            if result.verdict is not Verdict.FAIL or result.kind is not Kind.ALIGNED:
                problems.append(
                    f"{inst.label}: substitution must give an aligned failure"
                )
            for pair in tau - sib:
                if pair in treat:
                    problems.append(f"{inst.label}: {pair} should be a witness")
    return problems


def record_surface(records: tuple[Record, ...]) -> Surface:
    """Return the record-identity surface: mechanism and only use are the record."""
    return Surface("record", {r: r for r in records}, ({r: r for r in records},))


def check_record_surface(inst: Instance, cov: Coverage) -> list[str]:
    """Check that the record surface passes exactly when no distinct records merge."""
    problems: list[str] = []
    probe = replace(
        inst, surfaces=(record_surface(inst.records),), sibling=None, warrant=Warrant()
    )
    result = audit_oracle.audit_surface(probe, probe.surfaces[0])
    tau = audit_oracle.declared_relation(inst, inst.declared)
    merges_distinct = any(r != s for r, s in tau)
    if (result.verdict is Verdict.PASS) == merges_distinct:
        problems.append(f"{inst.label}: record surface verdict {result.verdict}")
    cov.hit("record-surface:merging" if merges_distinct else "record-surface:identity")
    return problems


def check_omitted_use(inst: Instance, cov: Coverage) -> list[str]:
    """Check ``oi.prop.refutes-use`` on every surface that passes.

    When the mechanism separates a declared pair, a use that reports the
    mechanism value is controlled and turns the pass into a failure.
    When the mechanism does not separate the pair, any use that does
    separate it violates surface control, so the audit is indeterminate.
    """
    problems: list[str] = []
    tau = audit_oracle.declared_relation(inst, inst.declared)
    pairs = sorted((r, s) for r, s in tau if r != s)
    if not pairs:
        return problems
    r, s = pairs[0]
    for surface in inst.surfaces:
        if audit_oracle.audit_surface(inst, surface).verdict is not Verdict.PASS:
            continue
        if surface.value[r] != surface.value[s]:
            extra: dict[Record, Hashable] = dict(surface.value)
            expected = Verdict.FAIL
            cov.hit("omitted-use:controlled")
        else:
            extra = dict.fromkeys(inst.records, 0)
            extra[s] = 1
            expected = Verdict.INDETERMINATE
            cov.hit("omitted-use:uncontrolled")
        extended = Surface(surface.name, surface.value, (*surface.uses, extra))
        probe = replace(inst, surfaces=(extended,))
        for name, res in (
            ("oracle", audit_oracle.audit_surface(probe, extended)),
            ("fast", audit_fast.audit_surface(probe, extended)),
        ):
            if res.verdict is not expected:
                problems.append(
                    f"{inst.label}: {name} gave {res.verdict} not {expected}"
                )
            if expected is Verdict.FAIL and not _witness_valid(probe, res, (extended,)):
                problems.append(
                    f"{inst.label}: {name} witness invalid after omitted use"
                )
    return problems


def check_history_extension(
    inst: Instance, extra: tuple[Step, ...], cov: Coverage
) -> list[str]:
    """Check how a generated relation responds to extra history.

    Extra licensed steps can only enlarge the relation, so a failure stays a
    failure.
    Extra unlicensed steps leave every result unchanged.
    """
    problems: list[str] = []
    declared = inst.declared
    if not isinstance(declared, Generated):
        return problems
    licensed_more = replace(
        inst,
        declared=Generated(
            declared.history + extra, declared.licensed | frozenset(extra)
        ),
    )
    inert_steps = tuple(
        Step("inert", s.source, s.target)
        for s in extra
        if Step("inert", s.source, s.target) not in declared.licensed
    )
    inert_more = replace(
        inst, declared=Generated(declared.history + inert_steps, declared.licensed)
    )
    for surface in inst.surfaces:
        before = audit_oracle.audit_surface(inst, surface)
        after = audit_oracle.audit_surface(licensed_more, surface)
        if before.verdict is Verdict.FAIL and after.verdict is not Verdict.FAIL:
            problems.append(f"{inst.label}: a failure reverted under extension")
        if before.verdict is Verdict.PASS and after.verdict is Verdict.FAIL:
            cov.hit("history:pass-lost")
        inert = audit_oracle.audit_surface(inert_more, surface)
        if inert.key() != before.key():
            problems.append(f"{inst.label}: unlicensed steps changed the result")
    return problems
