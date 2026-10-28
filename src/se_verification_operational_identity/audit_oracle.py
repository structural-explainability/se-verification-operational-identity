"""audit_oracle.py - Transparent reference checker for the SE-210 audit.

The oracle reads the paper's definitions literally over explicit sets of
ordered record pairs.
It is deliberately simple rather than efficient.

It shares nothing with :mod:`se_verification_operational_identity.audit_fast`
except the pure data classes of
:mod:`se_verification_operational_identity.audit_model`.
In particular it has its own:

- licence evaluation (which history steps contribute edges),
- relation construction (pair sets and a naive fixpoint closure),
- signature computation (identity-treatment signatures from raw uses),
- precondition tests (surface control, computability, warrant), and
- comparison and classification logic.

Agreement with the fast checker therefore tests two separate derivations
from the same raw data.
It does not remove the risk that both derivations misread a definition,
which is why the Lean vectors and the paper-case regressions also exist.
"""

from .audit_model import (
    Declared,
    Generated,
    Instance,
    Kind,
    Record,
    Result,
    Supplied,
    Surface,
    Verdict,
)

type Relation = frozenset[tuple[Record, Record]]


def licensed_edges(declared: Generated) -> list[tuple[Record, Record]]:
    """Return the edges contributed by licensed steps, by literal membership.

    A step contributes an edge exactly when it equals some member of the
    licensed set.
    Family labels are never consulted.
    """
    edges: list[tuple[Record, Record]] = []
    for step in declared.history:
        is_licensed = False
        for candidate in declared.licensed:
            if (
                candidate.family == step.family
                and candidate.source == step.source
                and candidate.target == step.target
            ):
                is_licensed = True
        if is_licensed:
            edges.append((step.source, step.target))
    return edges


def equivalence_closure(
    records: tuple[Record, ...], edges: list[tuple[Record, Record]]
) -> Relation:
    """Return the smallest equivalence relation on the records containing the edges.

    Reflexive pairs and both directions of every edge are added,
    then transitive consequences are added until nothing changes.
    """
    pairs: set[tuple[Record, Record]] = {(r, r) for r in records}
    for x, y in edges:
        pairs.add((x, y))
        pairs.add((y, x))
    changed = True
    while changed:
        changed = False
        snapshot = list(pairs)
        for a, b in snapshot:
            for c, d in snapshot:
                if b == c and (a, d) not in pairs:
                    pairs.add((a, d))
                    changed = True
    return frozenset(pairs)


def declared_relation(inst: Instance, declared: Declared) -> Relation:
    """Return the equivalence relation a declared relation induces on the records."""
    if isinstance(declared, Supplied):
        pairs: set[tuple[Record, Record]] = set()
        for block in declared.blocks:
            for r in block:
                for s in block:
                    pairs.add((r, s))
        return frozenset(pairs)
    return equivalence_closure(inst.records, licensed_edges(declared))


def signature(surface: Surface, r: Record) -> tuple[object, ...]:
    """Return the identity-treatment signature of a record: its outcome under each use."""
    return tuple(use[r] for use in surface.uses)


def computable(surface: Surface, records: tuple[Record, ...]) -> bool:
    """Return whether every use has an outcome for every record."""
    return all(r in use for use in surface.uses for r in records)


def controlled(surface: Surface, records: tuple[Record, ...]) -> bool:
    """Return whether every use gives equal outcomes to records of equal value.

    This is surface control, tested pair by pair as the definition states it.
    It assumes every use is defined on every record.
    """
    for use in surface.uses:
        for r in records:
            for s in records:
                if surface.value[r] == surface.value[s] and use[r] != use[s]:
                    return False
    return True


def warranted(inst: Instance) -> bool:
    """Return whether the audit preconditions are established.

    A licence warrant is required only when some relation is generated.
    """
    w = inst.warrant
    uses_generated = isinstance(inst.declared, Generated) or isinstance(
        inst.sibling, Generated
    )
    return (
        w.declared_valid
        and w.mapping_justified
        and w.scope_bounded
        and (w.licences_warranted or not uses_generated)
    )


