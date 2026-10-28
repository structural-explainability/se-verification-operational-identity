"""The Lean vector generator is deterministic and covers every distinct result."""

from se_verification_operational_identity.audit_lean import emit_vectors


def test_emission_is_deterministic() -> None:
    assert emit_vectors() == emit_vectors()


def test_every_verdict_and_position_is_emitted() -> None:
    text = emit_vectors()
    for token in (
        "Verdict.pass",
        "Verdict.fail",
        "theorem v001_verdict",
        "Aligned",
        "SubSibling",
        "SuperSibling",
        "SiblingIncomparable",
        "¬ Substitution",
    ):
        assert token in text, token
    assert "sorry" not in text
