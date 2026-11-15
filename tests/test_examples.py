from __future__ import annotations

import struct
from pathlib import Path

from app_testbench.flow import load_flow

ROOT = Path(__file__).resolve().parents[1]


def _png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", header[16:24])


def test_markor_live_case_flow_is_reproducible(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MARKOR_APK", str(tmp_path / "net.gsantner.markor_164.apk"))
    monkeypatch.setenv("NOTE_TITLE", "app-testbench-persistence-test")

    flow = load_flow(ROOT / "examples" / "markor-note-persistence" / "flow.yaml")

    assert flow.name == "markor-note-persistence"
    assert flow.step_count == 47
    actions = [step.action for step in [*flow.setup, *flow.steps, *flow.teardown]]
    assert "install" in actions
    assert "text" in actions
    assert "assert_ui_contains" in actions
    assert "dump_ui" in actions


def test_settings_live_case_flow_covers_scroll_and_back() -> None:
    flow = load_flow(ROOT / "examples" / "settings-network-scroll" / "flow.yaml")

    assert flow.name == "settings-network-scroll"
    assert flow.step_count == 23
    actions = [step.action for step in [*flow.setup, *flow.steps, *flow.teardown]]
    assert actions.count("swipe") >= 6
    assert "back" in actions
    assert "wait_for_text" in actions


def test_public_case_screenshots_exist_with_expected_dimensions() -> None:
    app_assets = [
        ROOT / "docs" / "assets" / "cases" / "markor" / "note-saved.png",
        ROOT / "docs" / "assets" / "cases" / "markor" / "note-search.png",
        ROOT / "docs" / "assets" / "cases" / "markor" / "note-reopened.png",
        ROOT / "docs" / "assets" / "cases" / "settings" / "network.png",
        ROOT / "docs" / "assets" / "cases" / "settings" / "scrolled-list.png",
    ]
    report_assets = [
        ROOT / "docs" / "assets" / "cases" / "markor" / "report-passed.png",
        ROOT / "docs" / "assets" / "cases" / "markor" / "report-passed-dark.png",
        ROOT / "docs" / "assets" / "cases" / "settings" / "report-failed.png",
        ROOT / "docs" / "assets" / "cases" / "settings" / "report-failed-dark.png",
    ]

    for path in app_assets:
        assert path.is_file(), path
        assert _png_size(path) == (1280, 720)
    for path in report_assets:
        assert path.is_file(), path
        assert _png_size(path) == (1440, 1100)
