#!/usr/bin/env python3
"""Serve a directory with byte-range support for deterministic media tests."""

from __future__ import annotations

import argparse
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


class RangeRequestHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def send_head(self):
        path = Path(self.translate_path(self.path))
        if not path.is_file():
            return super().send_head()

        file_size = path.stat().st_size
        range_header = self.headers.get("Range")
        if not range_header:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", self.guess_type(str(path)))
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            return path.open("rb")

        match = RANGE_RE.fullmatch(range_header.strip())
        if not match:
            self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, "Invalid Range header")
            return None
        start_text, end_text = match.groups()
        if not start_text and not end_text:
            self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, "Empty Range")
            return None
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else file_size - 1
        else:
            suffix_length = int(end_text)
            start = max(0, file_size - suffix_length)
            end = file_size - 1
        if start >= file_size or end < start:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.end_headers()
            return None
        end = min(end, file_size - 1)
        length = end - start + 1

        stream = path.open("rb")
        stream.seek(start)
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Content-Length", str(length))
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return _LimitedReader(stream, length)


class _LimitedReader:
    def __init__(self, stream, remaining: int) -> None:
        self.stream = stream
        self.remaining = remaining

    def read(self, size: int = -1) -> bytes:
        if self.remaining <= 0:
            return b""
        if size < 0 or size > self.remaining:
            size = self.remaining
        data = self.stream.read(size)
        self.remaining -= len(data)
        return data

    def close(self) -> None:
        self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18766)
    args = parser.parse_args()
    directory = args.directory.expanduser().resolve()
    if not directory.is_dir():
        raise SystemExit(f"Directory does not exist: {directory}")

    def handler(*handler_args, **handler_kwargs):
        return RangeRequestHandler(*handler_args, directory=str(directory), **handler_kwargs)

    server = ThreadingHTTPServer((args.bind, args.port), handler)
    print(f"Serving {directory} at http://{args.bind}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
