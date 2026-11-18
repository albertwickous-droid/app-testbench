from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from app_testbench.flow import load_flow

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs" / "assets" / "cases"


def _png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", header[16:24])


def _png_chunk_types(path: Path) -> set[bytes]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    offset = 8
    chunk_types: set[bytes] = set()
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_types.add(chunk_type)
        offset += 12 + length
    return chunk_types


def _case_flow(monkeypatch, relative_path: str, package: str | None = None):
    if package is None:
        asset = ROOT / "runs" / "case-assets" / "pinned.apk"
    else:
        asset = ROOT / "runs" / "case-assets" / package / "pinned.apk"
    for name in (
        "ANKIDROID_APK",
        "MARKOR_APK",
        "WIKIPEDIA_APK",
        "FENNEC_APK",
        "VLC_APK",
    ):
        monkeypatch.setenv(name, str(asset))
    monkeypatch.setenv("NOTE_TITLE", "app-testbench-markor")
    monkeypatch.setenv("FENNEC_SITE_URL", "http://127.0.0.1:18765/index.html")
    monkeypatch.setenv("FENNEC_ABOUT_URL", "http://127.0.0.1:18765/about.html")
    monkeypatch.setenv("FENNEC_ORDERS_URL", "http://127.0.0.1:18765/orders.html")
    monkeypatch.setenv("VLC_MEDIA_URL", "http://127.0.0.1:18766/sintel-trailer.mp4")
    return load_flow(ROOT / relative_path)


def test_wikipedia_live_case_covers_research_and_cold_start(monkeypatch) -> None:
    flow = _case_flow(monkeypatch, "examples/wikipedia-research-session/flow.yaml")

    assert flow.name == "wikipedia-research-session"
    assert flow.step_count == 63
    assert flow.device["package"] == "org.wikipedia"

    steps = flow.all_steps
    actions = {step.action for step in steps}
    assert {
        "install",
        "clear_app_data",
        "orientation",
        "launch",
        "wait_for_text",
        "tap_text",
        "text",
        "wait",
        "assert_ui_contains",
        "screenshot",
        "dump_ui",
        "logcat",
        "close",
    } <= actions

    install = next(step for step in steps if step.action == "install")
    assert install.params["expected_package"] == "org.wikipedia"
    assert install.params["expected_version_code"] == 50616
    assert install.params["expected_version_name"] == "r/50616-r-2026-11-03"
    assert sum(step.action == "launch" for step in steps) == 2
    assert any(step.id == "persisted-description-assertion" for step in steps)
    assert all(
        step.params.get("label")
        for step in steps
        if step.action in {"screenshot", "dump_ui", "logcat"}
    )


def test_firefox_live_case_covers_browser_state_download_and_tabs(monkeypatch) -> None:
    flow = _case_flow(monkeypatch, "examples/firefox-webapp-session/flow.yaml")

    assert flow.name == "firefox-webapp-session"
    assert flow.step_count == 66
    assert flow.device["package"] == "org.mozilla.fennec_fdroid"

    steps = flow.all_steps
    actions = {step.action for step in steps}
    assert {
        "install",
        "reverse_port",
        "open",
        "clear_app_data",
        "launch",
        "wait_for_text",
        "tap_text",
        "assert_ui_contains",
        "screenshot",
        "dump_ui",
        "logcat",
        "close",
    } <= actions

    install = next(step for step in steps if step.action == "install")
    assert install.params["expected_package"] == "org.mozilla.fennec_fdroid"
    assert install.params["expected_version_code"] == 1600020
    assert install.params["expected_version_name"] == "160.0.0"
    assert sum(step.action == "launch" for step in steps) == 2
    assert any(step.id == "cookie-localstorage-assertion" for step in steps)
    assert any(step.id == "restored-session-assertion" for step in steps)

    site_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "examples" / "firefox-webapp-session" / "site").rglob("*.html"))
    )
    assert 'type="password"' not in site_text.casefold()
    assert "qa-runner" in site_text
    assert "Cookie + Local Storage" in site_text
    assert 'download="app-testbench-browser-evidence.txt"' in site_text


def test_vlc_live_case_covers_activity_media_logs_and_orientation(monkeypatch) -> None:
    flow = _case_flow(monkeypatch, "examples/vlc-media-playback/flow.yaml")

    assert flow.name == "vlc-media-playback"
    assert flow.step_count == 43
    assert flow.device["package"] == "org.videolan.vlc"

    steps = flow.all_steps
    actions = {step.action for step in steps}
    assert {
        "install",
        "clear_app_data",
        "reverse_port",
        "open",
        "orientation",
        "keyevent",
        "wait_for_activity",
        "assert_logcat_contains",
        "screenshot",
        "dump_ui",
        "logcat",
        "close",
    } <= actions

    install = next(step for step in steps if step.action == "install")
    assert install.params["expected_package"] == "org.videolan.vlc"
    assert install.params["expected_version_code"] == 13070208
    assert install.params["expected_version_name"] == "3.7.2"
    activity_waits = [step for step in steps if step.action == "wait_for_activity"]
    assert activity_waits
    assert all(
        step.params["activity"] == "org.videolan.vlc/.gui.video.VideoPlayerActivity"
        for step in activity_waits
    )
    log_assertions = [
        step.params["text"] for step in steps if step.action == "assert_logcat_contains"
    ]
    assert "Creating an input for 'sintel-trailer.mp4'" in log_assertions
    assert "android_audiotrack" in log_assertions


