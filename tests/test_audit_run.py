"""The command-line harness passes and can emit the Lean vectors."""

from pathlib import Path

from se_verification_operational_identity.audit_check import run
from se_verification_operational_identity.audit_lean import emit_vectors


def test_harness_passes(capsys: object, tmp_path: Path) -> None:
    target = tmp_path / "Vectors.lean"
    assert run(300, 0, False, target) == 0
    assert target.read_text(encoding="utf-8") == emit_vectors()
