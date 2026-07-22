"""paper_cases.py - Regression cases taken from SE-210, Operational Identity.

Each case supplies a small record system together with the verdict,
classification, and regime-substitution result asserted by the paper.

The examples use these transformation-family classifications:

    refine-structure : preserves identity under RULE-C but breaks it under RULE-S
    revise-wording   : preserves identity under both RULE-C and RULE-S
    amend-content    : breaks identity under RULE-C but preserves it under RULE-S
    BF (branch/fork) : preserves identity under LOC but breaks it under OBJ
"""

from .model import Cls, Instance, Kind, Regime, Surface, Verdict

# === rule carrier kind: RULE-C declared, RULE-S sibling ===

_RULE_FAMILIES_C = {
    "refine-structure": Cls.PRS,
    "revise-wording": Cls.PRS,
    "amend-content": Cls.BRK,
}
_RULE_FAMILIES_S = {
    "refine-structure": Cls.BRK,
    "revise-wording": Cls.PRS,
    "amend-content": Cls.PRS,
}


def _rule_c() -> Regime:
    return Regime("RULE-C", _RULE_FAMILIES_C, sibling="RULE-S")


def _rule_s() -> Regime:
    return Regime("RULE-S", _RULE_FAMILIES_S, sibling="RULE-C")


def _ident_use(values: dict[str, object]) -> Surface:
    """Create a surface whose reported identity outcome is its stored value.

    Records with the same supplied value receive the same outcome.
    Records with different supplied values receive different outcomes.
    """
    table = {v: v for v in set(values.values())}
    return Surface("d", values, [table])


# === LOC/OBJ carrier kind ===

_LOC = Regime("LOC", {"BF": Cls.PRS}, sibling="OBJ")
_OBJ = Regime("OBJ", {"BF": Cls.BRK}, sibling="LOC")


def case_faithful_pass() -> tuple[Instance, Verdict, Kind, bool]:  # type: ignore
    """Return a simple passing audit.

    The empty history leaves every record in its own declared identity class.
    Because no declared class contains two different records, the surface
    cannot split a declared class, regardless of its three distinct outcomes.

    The audit therefore passes, has no divergence classification, and does
    not exhibit regime substitution.
    """
    inst = Instance(
        records=("r0", "r1", "r2"),
        history=(),  # empty history: ~_tau is identity, three singletons
        tau=_rule_c(),
        sib=_rule_s(),
        surface=_ident_use({"r0": 0, "r1": 1, "r2": 2}),
        label="faithful/pass",
    )
    return inst, Verdict.PASS, Kind.NONE, False


def case_unpositioned_no_sibling() -> tuple[Instance, Verdict, Kind, bool]:
    """Return a failure that cannot be compared with a sibling regime.

    The declared regime treats r0 and r1 as the same because transformation g
    preserves identity.
    The implementation treats them as different, so the
    surface splits a declared identity class and the audit fails.

    Because this regime has no sibling basis, the divergence cannot be placed
    relative to a sibling and is classified as unpositioned.
    """
    tau = Regime("NEU-KIND", {"g": Cls.PRS}, sibling=None)
    inst = Instance(
        records=("r0", "r1"),
        history=(("g", "r0", "r1"),),  # merges the pair under tau
        tau=tau,
        sib=None,
        surface=_ident_use({"r0": 0, "r1": 1}),  # surface splits it
        label="unpositioned (no sibling)",
    )
    return inst, Verdict.FAIL, Kind.UNPOSITIONED, False


def case_sibling_aligned_substitution() -> tuple[Instance, Verdict, Kind, bool]:
    """Return the sibling-aligned substitution example from Example 4.11.

    The declared location-based regime treats each branch or fork as
    preserving the same item.
    The object-based sibling treats the resulting
    records as different objects.

    The sensor-serial implementation makes exactly the same distinctions as
    the object-based sibling,
    both inside the declared class and across the entire record domain.

    The audit therefore fails with sibling-aligned divergence, and the
    implementation exhibits regime substitution by carrying the sibling
    partition globally.
    """
    inst = Instance(
        records=("r0", "r1", "r2"),
        history=(("BF", "r0", "r1"), ("BF", "r0", "r2")),
        tau=_LOC,
        sib=_OBJ,
        surface=_ident_use({"r0": "s0", "r1": "s1", "r2": "s2"}),  # follows OBJ
        label="sibling-aligned + substitution (Ex. 4.11)",
    )
    return inst, Verdict.FAIL, Kind.ALIGNED, True


def case_aligned_without_substitution() -> tuple[Instance, Verdict, Kind, bool]:
    """Return the aligned-without-substitution case from Proposition 4.14.

    Inside each class created by the declared content-based regime, the
    implementation makes exactly the same distinctions as the structure-based
    sibling. The divergence is therefore sibling-aligned.

    Outside those declared classes, however, the implementation and sibling
    treat some records differently. Their complete partitions are not equal,
    so sibling alignment does not establish regime substitution.
    """
    inst = Instance(
        records=("r0", "r1", "r2", "r3"),
        history=(
            ("refine-structure", "r0", "r1"),
            ("revise-wording", "r0", "r2"),
            ("amend-content", "r0", "r3"),
        ),
        tau=_rule_c(),
        sib=_rule_s(),
        surface=_ident_use({"r0": 0, "r2": 0, "r1": 1, "r3": 1}),
        label="aligned without substitution (Prop. 4.14)",
    )
    return inst, Verdict.FAIL, Kind.ALIGNED, False


