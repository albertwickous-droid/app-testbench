from __future__ import annotations

import hashlib
import importlib.util
import struct
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from app_testbench.flow import load_flow

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs" / "assets" / "cases"


def _png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", header[16:24])


def _load_range_server_module():
    path = ROOT / "examples" / "vlc-http-playback" / "range_server.py"
    spec = importlib.util.spec_from_file_location("app_testbench_range_server", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fennec_live_case_covers_browser_state_and_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FENNEC_APK", str(tmp_path / "pinned-fennec.apk"))
    monkeypatch.setenv("FENNEC_SITE_URL", "http://127.0.0.1:18765/")

    flow = load_flow(ROOT / "examples" / "fennec-local-web-session" / "flow.yaml")

    assert flow.name == "fennec-local-web-session"
    assert flow.step_count == 71
    actions = [step.action for step in [*flow.setup, *flow.steps, *flow.teardown]]
    for action in {
        "reverse_port",
        "install",
        "clear_app_data",
        "orientation",
        "open",
        "text",
        "wait_for_text",
        "assert_ui_contains",
        "assert_ui_not_contains",
        "screenshot",
        "dump_ui",
        "logcat",
    }:
        assert action in actions


def test_vlc_live_case_covers_media_decode_and_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VLC_APK", str(tmp_path / "pinned-vlc.apk"))
    monkeypatch.setenv("VLC_MEDIA_URL", "http://127.0.0.1:18766/sintel-trailer.mp4?case=test")

    flow = load_flow(ROOT / "examples" / "vlc-http-playback" / "flow.yaml")

    assert flow.name == "vlc-http-playback"
    assert flow.step_count == 30
    actions = [step.action for step in [*flow.setup, *flow.steps, *flow.teardown]]
    for action in {"reverse_port", "clear_app_data", "orientation", "open", "screenshot", "logcat"}:
        assert action in actions


def test_fennec_fixture_has_unique_repository_owned_site_marker() -> None:
    site = (ROOT / "examples" / "fennec-local-web-session" / "site" / "index.html").read_text(
        encoding="utf-8"
    )

    assert "FieldDesk QA Console" in site
    assert "qa@example.test" in site
    assert "demo123" in site


def test_vlc_range_server_returns_exact_partial_content(tmp_path: Path) -> None:
    module = _load_range_server_module()
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"x" * 32)
    handler = partial(module.RangeRequestHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/clip.mp4",
            headers={"Range": "bytes=0-15"},
        )
        with urlopen(request, timeout=5) as response:
            assert response.status == 206
            assert response.headers["Content-Range"] == "bytes 0-15/32"
            assert response.read() == b"x" * 16
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_public_case_screenshots_are_real_evidence_with_expected_sizes() -> None:
    expected = {
        CASES / "fennec" / "first-run.png": (720, 1280),
        CASES / "fennec" / "dashboard.png": (720, 1132),
        CASES / "fennec" / "search-result.png": (720, 1132),
        CASES / "fennec" / "detail.png": (720, 1132),
        CASES / "fennec" / "session-restored.png": (720, 1132),
        CASES / "fennec" / "logged-out.png": (720, 1132),
        CASES / "fennec" / "report-passed.png": (1440, 1100),
        CASES / "vlc" / "welcome.png": (1280, 720),
        CASES / "vlc" / "home.png": (1280, 720),
        CASES / "vlc" / "tutorial.png": (1280, 720),
        CASES / "vlc" / "playback-controls.png": (1280, 720),
        CASES / "evidence" / "report-failed.png": (1440, 1100),
    }

    for path, dimensions in expected.items():
        assert path.is_file(), path
        assert _png_size(path) == dimensions, path


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
