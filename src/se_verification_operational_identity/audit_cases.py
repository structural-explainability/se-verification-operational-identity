"""audit_cases.py - Regression cases taken from the revised SE-210 paper.

Every case stipulates which steps are licensed.
The stipulations follow the paper's examples (Remark ``oi.rem.norefine`` and
Example ``oi.ex.loc-obj-fork``).
They are assumptions of the examples, not a rule that a family label licenses
a step.
:func:`generated` is the single place where a per-family stipulation is turned
into a licensed set, and a family absent from the table is not licensed.

Cases are tagged with the paper label they exercise.
Numbers are not used because they change between revisions.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from .audit_model import (
    Family,
    Generated,
    Instance,
    Kind,
    Record,
    Result,
    Step,
    Supplied,
    Surface,
    Verdict,
    Warrant,
    identity_surface,
    surface_from_tables,
)


@dataclass(frozen=True)
class Case:
    """One instance with the result the paper asserts for it."""

    paper: str
    inst: Instance
    verdict: Verdict
    kind: Kind
    substitution: bool

    def expected(self) -> tuple[str, str, bool]:
        """Return the expected result key."""
        return (self.verdict.value, self.kind.value, self.substitution)


def generated(
    history: tuple[Step, ...], stipulation: Mapping[Family, bool]
) -> Generated:
    """Build a generated relation from a per-family stipulation of licences.

    A step is licensed exactly when its family is stipulated licensed.
    A family missing from the stipulation is not licensed.
    """
    licensed = frozenset(s for s in history if stipulation.get(s.family, False))
    return Generated(history, licensed)


def steps(*triples: tuple[Family, Record, Record]) -> tuple[Step, ...]:
    """Build a history from ``(family, source, target)`` triples."""
    return tuple(Step(f, x, y) for f, x, y in triples)


# Stipulated licences for the rule carrier kind (Remark oi.rem.norefine).
RULE_C: Mapping[Family, bool] = {
    "refine-structure": True,
    "revise-wording": True,
    "amend-content": False,
}
RULE_S: Mapping[Family, bool] = {
    "refine-structure": False,
    "revise-wording": True,
    "amend-content": True,
}
# Stipulated licences for the locus/object axis (oi.ex.loc-obj-fork).
LOC: Mapping[Family, bool] = {"BF": True}
OBJ: Mapping[Family, bool] = {"BF": False}


def _case(
    paper: str,
    inst: Instance,
    want: tuple[Verdict, Kind, bool],
) -> Case:
    return Case(paper, inst, want[0], want[1], want[2])


def _rule_instance(
    label: str,
    records: tuple[Record, ...],
    history: tuple[Step, ...],
    surface: Surface,
) -> Instance:
    return Instance(
        records=records,
        declared=generated(history, RULE_C),
        sibling=generated(history, RULE_S),
        surfaces=(surface,),
        label=label,
    )


def cases() -> tuple[Case, ...]:
    """Return every single-instance regression case."""
    r3 = ("r0", "r1", "r2")
    r4 = ("r0", "r1", "r2", "r3")
    out: list[Case] = []

    out.append(
        _case(
            "oi.prop.refutes (faithful)",
            _rule_instance(
                "faithful: empty history",
                r3,
                (),
                identity_surface("d", {"r0": 0, "r1": 1, "r2": 2}),
            ),
            (Verdict.PASS, Kind.NONE, False),
        )
    )
    out.append(
        _case(
            "oi.def.classification (unpositioned)",
            Instance(
                records=("r0", "r1"),
                declared=generated(steps(("g", "r0", "r1")), {"g": True}),
                surfaces=(identity_surface("d", {"r0": 0, "r1": 1}),),
                label="unpositioned: no sibling",
            ),
            (Verdict.FAIL, Kind.UNPOSITIONED, False),
        )
    )
    out.append(
        _case(
            "oi.ex.loc-obj-fork",
            Instance(
                records=r3,
                declared=generated(steps(("BF", "r0", "r1"), ("BF", "r0", "r2")), LOC),
                sibling=generated(steps(("BF", "r0", "r1"), ("BF", "r0", "r2")), OBJ),
                surfaces=(
                    identity_surface("sensor", {"r0": "s0", "r1": "s1", "r2": "s2"}),
                ),
                label="fork: substitution with a witness",
            ),
            (Verdict.FAIL, Kind.ALIGNED, True),
        )
    )
    out.append(
        _case(
            "oi.prop.substitution-witness (supplied relations)",
            Instance(
                records=("r0", "r1"),
                declared=Supplied((frozenset({"r0", "r1"}),)),
                sibling=Supplied((frozenset({"r0"}), frozenset({"r1"}))),
                surfaces=(identity_surface("d", {"r0": 0, "r1": 1}),),
                label="substitution with a witness, supplied partitions",
            ),
            (Verdict.FAIL, Kind.ALIGNED, True),
        )
    )
    out.append(
        _case(
            "oi.rem.merging-substitution",
            Instance(
                records=("r0", "r1"),
                declared=generated(steps(("amend-content", "r0", "r1")), RULE_C),
                sibling=generated(steps(("amend-content", "r0", "r1")), RULE_S),
                surfaces=(identity_surface("d", {"r0": 0, "r1": 0}),),
                label="substitution with a PASS",
            ),
            (Verdict.PASS, Kind.NONE, True),
        )
    )
    h4 = steps(
        ("refine-structure", "r0", "r1"),
        ("revise-wording", "r0", "r2"),
        ("amend-content", "r0", "r3"),
    )
    out.append(
        _case(
            "oi.prop.aligned-not-substitution",
            _rule_instance(
                "aligned without substitution",
                r4,
                h4,
                identity_surface("d", {"r0": 0, "r2": 0, "r1": 1, "r3": 1}),
            ),
            (Verdict.FAIL, Kind.ALIGNED, False),
        )
    )
    h_sub = steps(("refine-structure", "r0", "r1"), ("revise-wording", "r0", "r2"))
    out.append(
        _case(
            "oi.prop.witness-not-alignment",
            _rule_instance(
                "sub-sibling",
                r3,
                h_sub,
                identity_surface("d", {"r0": 0, "r1": 1, "r2": 2}),
            ),
            (Verdict.FAIL, Kind.SUB, False),
        )
    )
    out.append(
        _case(
            "oi.sec.worked (ruleTextVersion)",
            _rule_instance(
                "worked example: ruleTextVersion",
                r3,
                h_sub,
                identity_surface("ruleTextVersion", {"r0": 1, "r1": 2, "r2": 3}),
            ),
            (Verdict.FAIL, Kind.SUB, False),
        )
    )
    out.append(
        _case(
            "oi.rem.nonvacuity (super-sibling)",
            _rule_instance(
                "super-sibling",
                r3,
                steps(
                    ("refine-structure", "r0", "r1"), ("refine-structure", "r0", "r2")
                ),
                identity_surface("d", {"r0": 0, "r1": 0, "r2": 1}),
            ),
            (Verdict.FAIL, Kind.SUPER, False),
        )
    )
    out.append(
        _case(
            "oi.rem.nonvacuity (sibling-incomparable)",
            _rule_instance(
                "sibling-incomparable",
                r4,
                steps(
                    ("revise-wording", "r0", "r1"),
                    ("refine-structure", "r0", "r2"),
                    ("revise-wording", "r2", "r3"),
                ),
                identity_surface("d", {"r0": 0, "r2": 0, "r1": 1, "r3": 1}),
            ),
            (Verdict.FAIL, Kind.INCOMPARABLE, False),
        )
    )
    out.append(
        _case(
            "oi.rem.neutral",
            Instance(
                records=("r0", "r1"),
                declared=generated(
                    steps(("neutral-op", "r0", "r1")), {"neutral-op": False}
                ),
                surfaces=(identity_surface("d", {"r0": 0, "r1": 1}),),
                label="a neutral step licenses nothing",
            ),
            (Verdict.PASS, Kind.NONE, False),
        )
    )
    two = steps(("f", "r0", "r1"), ("f", "r1", "r2"))
    out.append(
        _case(
            "oi.def.nonbreaking (unlicensed step ignored)",
            Instance(
                records=r3,
                declared=Generated(two, frozenset({two[0]})),
                surfaces=(identity_surface("d", {"r0": 0, "r1": 0, "r2": 1}),),
                label="only the licensed step joins records",
            ),
            (Verdict.PASS, Kind.NONE, False),
        )
    )
    out.extend(_indeterminate_cases())
    return tuple(out)


def _indeterminate_cases() -> list[Case]:
    """Return cases whose preconditions are not established."""
    pair = ("r0", "r1")
    history = steps(("f", "r0", "r1"))
    unwarranted = Warrant(licences_warranted=False)
    indet = (Verdict.INDETERMINATE, Kind.NONE, False)
    faithful_surface = identity_surface("d", {"r0": 0, "r1": 0})
    failing_surface = identity_surface("d", {"r0": 0, "r1": 1})
    out: list[Case] = []
    for label, surface in (
        ("unwarranted licences, surface would pass", faithful_surface),
        ("unwarranted licences, surface would fail", failing_surface),
    ):
        out.append(
            _case(
                "oi.rem.precond",
                Instance(
                    records=pair,
                    declared=generated(history, {"f": True}),
                    surfaces=(surface,),
                    warrant=unwarranted,
                    label=label,
                ),
                indet,
            )
        )
    out.append(
        _case(
            "oi.rem.precond (licences irrelevant for a supplied relation)",
            Instance(
                records=pair,
                declared=Supplied((frozenset(pair),)),
                surfaces=(faithful_surface,),
                warrant=unwarranted,
                label="supplied relation needs no licence warrant",
            ),
            (Verdict.PASS, Kind.NONE, False),
        )
    )
    out.append(
        _case(
            "oi.rem.precond (other preconditions)",
            Instance(
                records=pair,
                declared=Supplied((frozenset(pair),)),
                surfaces=(faithful_surface,),
                warrant=Warrant(mapping_justified=False),
                label="unjustified implementation mapping",
            ),
            indet,
        )
    )
    uncontrolled = Surface(
        "uncontrolled",
        {"r0": 0, "r1": 0},
        ({"r0": "a", "r1": "b"},),
    )
    out.append(
        _case(
            "oi.def.surface (surface control)",
            Instance(
                records=pair,
                declared=Supplied((frozenset(pair),)),
                surfaces=(uncontrolled,),
                label="use does not factor through the mechanism",
            ),
            indet,
        )
    )
    partial = Surface("partial", {"r0": 0, "r1": 1}, ({"r0": "a"},))
    out.append(
        _case(
            "oi.rem.record-indexed",
            Instance(
                records=pair,
                declared=Supplied((frozenset(pair),)),
                surfaces=(partial,),
                label="outcome not computable for a record",
            ),
            indet,
        )
    )
    return out


def nonmonotone_pair() -> tuple[Instance, Instance]:
    """Return the before and after instances of ``oi.prop.nonmonotone``.

    With the empty history the surface is faithful.
    Two licensed steps are then added.
    The surface, records, and signatures are unchanged.
    """
    surface = identity_surface("d", {"r": 0, "s": 1, "t": 2})
    extended = steps(("f", "r", "t"), ("g", "t", "s"))
    before = Instance(
        records=("r", "s", "t"),
        declared=Generated((), frozenset()),
        surfaces=(surface,),
        label="nonmonotone: before",
    )
    after = Instance(
        records=("r", "s", "t"),
        declared=Generated(extended, frozenset(extended)),
        surfaces=(surface,),
        label="nonmonotone: after",
    )
    return before, after


def omitted_surface_example() -> tuple[Instance, Surface]:
    """Return a store that passes and a joint surface that splits a declared class.

    Two mechanisms are exclusive-or related, and the use that matters factors
    through their pair and through neither alone
    (Definition ``oi.def.omittedsurface``).
    The examined surfaces carry only constant uses, so each passes.
    """
    records = ("r0", "r1", "r2", "r3")
    d1 = {"r0": 0, "r1": 0, "r2": 1, "r3": 1}
    d2 = {"r0": 0, "r1": 1, "r2": 0, "r3": 1}
    constant = [dict.fromkeys((0, 1), "c")]
    s1 = surface_from_tables("d1", d1, constant)
    s2 = surface_from_tables("d2", d2, constant)
    joint_value = {r: (d1[r], d2[r]) for r in records}
    parity = {(a, b): (a + b) % 2 for a in (0, 1) for b in (0, 1)}
    joint = surface_from_tables("d1+d2", joint_value, [parity])
    inst = Instance(
        records=records,
        declared=Supplied(
            (frozenset({"r0", "r1"}), frozenset({"r2"}), frozenset({"r3"}))
        ),
        surfaces=(s1, s2),
        label="omitted joint surface",
    )
    return inst, joint


def result_matches(case: Case, result: Result) -> bool:
    """Return whether a result equals the case's expected key."""
    return result.key() == case.expected()
