#!/usr/bin/env python3
"""Tripo-3D clients for Tencent TokenHub (Python standard library only).

Models (all submitted to /v1/api/3d/submit, polled with /v1/api/3d/query):
  tripo-3d-3.1        text / image / multi-view -> 3D model (high fidelity, up to 2M polygons)
  tripo-3d-p1         text / image / multi-view -> 3D model (low-poly oriented)
  tripo-3d-rigging    3D model -> rigged model (skeleton)
  tripo-3d-rigging-check  3D GLB -> rigging suitability + recommended skeleton type
  tripo-3d-animation  rigged model task id + preset animation -> animated model
  tripo-3d-format     3D model -> other format (GLTF/GLB/FBX/OBJ/STL)

The API key is read from the TOKENHUB_API_KEY environment variable only. It is never
printed, never written to disk, and never accepted as a command-line argument.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://tokenhub.tencentmaas.com"
SUBMIT_PATH = "/v1/api/3d/submit"
QUERY_PATH = "/v1/api/3d/query"
PROMPT_LIMIT = 1024
MODEL_IDS = {
    "3.1": "tripo-3d-3.1",
    "p1": "tripo-3d-p1",
    "rigging": "tripo-3d-rigging",
    "rigging-check": "tripo-3d-rigging-check",
    "animation": "tripo-3d-animation",
    "format": "tripo-3d-format",
}
VIEWS = ("front", "left", "back", "right")
FORMATS = ("GLTF", "GLB", "FBX", "OBJ", "STL")
MODEL_INPUT_FORMATS = ("GLB", "GLTF", "FBX", "OBJ", "STL")
DONE_STATES = {"completed", "succeeded", "success", "done"}
FAILED_STATES = {"failed", "error", "cancelled", "canceled"}


class TripoError(Exception):
    """Raised for invalid input or API failures; the message never contains the key."""


def _https_url(value: str, label: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise TripoError(f"{label} must be a public https:// URL (got {value!r})")
    return value


def _model_input_url(value: str) -> str:
    _https_url(value, "input model")
    suffix = Path(urllib.parse.urlparse(value).path).suffix.lower().lstrip(".")
    if suffix and suffix.upper() not in MODEL_INPUT_FORMATS:
        raise TripoError(f"input model extension .{suffix} is not one of {', '.join(MODEL_INPUT_FORMATS)}")
    return value


def build_payload(args: argparse.Namespace) -> dict:
    """Return the JSON body for a submit call. Pure function: no network, no key."""
    command = args.command
    if command == "generate":
        model = MODEL_IDS[args.model]
        if args.prompt is not None:
            if not args.prompt.strip():
                raise TripoError("--prompt must not be empty")
            if len(args.prompt) > PROMPT_LIMIT:
                raise TripoError(f"--prompt is limited to {PROMPT_LIMIT} characters")
        sources = [args.prompt is not None, args.image is not None, bool(args.views)]
        if sum(sources) != 1:
            raise TripoError("choose exactly one of --prompt, --image or --views")
        payload = {"model": model}
        if args.prompt is not None:
            payload["prompt"] = args.prompt
        elif args.image is not None:
            payload["input"] = _https_url(args.image, "--image")
        else:
            views = {}
            for item in args.views:
                view, _, url = item.partition("=")
                if view not in VIEWS or not url:
                    raise TripoError(f"--views entries must look like front=URL (views: {', '.join(VIEWS)})")
                if view in views:
                    raise TripoError(f"duplicate view {view!r}")
                views[view] = _https_url(url, f"--views {view}")
            payload["inputs"] = [{view: views[view]} for view in VIEWS if view in views]
        return payload

    if command == "rig":
        return {"model": MODEL_IDS["rigging"], "input": _model_input_url(args.input)}

    if command == "rig-check":
        url = _https_url(args.input, "--input")
        if Path(urllib.parse.urlparse(url).path).suffix.lower() != ".glb":
            raise TripoError("rig-check accepts GLB files only")
        return {"model": MODEL_IDS["rigging-check"], "input": url}

    if command == "animate":
        if not args.rigged_task_id.strip():
            raise TripoError("--rigged-task-id must not be empty")
        return {"model": MODEL_IDS["animation"], "input": args.rigged_task_id,
                "animation": f"preset:{args.preset}"}

    if command == "format":
        fmt = args.format.upper()
        if fmt not in FORMATS:
            raise TripoError(f"--format must be one of {', '.join(FORMATS)}")
        return {"model": MODEL_IDS["format"], "format": fmt,
                "input": _model_input_url(args.input)}

    raise TripoError(f"no payload for command {command!r}")


def _api_key() -> str:
    key = os.environ.get("TOKENHUB_API_KEY", "").strip()
    if not key:
        raise TripoError("TOKENHUB_API_KEY is not set in this process environment")
    return key


def _post(path: str, body: dict, timeout: int) -> dict:
    request = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise TripoError(f"HTTP {exc.code} from {path}: {detail}") from None
    except urllib.error.URLError as exc:
        raise TripoError(f"network error calling {path}: {exc.reason}") from None
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise TripoError(f"non-JSON response from {path}") from None
    error = body.get("error") if isinstance(body, dict) else None
    if error:
        raise TripoError(f"API error from {path}: {json.dumps(error, ensure_ascii=False)[:500]}")
    return body


def _job_id(body: dict) -> str:
    for key in ("id", "task_id", "job_id"):
        if body.get(key):
            return str(body[key])
    raise TripoError("submit response has no job id; raw keys: " + ", ".join(sorted(body)))


def _status(body: dict) -> str:
    return str(body.get("status") or body.get("Status") or "UNKNOWN").lower()


def _download_urls(body: dict) -> list[str]:
    urls: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("url", "download_url") and isinstance(value, str) and value.startswith("https://"):
                    urls.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(body)
    return list(dict.fromkeys(urls))


def download(url: str, output_dir: Path) -> Path:
    name = Path(urllib.parse.urlparse(url).path).name or "download.bin"
    target = output_dir / name
    with urllib.request.urlopen(url, timeout=300) as response, open(target, "wb") as handle:
        while chunk := response.read(1 << 20):
            handle.write(chunk)
    return target


def wait_for(model: str, job_id: str, interval: float, timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    while True:
        body = _post(QUERY_PATH, {"model": model, "id": job_id}, timeout=60)
        state = _status(body)
        print(f"job {job_id}: {state}", file=sys.stderr)
        if state in DONE_STATES:
            return body
        if state in FAILED_STATES:
            raise TripoError(f"job {job_id} ended with status {state}")
        if time.monotonic() > deadline:
            raise TripoError(f"job {job_id} still running after {timeout:.0f}s; resume with: "
                             f"query --model {model} --id {job_id}")
        time.sleep(interval)


def _print(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def run(args: argparse.Namespace) -> int:
    if args.command == "query":
        model = MODEL_IDS[args.model]
        body = _post(QUERY_PATH, {"model": model, "id": args.id}, timeout=60)
        _print(body)
        return 0

    payload = build_payload(args)
    if args.dry_run:
        _print({"provider": "tokenhub", "method": "POST", "url": BASE_URL + SUBMIT_PATH, "payload": payload})
        return 0

    body = _post(SUBMIT_PATH, payload, timeout=120)
    job_id = _job_id(body)
    print(f"submitted job {job_id} ({payload['model']})", file=sys.stderr)
    if not args.wait:
        _print({"job_id": job_id, "model": payload["model"], "submit_response": body})
        return 0

    final = wait_for(payload["model"], job_id, args.poll_interval, args.wait_timeout)
    urls = _download_urls(final)
    saved = []
    if args.output_dir and urls:
        out = Path(args.output_dir) / job_id
        out.mkdir(parents=True, exist_ok=True)
        saved = [str(download(url, out)) for url in urls]
    _print({"job_id": job_id, "model": payload["model"], "status": _status(final),
            "downloaded": saved, "result_urls": urls, "response": final})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tripo-3D via Tencent TokenHub")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, wait=True):
        p.add_argument("--dry-run", action="store_true", help="print the request without calling the API")
        if wait:
            p.add_argument("--wait", action="store_true", help="poll until done, then download results")
            p.add_argument("--poll-interval", type=float, default=10.0)
            p.add_argument("--wait-timeout", type=float, default=1800.0)
            p.add_argument("--output-dir", help="directory for downloaded results")

    g = sub.add_parser("generate", help="text/image/multi-view to 3D (3.1 or p1)")
    g.add_argument("--model", choices=("3.1", "p1"), default="3.1")
    g.add_argument("--prompt", help="Chinese or English prompt, up to 1024 characters")
    g.add_argument("--image", help="public https image URL (JPEG/PNG, 256x256 to 20MB)")
    g.add_argument("--views", nargs="+", metavar="VIEW=URL", help="front/left/back/right image URLs")
    common(g)

    r = sub.add_parser("rig", help="add a skeleton to a 3D model")
    r.add_argument("--input", required=True, help="public https URL of GLB/GLTF/FBX/OBJ/STL")
    common(r)

    c = sub.add_parser("rig-check", help="check whether a GLB can be rigged")
    c.add_argument("--input", required=True, help="public https URL of a GLB file")
    common(c, wait=True)

    a = sub.add_parser("animate", help="apply a preset animation to a rigged model")
    a.add_argument("--rigged-task-id", required=True, help="task id of a finished rigging job")
    a.add_argument("--preset", default="walk", help="preset name, e.g. walk (see guide.md)")
    common(a)

    f = sub.add_parser("format", help="convert a 3D model to another format")
    f.add_argument("--input", required=True, help="public https URL of GLB/GLTF/FBX/OBJ/STL (<=150MB)")
    f.add_argument("--format", default="GLTF", help="GLTF, GLB, FBX, OBJ or STL")
    common(f)

    q = sub.add_parser("query", help="query an existing job by id")
    q.add_argument("--model", required=True, choices=sorted(MODEL_IDS), help="model key, e.g. 3.1 or rigging")
    q.add_argument("--id", required=True)
    q.add_argument("--dry-run", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except TripoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