def case_sub_sibling_worked() -> tuple[Instance, Verdict, Kind, bool]:
    """Return the version-counter example from Proposition 4.15 and Section 6.

    The declared content-based regime treats all three records as the same
    rule. The structure-based sibling separates the structural refinement but
    still merges the wording revision with the original rule.

    The version counter assigns a different value to every record, so the
    implementation separates more pairs than either regime. The audit fails
    and classifies the divergence as sub-sibling.

    Because the implementation partition is not equal to the sibling
    partition, regime substitution does not hold.
    """
    inst = Instance(
        records=("r0", "r1", "r2"),
        history=(
            ("refine-structure", "r0", "r1"),
            ("revise-wording", "r0", "r2"),
        ),
        tau=_rule_c(),
        sib=_rule_s(),
        surface=_ident_use({"r0": 0, "r1": 1, "r2": 2}),  # distinct per record
        label="sub-sibling (Prop. 4.15 / worked example)",
    )
    return inst, Verdict.FAIL, Kind.SUB, False


def case_super_sibling() -> tuple[Instance, Verdict, Kind, bool]:
    """Return the super-sibling example from Remark 4.16(c).

    The declared content-based rule treats all three records as the same rule.
    The structure-based sibling treats all three records as different.
    The implementation takes a middle position:
    it treats r0 and r1 as the same, but treats r2 as different.

    The implementation therefore makes fewer distinctions than the sibling,
    but more distinctions than the declared rule.
    The audit fails and classifies the divergence as super-sibling.
    """
    inst = Instance(
        records=("r0", "r1", "r2"),
        history=(
            ("refine-structure", "r0", "r1"),
            ("refine-structure", "r0", "r2"),
        ),
        tau=_rule_c(),
        sib=_rule_s(),
        surface=_ident_use({"r0": 0, "r1": 0, "r2": 1}),
        label="super-sibling (Rem. 4.16c)",
    )
    return inst, Verdict.FAIL, Kind.SUPER, False


def case_incomparable() -> tuple[Instance, Verdict, Kind, bool]:
    """Return the sibling-incomparable example from Remark 4.16(d).

    The declared content-based regime treats all four records as the same
    rule.

    The structure-based sibling groups r0 with r1 and groups r2 with r3.
    The implementation instead groups r0 with r2 and groups r1 with r3.

    Each relation merges a pair that the other separates.
    Neither set of distinctions contains the other,
    so the audit fails and classifies the divergence as sibling-incomparable.
    """
    inst = Instance(
        records=("r0", "r1", "r2", "r3"),
        history=(
            ("revise-wording", "r0", "r1"),
            ("refine-structure", "r0", "r2"),
            ("revise-wording", "r2", "r3"),
        ),
        tau=_rule_c(),
        sib=_rule_s(),
        surface=_ident_use({"r0": 0, "r2": 0, "r1": 1, "r3": 1}),
        label="sibling-incomparable (Rem. 4.16d)",
    )
    return inst, Verdict.FAIL, Kind.INCOMPARABLE, False


def cases() -> list[tuple[Instance, Verdict, Kind, bool]]:
    """Return all single-instance regression cases from the paper.

    Each tuple contains the supplied instance, expected audit verdict,
    expected divergence classification, and expected substitution flag.
    """
    return [
        case_faithful_pass(),
        case_unpositioned_no_sibling(),
        case_sibling_aligned_substitution(),
        case_aligned_without_substitution(),
        case_sub_sibling_worked(),
        case_super_sibling(),
        case_incomparable(),
    ]


# === history-extension monotonicity (Prop. 5.5): returned as a pair ===


def monotonicity_pair() -> tuple[Instance, Instance]:
    """Return the before-and-after instances from Proposition 5.5.

    Before the history is extended, the declared regime leaves r, s, and t
    in separate identity classes.
    The surface is therefore faithful and the audit passes.

    After two identity-preserving transformations are added, transitive
    closure places r, t, and s in one declared class.
    The surface outcomes remain unchanged and
    still distinguish all three records, so the newly
    merged declared class is split and the audit fails.

    The example shows that extending the history alone can change a passing
    verdict to a failing one without changing the records, surface, or
    operational signatures.
    """
    surface = _ident_use({"r": 0, "s": 1, "t": 2})
    tau = Regime("MON", {"f": Cls.PRS, "g": Cls.PRS}, sibling=None)
    before = Instance(
        records=("r", "s", "t"),
        history=(),
        tau=tau,
        sib=None,
        surface=surface,
        label="Prop. 5.5 before (empty history)",
    )
    after = Instance(
        records=("r", "s", "t"),
        history=(("f", "r", "t"), ("g", "t", "s")),
        tau=tau,
        sib=None,
        surface=surface,
        label="Prop. 5.5 after (r ~ s via closure)",
    )
    return before, after
