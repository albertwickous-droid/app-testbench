from __future__ import annotations

from pathlib import Path

import yaml


def load_workflow(root: Path, name: str) -> dict:
    return yaml.safe_load((root / ".github" / "workflows" / name).read_text(encoding="utf-8"))


def test_github_release_does_not_depend_on_pypi() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = load_workflow(root, "release.yml")

    assert set(workflow["jobs"]) == {"verify", "build", "github-release"}
    release_job = workflow["jobs"]["github-release"]
    assert release_job["permissions"]["contents"] == "write"
    release_step = next(
        step
        for step in release_job["steps"]
        if step.get("uses") == "softprops/action-gh-release@v2"
    )
    assert release_step["with"]["tag_name"] == "${{ github.ref_name }}"
    assert release_step["with"]["draft"] is True
    assert release_step["with"]["body_path"] == "docs/releases/${{ github.ref_name }}.md"
    assert release_step["with"]["fail_on_unmatched_files"] is True


def test_pypi_publish_is_manual_and_uses_trusted_publishing() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = load_workflow(root, "publish-pypi.yml")
    trigger = workflow[True]
    publish = workflow["jobs"]["publish"]

    assert "workflow_dispatch" in trigger
    assert publish["environment"]["name"] == "pypi"
    assert publish["permissions"]["contents"] == "read"
    assert publish["permissions"]["id-token"] == "write"
    assert publish["if"] == "inputs.confirm == 'PUBLISH'"


def test_release_version_metadata_matches() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    package_init = (root / "src" / "app_testbench" / "__init__.py").read_text(encoding="utf-8")

    assert 'version = "0.1.1"' in pyproject
    assert '__version__ = "0.1.1"' in package_init
