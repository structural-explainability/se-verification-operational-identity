"""audit_fast.py - Partition-label implementation of the SE-210 audit.

This checker builds block labels instead of pair sets.
Generated relations are closed with union-find (path compression and union by
size), operational classes come from signature tuples, and every comparison
scans labels inside declared blocks.
No subset of ``R x R`` is materialized.

It shares nothing with :mod:`se_verification_operational_identity.audit_oracle`
except the pure data classes of
:mod:`se_verification_operational_identity.audit_model`.
It has its own licence evaluation (set membership), signature computation,
precondition tests (single passes over value-to-outcome dictionaries),
relation construction, and comparison.

:class:`OpCounter` counts the primitive operations the procedure performs.
The counts are supporting evidence about how the implementation scales.
They are not a proof of the asymptotic bound stated in Theorem
``oi.thm.decidable``, which is a statement about every input and every
sufficiently large size.
"""

from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass

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


@dataclass
class OpCounter:
    """Count primitive operations performed by the fast checker.

    ``parent_steps`` counts parent-pointer traversals in union-find,
    ``unions`` counts successful merges,
    and ``use_evals`` counts identified-use evaluations.
    """

    parent_steps: int = 0
    unions: int = 0
    use_evals: int = 0


class UnionFind:
    """Disjoint groups of records with path compression and union by size."""

    def __init__(self, items: Iterable[Record], counter: OpCounter) -> None:
        """Create one singleton group per record."""
        self.parent: dict[Record, Record] = {x: x for x in items}
        self.size: dict[Record, int] = dict.fromkeys(self.parent, 1)
        self.counter = counter

    def find(self, x: Record) -> Record:
        """Return the representative of the group containing ``x``."""
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
            self.counter.parent_steps += 1
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
            self.counter.parent_steps += 1
        return root

    def union(self, a: Record, b: Record) -> None:
        """Merge the groups of ``a`` and ``b``, attaching the smaller to the larger."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.counter.unions += 1


def declared_labels(
    records: tuple[Record, ...], declared: Declared, counter: OpCounter
) -> dict[Record, Hashable]:
    """Label every record with its class under a declared relation."""
    if isinstance(declared, Supplied):
        labelled: dict[Record, Hashable] = {}
        for index, block in enumerate(declared.blocks):
            for r in block:
                labelled[r] = index
        return labelled
    uf = UnionFind(records, counter)
    licensed = declared.licensed
    for step in declared.history:
        if step in licensed:
            uf.union(step.source, step.target)
    return {r: uf.find(r) for r in records}


def surface_signatures(
    surface: Surface, records: tuple[Record, ...], counter: OpCounter
) -> dict[Record, tuple[Hashable, ...]]:
    """Return each record's signature: its outcomes under the surface's uses."""
    counter.use_evals += len(surface.uses) * len(records)
    return {r: tuple(use[r] for use in surface.uses) for r in records}


def surface_ready(surface: Surface, records: tuple[Record, ...]) -> bool:
    """Return whether every use is defined everywhere and factors through the value.

    Each use is scanned once, remembering the outcome seen for each value.
    """
    for use in surface.uses:
        seen: dict[Hashable, Hashable] = {}
        for r in records:
            if r not in use:
                return False
            value = surface.value[r]
            if value in seen:
                if seen[value] != use[r]:
                    return False
            else:
                seen[value] = use[r]
    return True


def is_warranted(inst: Instance) -> bool:
    """Return whether the audit preconditions are established."""
    w = inst.warrant
    needs_licences = isinstance(inst.declared, Generated) or isinstance(
        inst.sibling, Generated
    )
    if needs_licences and not w.licences_warranted:
        return False
    return w.declared_valid and w.mapping_justified and w.scope_bounded


def blocks_of(
    labels: Mapping[Record, Hashable], records: Iterable[Record]
) -> list[list[Record]]:
    """Group records by label, keeping first-seen order."""
    groups: dict[Hashable, list[Record]] = {}
    for r in records:
        groups.setdefault(labels[r], []).append(r)
    return list(groups.values())


def refines_within(
    block: list[Record],
    fine: Mapping[Record, Hashable],
    coarse: Mapping[Record, Hashable],
) -> bool:
    """Return whether ``fine`` refines ``coarse`` among the records of one block."""
    seen: dict[Hashable, Hashable] = {}
    for r in block:
        f, c = fine[r], coarse[r]
        if f in seen:
            if seen[f] != c:
                return False
        else:
            seen[f] = c
    return True


def same_partition(
    a: Mapping[Record, Hashable], b: Mapping[Record, Hashable], records: list[Record]
) -> bool:
    """Return whether two labelings induce the same partition."""
    return refines_within(records, a, b) and refines_within(records, b, a)


def compare(
    records: tuple[Record, ...],
    tau: Mapping[Record, Hashable],
    op: Mapping[Record, Hashable],
    sib: Mapping[Record, Hashable] | None,
) -> Result:
    """Compare declared, operational, and alternative labelings.

    The preconditions are assumed to hold.
    Substitution is computed whether or not the audit passes.
    """
    everyone = list(records)
    substitution = (
        sib is not None
        and same_partition(op, sib, everyone)
        and not same_partition(tau, sib, everyone)
    )
    tau_blocks = blocks_of(tau, records)
    witness: tuple[Record, Record] | None = None
    for block in tau_blocks:
        anchor = block[0]
        for r in block[1:]:
            if op[r] != op[anchor]:
                witness = (anchor, r)
                break
        if witness is not None:
            break
    if witness is None:
        return Result(Verdict.PASS, Kind.NONE, substitution, None)
    if sib is None:
        return Result(Verdict.FAIL, Kind.UNPOSITIONED, substitution, witness)
    sibling_splits = any(
        any(sib[r] != sib[block[0]] for r in block) for block in tau_blocks
    )
    if not sibling_splits:
        return Result(Verdict.FAIL, Kind.UNPOSITIONED, substitution, witness)
    op_in_sib = all(refines_within(b, op, sib) for b in tau_blocks)
    sib_in_op = all(refines_within(b, sib, op) for b in tau_blocks)
    if op_in_sib and sib_in_op:
        kind = Kind.ALIGNED
    elif op_in_sib:
        kind = Kind.SUB
    elif sib_in_op:
        kind = Kind.SUPER
    else:
        kind = Kind.INCOMPARABLE
    return Result(Verdict.FAIL, kind, substitution, witness)


_INDETERMINATE = Result(Verdict.INDETERMINATE, Kind.NONE, False, None)


def _labels_for(
    inst: Instance, counter: OpCounter
) -> tuple[dict[Record, Hashable], dict[Record, Hashable] | None]:
    """Return declared and optional alternative labelings."""
    tau = declared_labels(inst.records, inst.declared, counter)
    sib = (
        None
        if inst.sibling is None
        else declared_labels(inst.records, inst.sibling, counter)
    )
    return tau, sib


def audit_surface(
    inst: Instance, surface: Surface, counter: OpCounter | None = None
) -> Result:
    """Audit one examined surface against the declared relation."""
    counter = counter if counter is not None else OpCounter()
    if not is_warranted(inst) or not surface_ready(surface, inst.records):
        return _INDETERMINATE
    tau, sib = _labels_for(inst, counter)
    sigs = surface_signatures(surface, inst.records, counter)
    op: dict[Record, Hashable] = dict(sigs)
    return compare(inst.records, tau, op, sib)


def audit_store(inst: Instance, counter: OpCounter | None = None) -> Result:
    """Audit the whole examined family.

    Two records are the same in the store when every surface gives them the
    same signature, so the store label of a record is the tuple of its
    surface signatures.
    """
    counter = counter if counter is not None else OpCounter()
    if not is_warranted(inst):
        return _INDETERMINATE
    if not all(surface_ready(s, inst.records) for s in inst.surfaces):
        return _INDETERMINATE
    tau, sib = _labels_for(inst, counter)
    per_surface = [surface_signatures(s, inst.records, counter) for s in inst.surfaces]
    op: dict[Record, Hashable] = {
        r: tuple(sigs[r] for sigs in per_surface) for r in inst.records
    }
    return compare(inst.records, tau, op, sib)


def audit(inst: Instance, counter: OpCounter | None = None) -> Result:
    """Audit an instance: its single surface, or its store when there are several."""
    if len(inst.surfaces) == 1:
        return audit_surface(inst, inst.surfaces[0], counter)
    return audit_store(inst, counter)
