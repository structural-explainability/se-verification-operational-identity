"""The three derivations of the audit share no semantic code.

The model module holds data only.
Each checker may import its data classes and nothing that computes
licences, signatures, relations, or verdicts from another checker.
"""

import ast
from pathlib import Path

import pytest

PACKAGE = (
    Path(__file__).resolve().parents[1] / "src" / "se_verification_operational_identity"
)
CHECKERS = ("audit_oracle", "audit_fast", "audit_edges")
DATA_NAMES = {
    "Declared",
    "Family",
    "Generated",
    "Hashable",
    "Instance",
    "Kind",
    "Outcome",
    "Record",
    "Result",
    "Step",
    "Supplied",
    "Surface",
    "Value",
    "Verdict",
    "Warrant",
}


def _local_imports(module: str) -> dict[str, set[str]]:
    tree = ast.parse((PACKAGE / f"{module}.py").read_text(encoding="utf-8"))
    found: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            found.setdefault(node.module or "", set()).update(
                a.name for a in node.names
            )
    return found


@pytest.mark.parametrize("module", CHECKERS)
def test_checker_imports_only_data_from_the_model(module: str) -> None:
    imports = _local_imports(module)
    assert set(imports) <= {"audit_model"}, f"{module} imports {sorted(imports)}"
    assert imports.get("audit_model", set()) <= DATA_NAMES


def test_model_defines_no_audit_logic() -> None:
    tree = ast.parse((PACKAGE / "audit_model.py").read_text(encoding="utf-8"))
    functions = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert functions <= {"_check_relation", "surface_from_tables", "identity_surface"}
