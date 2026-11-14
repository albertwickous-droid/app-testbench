from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGAL_NOTICES = (
    "DISCLAIMER.md",
    "RESPONSIBLE_USE.md",
    "PRIVACY.md",
    "THIRD_PARTY_NOTICES.md",
)


def test_legal_notices_exist_and_are_distributed() -> None:
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    for name in LEGAL_NOTICES:
        path = ROOT / name
        assert path.is_file(), f"missing legal notice: {name}"
        assert path.read_text(encoding="utf-8").strip(), f"empty legal notice: {name}"
        assert f"include {name}" in manifest, f"legal notice missing from sdist: {name}"
        assert f'"{name}"' in pyproject, f"legal notice missing from wheel metadata: {name}"