def preconditions_hold(inst: Instance, surfaces: tuple[Surface, ...]) -> bool:
    """Return whether the warrant, computability, and surface control all hold."""
    if not warranted(inst):
        return False
    for surface in surfaces:
        if not computable(surface, inst.records):
            return False
        if not controlled(surface, inst.records):
            return False
    return True


def surface_relation(surface: Surface, records: tuple[Record, ...]) -> Relation:
    """Return the treatment relation of one surface: equal signatures."""
    return frozenset(
        (r, s)
        for r in records
        for s in records
        if signature(surface, r) == signature(surface, s)
    )


def store_relation(
    surfaces: tuple[Surface, ...], records: tuple[Record, ...]
) -> Relation:
    """Return the store relation: the intersection of the surface relations."""
    result: Relation = frozenset((r, s) for r in records for s in records)
    for surface in surfaces:
        result = result & surface_relation(surface, records)
    return result


def first_witness(
    tau: Relation, treat: Relation, records: tuple[Record, ...]
) -> tuple[Record, Record] | None:
    """Return the first pair the declaration merges and the treatment separates."""
    for r in records:
        for s in records:
            if (r, s) in tau and (r, s) not in treat:
                return (r, s)
    return None


def position_flags(
    tau: Relation, treat: Relation, sib: Relation
) -> tuple[bool, bool, bool, bool]:
    """Return the four positions (aligned, sub, super, incomparable) of a divergence.

    Both relations are first restricted to the declared relation.
    Exactly one flag is true for every input.
    """
    delta_op = treat & tau
    delta_sib = sib & tau
    op_in_sib = delta_op <= delta_sib
    sib_in_op = delta_sib <= delta_op
    aligned = op_in_sib and sib_in_op
    sub = op_in_sib and not sib_in_op
    sup = sib_in_op and not op_in_sib
    incomparable = not op_in_sib and not sib_in_op
    return (aligned, sub, sup, incomparable)


def compare(
    tau: Relation, treat: Relation, sib: Relation | None, records: tuple[Record, ...]
) -> Result:
    """Compare declared, operational, and alternative relations.

    This assumes the preconditions already hold.
    Substitution is computed whether or not the audit passes.
    """
    substitution = sib is not None and treat == sib and tau != sib
    if tau <= treat:
        return Result(Verdict.PASS, Kind.NONE, substitution, None)
    witness = first_witness(tau, treat, records)
    if sib is None:
        return Result(Verdict.FAIL, Kind.UNPOSITIONED, substitution, witness)
    if (sib & tau) == tau:
        return Result(Verdict.FAIL, Kind.UNPOSITIONED, substitution, witness)
    aligned, sub, sup, _incomparable = position_flags(tau, treat, sib)
    if aligned:
        kind = Kind.ALIGNED
    elif sub:
        kind = Kind.SUB
    elif sup:
        kind = Kind.SUPER
    else:
        kind = Kind.INCOMPARABLE
    return Result(Verdict.FAIL, kind, substitution, witness)


_INDETERMINATE = Result(Verdict.INDETERMINATE, Kind.NONE, False, None)


def audit_surface(inst: Instance, surface: Surface) -> Result:
    """Audit one examined surface against the declared relation."""
    if not preconditions_hold(inst, (surface,)):
        return _INDETERMINATE
    tau = declared_relation(inst, inst.declared)
    sib = None if inst.sibling is None else declared_relation(inst, inst.sibling)
    treat = surface_relation(surface, inst.records)
    return compare(tau, treat, sib, inst.records)


def audit_store(inst: Instance) -> Result:
    """Audit the whole examined family through its intersected relation."""
    if not preconditions_hold(inst, inst.surfaces):
        return _INDETERMINATE
    tau = declared_relation(inst, inst.declared)
    sib = None if inst.sibling is None else declared_relation(inst, inst.sibling)
    treat = store_relation(inst.surfaces, inst.records)
    return compare(tau, treat, sib, inst.records)


def audit(inst: Instance) -> Result:
    """Audit an instance: its single surface, or its store when there are several."""
    if len(inst.surfaces) == 1:
        return audit_surface(inst, inst.surfaces[0])
    return audit_store(inst)
