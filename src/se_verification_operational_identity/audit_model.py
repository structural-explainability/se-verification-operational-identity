"""audit_model.py - Pure data model for the revised SE-210 finite audit.

This module holds only data.
It contains no licence evaluation, signature computation, relation
construction, or comparison logic.
Each checker derives everything it needs from these raw values,
so a defect in one derivation cannot be shared with the other.

An :class:`Instance` supplies what the paper assumes an auditor already has:

- a finite record domain,
- a declared identity relation, either supplied directly as a partition
  or generated from a history of individually licensed steps,
- an optional alternative (sibling) relation of the same two forms,
- one or more examined surfaces, each with a mechanism and identified uses, and
- a warrant recording whether the audit preconditions are established.

A family label never licenses a step.
Only membership of a step in the supplied licensed set does
(Remark ``oi.rem.neutral``).
"""

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

type Record = str
type Family = str
type Value = Hashable
type Outcome = Hashable


@dataclass(frozen=True)
class Step:
    """One performed transformation step of a history.

    ``family`` is the transformation family label.
    ``source`` and ``target`` are the records the step connects.
    """

    family: Family
    source: Record
    target: Record


@dataclass(frozen=True)
class Supplied:
    """A declared relation supplied directly as a partition of the records.

    ``blocks`` are pairwise disjoint and together cover the record domain.
    """

    blocks: tuple[frozenset[Record], ...]


@dataclass(frozen=True)
class Generated:
    """A declared relation generated from licensed history steps.

    ``history`` is the performed sequence of steps.
    ``licensed`` is the set of steps independently licensed as identity
    continuations.
    A step contributes an edge only when it belongs to ``licensed``.
    """

    history: tuple[Step, ...]
    licensed: frozenset[Step]


type Declared = Supplied | Generated


@dataclass(frozen=True)
class Surface:
    """One examined implementation surface.

    ``value`` maps every record to its mechanism value and must be total.

    ``uses`` are the identified identity-relevant uses.
    Each use maps records to outcomes.
    A use may be partial, in which case the outcome cannot be computed for
    the missing records and the audit is indeterminate.
    Surface control (each use factors through the mechanism value) is a
    property the checkers test, and it is not guaranteed by construction.
    """

    name: str
    value: Mapping[Record, Value]
    uses: tuple[Mapping[Record, Outcome], ...]


@dataclass(frozen=True)
class Warrant:
    """Record which audit preconditions are established.

    The four fields correspond to the preconditions of Definition
    ``oi.def.precond``.
    ``licences_warranted`` matters only when a relation is generated.
    """

    declared_valid: bool = True
    licences_warranted: bool = True
    mapping_justified: bool = True
    scope_bounded: bool = True


@dataclass(frozen=True)
class Instance:
    """All supplied data needed to audit one record domain.

    ``surfaces`` is the examined surface family, with at least one surface.
    ``sibling`` is the optional supplied alternative relation.
    """

    records: tuple[Record, ...]
    declared: Declared
    surfaces: tuple[Surface, ...]
    sibling: Declared | None = None
    warrant: Warrant = field(default_factory=Warrant)
    label: str = ""

    def __post_init__(self) -> None:
        """Reject malformed supplied data.

        Records must be distinct, at least one surface must be present,
        every relation must be well formed on the records,
        and every mechanism value map must be total.
        Missing outcomes are not malformed.
        They make the audit indeterminate.
        """
        rset = set(self.records)
        if len(rset) != len(self.records):
            msg = "records must be distinct"
            raise ValueError(msg)
        if not self.surfaces:
            msg = "at least one surface is required"
            raise ValueError(msg)
        for relation in (self.declared, self.sibling):
            if relation is not None:
                _check_relation(relation, rset)
        for surface in self.surfaces:
            if set(surface.value) != rset:
                msg = f"mechanism value of {surface.name!r} must be total on R"
                raise ValueError(msg)
            for use in surface.uses:
                if not set(use) <= rset:
                    msg = f"use of {surface.name!r} mentions a record outside R"
                    raise ValueError(msg)


def _check_relation(relation: Declared, rset: set[Record]) -> None:
    """Raise ValueError unless the relation is well formed on ``rset``."""
    if isinstance(relation, Supplied):
        covered: set[Record] = set()
        for block in relation.blocks:
            if not block or covered & block:
                msg = "supplied blocks must be nonempty and disjoint"
                raise ValueError(msg)
            covered |= block
        if covered != rset:
            msg = "supplied blocks must cover exactly the records"
            raise ValueError(msg)
    else:
        for step in relation.history:
            if step.source not in rset or step.target not in rset:
                msg = "history endpoint outside R"
                raise ValueError(msg)


def surface_from_tables(
    name: str,
    value: Mapping[Record, Value],
    tables: Sequence[Mapping[Any, Outcome]],  # key type is invariant in Mapping
) -> Surface:
    """Build a surface whose uses factor through the mechanism value.

    Each table maps mechanism values to outcomes.
    The resulting use sends a record to the table entry of its value, so
    surface control holds for the result.
    """
    uses = tuple({r: table[v] for r, v in value.items()} for table in tables)
    return Surface(name, dict(value), uses)


def identity_surface(name: str, value: Mapping[Record, Value]) -> Surface:
    """Build a surface with one use that reports the mechanism value itself."""
    return surface_from_tables(name, value, [{v: v for v in set(value.values())}])


class Verdict(Enum):
    """The three audit outcomes.

    ``PASS``: preconditions established and the surface splits no declared class.

    ``FAIL``: preconditions established and a declared class is split.

    ``INDETERMINATE``: a precondition, surface control, or an outcome is not
    established.
    It is never a pass.
    """

    PASS = "pass"
    FAIL = "fail"
    INDETERMINATE = "indeterminate"


class Kind(Enum):
    """Position of a failed audit relative to the supplied alternative.

    ``NONE`` is used when the audit passes or is indeterminate.
    ``UNPOSITIONED`` is used when no sibling is supplied or the sibling
    splits no declared class.
    """

    ALIGNED = "sibling-aligned"
    SUB = "sub-sibling"
    SUPER = "super-sibling"
    INCOMPARABLE = "sibling-incomparable"
    UNPOSITIONED = "unpositioned"
    NONE = "none"


@dataclass(frozen=True)
class Result:
    """The outcome of one audit.

    ``substitution`` reports extensional equality of the operational and
    alternative partitions when the regimes differ.
    It is independent of ``verdict``, so substitution can hold with a PASS.

    ``witness`` is excluded from equality because several pairs can witness
    the same failure.
    """

    verdict: Verdict
    kind: Kind
    substitution: bool
    witness: tuple[Record, Record] | None = field(default=None, compare=False)

    def key(self) -> tuple[str, str, bool]:
        """Return the fields on which independent checkers must agree."""
        return (self.verdict.value, self.kind.value, self.substitution)