def test_ankidroid_live_case_covers_real_persistence_journey(monkeypatch) -> None:
    flow = _case_flow(
        monkeypatch,
        "examples/ankidroid-deck-persistence/flow.yaml",
        "ankidroid",
    )

    assert flow.name == "ankidroid-deck-persistence"
    assert flow.step_count == 49
    assert flow.device["package"] == "com.ichi2.anki"

    steps = flow.all_steps
    actions = {step.action for step in steps}
    assert {
        "install",
        "clear_app_data",
        "orientation",
        "launch",
        "wait_for_text",
        "tap_text",
        "text",
        "swipe",
        "tap",
        "screenshot",
        "dump_ui",
        "logcat",
        "close",
        "assert_ui_contains",
    } <= actions

    install = next(step for step in steps if step.action == "install")
    assert install.params["expected_package"] == "com.ichi2.anki"
    assert install.params["expected_version_code"] == 225033004
    assert install.params["expected_version_name"] == "2.25.3"
    assert sum(step.action == "launch" for step in steps) == 2
    assert any(step.params.get("recover_anr") is True for step in steps)
    assert any(step.action == "assert_ui_contains" for step in steps)
    assert all(
        step.params.get("label")
        for step in steps
        if step.action in {"screenshot", "dump_ui", "logcat"}
    )


def test_markor_live_case_covers_file_search_and_persistence(monkeypatch) -> None:
    flow = _case_flow(
        monkeypatch,
        "examples/markor-note-persistence/flow.yaml",
        "markor",
    )

    assert flow.name == "markor-note-persistence"
    assert flow.step_count == 46
    assert flow.device["package"] == "net.gsantner.markor"

    steps = flow.all_steps
    actions = {step.action for step in steps}
    assert {
        "install",
        "launch",
        "wait_for_text",
        "tap_text",
        "clear_text",
        "text",
        "wait",
        "assert_ui_contains",
        "screenshot",
        "dump_ui",
        "logcat",
        "close",
    } <= actions

    install = next(step for step in steps if step.action == "install")
    assert install.params["expected_package"] == "net.gsantner.markor"
    assert install.params["expected_version_code"] == 164
    assert install.params["expected_version_name"] == "2026.10.0"
    assert sum(step.action == "launch" for step in steps) == 2
    assert sum(step.action == "clear_text" for step in steps) == 2
    typed = {step.params.get("text") for step in steps if step.action == "text"}
    assert "app-testbench-markor" in typed
    assert "App TestBench persistence check" in typed
    assert sum(step.action == "assert_ui_contains" for step in steps) == 2


def test_public_example_set_is_intentional() -> None:
    example_dirs = {
        path.name
        for path in (ROOT / "examples").iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }
    assert example_dirs == {
        "ankidroid-deck-persistence",
        "firefox-webapp-session",
        "markor-note-persistence",
        "vlc-media-playback",
        "wikipedia-research-session",
    }


def test_public_case_screenshots_are_real_evidence_with_expected_sizes() -> None:
    expected = {
        CASES / "ankidroid" / "card-filled.png": (720, 1280),
        CASES / "ankidroid" / "persistence.png": (720, 1280),
        CASES / "ankidroid" / "saved-card.png": (720, 1280),
        CASES / "markor" / "note-persisted.png": (720, 1280),
        CASES / "markor" / "note-search.png": (720, 1280),
        CASES / "markor" / "note-reopened.png": (720, 1280),
        CASES / "wikipedia" / "search-results.png": (720, 1280),
        CASES / "wikipedia" / "article.png": (720, 1280),
        CASES / "wikipedia" / "persisted.png": (720, 1280),
        CASES / "firefox" / "session.png": (720, 1280),
        CASES / "firefox" / "orders.png": (720, 1280),
        CASES / "firefox" / "tabs.png": (720, 1280),
        CASES / "firefox" / "download.png": (720, 1280),
        CASES / "vlc" / "tutorial.png": (720, 1280),
        CASES / "vlc" / "player-controls.png": (720, 1280),
        CASES / "vlc" / "landscape.png": (1280, 720),
        CASES / "vlc" / "resumed.png": (1280, 720),
        CASES / "evidence" / "report-failed.png": (1440, 1100),
    }

    for path, dimensions in expected.items():
        assert path.is_file(), path
        assert _png_size(path) == dimensions, path

    actual = {path for path in CASES.rglob("*.png")}
    assert actual == set(expected)


def test_public_pngs_have_no_private_or_embedded_metadata_chunks() -> None:
    forbidden = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"caBX"}
    public_pngs = [
        *CASES.rglob("*.png"),
        *(ROOT / "assets").glob("*.png"),
    ]
    for path in public_pngs:
        assert _png_chunk_types(path).isdisjoint(forbidden), path


def test_public_case_sha256_manifest_matches_files() -> None:
    manifest = (CASES / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    listed: set[str] = set()
    for line in manifest:
        digest, relative = line.split("  ", 1)
        path = CASES / relative
        assert path.is_file(), path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        listed.add(relative)

    actual = {path.relative_to(CASES).as_posix() for path in CASES.rglob("*.png")}
    assert listed == actual
