"""model.py - Shared data model for the finite SE-210 verification cases.

This module represents the information that the paper assumes an auditor has
already supplied.
It does not discover mechanisms, inspect deployed systems,
or establish that the disclosed artifacts, surfaces, or uses are complete.

An :class:`Instance` contains:

- a finite set of records,
- a transformation history connecting those records,
- a declared identity regime,
- an optional sibling regime, and
- an implementation surface with its identity-relevant uses.

The transparent oracle and optimized checker both consume this model.
They share these input types but independently construct relations, partitions,
witnesses, classifications, and verdicts so their results can be compared.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

type Record = str
type Family = str
# Mechanism values are heterogeneous by design (ints, strings, serials,
# tuples), so the value type is Any; it sits only in invariant Mapping-key
# positions where a concrete alias would reject the paper's own examples.
# Hashable is still required at runtime for grouping.
type Value = Any
type Outcome = object


class Cls(Enum):
    """Describe how a transformation family affects an identity basis.

    ``PRS`` means the transformation preserves the basis and therefore joins
    its endpoint records.

    ``BRK`` means the transformation breaks the basis and does not join its
    endpoint records.

    ``NEU`` means the transformation does not act on the basis and is treated
    as nonbreaking.

    ``NA`` means the transformation family does not apply to the carrier kind.

    These values implement Definition 2.1.
    """

    PRS = "PRS"  # preserves the identity basis
    BRK = "BRK"  # breaks it
    NEU = "NEU"  # neutral: does not act on the basis
    NA = "N/A"  # inapplicable to the carrier kind


#: Non-breaking classifications, Definition 2.2: PRS and NEU both yield edges.
NON_BREAKING: frozenset[Cls] = frozenset({Cls.PRS, Cls.NEU})


@dataclass(frozen=True)
class Regime:
    """Describe one declared rule of sameness.

    ``name`` identifies the regime.

    ``classify`` maps every transformation family used in the supplied history
    to its effect on this regime's identity basis.

    ``sibling`` names the alternative regime used for sibling-relative
    classification. It is None when the regime has no defined sibling.
    """

    name: str
    classify: Mapping[Family, Cls]
    sibling: str | None = None

    def cls(self, f: Family) -> Cls:
        """Return this regime's classification of a transformation family.

        A missing family indicates malformed supplied data because the
        classification function must cover every family occurring in the
        instance history.
        """
        try:
            return self.classify[f]
        except KeyError as exc:  # pragma: no cover - guards malformed input
            msg = f"regime {self.name!r} has no classification for family {f!r}"
            raise KeyError(msg) from exc


@dataclass(frozen=True)
class Surface:
    """Describe one disclosed implementation mechanism and its identified uses.

    ``value`` maps each record to the mechanism value observed for that record.

    ``uses`` contains the identity-relevant uses of that mechanism. Each use is
    represented as a table from mechanism values to outcomes. Records with the
    same mechanism value therefore receive the same outcome from every use,
    making each use a function of the mechanism value by construction.

    A record's complete identity-treatment signature is the ordered tuple of
    outcomes produced by these uses.

    This represents the supplied audit surface of Definition 3.8.
    """

    name: str
    value: Mapping[Record, Value]
    uses: Sequence[Mapping[Value, Outcome]]

    def signature(self, r: Record) -> tuple[Outcome, ...]:
        """Return the complete identity-treatment signature for one record.

        The record's mechanism value is found first.
        Each identified use is then applied to that value,
        and the resulting outcomes are returned
        in the same order as ``uses``.
        """
        v = self.value[r]
        return tuple(use[v] for use in self.uses)


@dataclass(frozen=True)
class Instance:
    """Contain all supplied data required to audit one carrier kind.

    ``records`` is the finite record domain.

    ``history`` contains transformation-family edges between records.

    ``tau`` is the declared identity regime being audited.

    ``surface`` is the implementation mechanism and identified-use family
    whose operational treatment is compared with the declaration.

    ``sib`` is the optional sibling regime used to classify a detected
    divergence.

    ``label`` is a human-readable name for tests and diagnostic output.
    """

    records: tuple[Record, ...]
    history: tuple[tuple[Family, Record, Record], ...]
    tau: Regime
    surface: Surface
    sib: Regime | None = None
    label: str = ""

    def __post_init__(self) -> None:
        """Reject malformed supplied audit data.

        Records must be unique, every history endpoint must belong to the
        record domain, the surface must define a value for every record, and
        any supplied sibling regime must match the sibling named by the
        declared regime.
        """
        rset = set(self.records)
        if len(rset) != len(self.records):
            msg = "records must be distinct"
            raise ValueError(msg)
        for _, x, y in self.history:
            if x not in rset or y not in rset:
                msg = "history endpoint outside R (Assumption 5.1c)"
                raise ValueError(msg)
        for r in self.records:
            if r not in self.surface.value:
                msg = f"surface value undefined on record {r!r}"
                raise ValueError(msg)
        if self.sib is not None and self.tau.sibling != self.sib.name:
            msg = "sib regime name does not match tau.sibling"
            raise ValueError(msg)


class Verdict(Enum):
    """Report whether the supplied implementation is faithful to the declaration.

    ``PASS`` means the implementation does not split any declared identity
    class.

    ``FAIL`` means at least one pair of records declared to be the same
    receives different identity treatment.

    The broader audit may also report an indeterminate outcome when disclosure
    or completeness preconditions cannot be established.
    That outcome is not represented here because
    every verification instance is fully supplied by construction.
    """

    PASS = "pass"  # noqa: S105
    FAIL = "fail"
    # `indeterminate` is a disclosure/precondition outcome, out of scope for
    # this core check: every Instance here is well-formed by construction.


class Kind(Enum):
    """Classify a failed audit relative to the declared regime's sibling.

    ``ALIGNED`` means the implementation and sibling make exactly the same
    distinctions inside the declared identity classes.

    ``SUB`` means the implementation makes all sibling distinctions and also
    makes additional distinctions.

    ``SUPER`` means the implementation makes some but not all sibling
    distinctions.

    ``INCOMPARABLE`` means each makes at least one distinction the other does
    not make.

    ``UNPOSITIONED`` means no informative sibling-relative comparison is
    available.

    ``NONE`` is used when the audit passes and no divergence classification is
    needed.

    These values implement Definition 4.8 and its residual case.
    """

    ALIGNED = "sibling-aligned"
    SUB = "sub-sibling"
    SUPER = "super-sibling"
    INCOMPARABLE = "sibling-incomparable"
    UNPOSITIONED = "unpositioned"
    NONE = "none"  # no classification (verdict is pass)


@dataclass(frozen=True)
class Result:
    """Contain the result returned by either checker.

    ``verdict`` reports whether the implementation is faithful.

    ``kind`` gives the sibling-relative divergence classification when the
    audit fails.

    ``substitution`` reports whether the implementation relation equals the
    sibling relation across the entire record domain.

    ``witness`` contains one pair that the declaration merges but the
    implementation separates.
    Different correct checkers may return different valid witnesses,
    so this field is excluded from dataclass equality.
    """

    verdict: Verdict
    kind: Kind
    substitution: bool
    witness: tuple[Record, Record] | None = field(default=None, compare=False)

    def key(self) -> tuple[str, str, bool]:
        """Return the fields that must agree between independent checkers.

        The witness is excluded because more than one record pair may
        demonstrate the same failure.
        """
        return (self.verdict.value, self.kind.value, self.substitution)


def nonbreaking_edges(inst: Instance, regime: Regime) -> list[tuple[Record, Record]]:
    """Return the history edges that preserve identity under a regime.

    An edge is included when its transformation family is classified as
    preserving or neutral under the supplied regime.
    These edges generate the regime declared identity relation
    through equivalence closure.

    This implements Definition 2.2.
    """
    return [(x, y) for (f, x, y) in inst.history if regime.cls(f) in NON_BREAKING]
