"""Offline tests: no network calls are made and no API key is required."""
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tripo_3d as t  # noqa: E402

GLB = "https://example.com/model.glb"


def parse(*argv):
    return t.build_parser().parse_args(list(argv))


class PayloadTests(unittest.TestCase):
    def test_text_to_3d_default_model(self):
        payload = t.build_payload(parse("generate", "--prompt", "一只可爱的小猫"))
        self.assertEqual(payload, {"model": "tripo-3d-3.1", "prompt": "一只可爱的小猫"})

    def test_p1_model_selection(self):
        payload = t.build_payload(parse("generate", "--model", "p1", "--prompt", "猫"))
        self.assertEqual(payload["model"], "tripo-3d-p1")

    def test_image_to_3d_uses_input_field(self):
        payload = t.build_payload(parse("generate", "--image", "https://example.com/test.jpg"))
        self.assertEqual(payload, {"model": "tripo-3d-3.1", "input": "https://example.com/test.jpg"})

    def test_multiview_keeps_canonical_order(self):
        payload = t.build_payload(parse("generate", "--views", "back=https://e.com/b.jpg",
                                        "front=https://e.com/f.jpg"))
        self.assertEqual(payload["inputs"], [{"front": "https://e.com/f.jpg"}, {"back": "https://e.com/b.jpg"}])

    def test_exactly_one_source_required(self):
        with self.assertRaises(t.TripoError):
            t.build_payload(parse("generate"))
        with self.assertRaises(t.TripoError):
            t.build_payload(parse("generate", "--prompt", "猫", "--image", "https://e.com/a.jpg"))

    def test_prompt_length_limit(self):
        with self.assertRaises(t.TripoError):
            t.build_payload(parse("generate", "--prompt", "猫" * (t.PROMPT_LIMIT + 1)))

    def test_http_urls_are_rejected(self):
        with self.assertRaises(t.TripoError):
            t.build_payload(parse("generate", "--image", "http://example.com/a.jpg"))
        with self.assertRaises(t.TripoError):
            t.build_payload(parse("rig", "--input", "file:///C:/model.glb"))

    def test_rigging_payload(self):
        payload = t.build_payload(parse("rig", "--input", "https://example.com/char.fbx"))
        self.assertEqual(payload, {"model": "tripo-3d-rigging", "input": "https://example.com/char.fbx"})

    def test_rigging_rejects_unknown_extension(self):
        with self.assertRaises(t.TripoError):
            t.build_payload(parse("rig", "--input", "https://example.com/char.blend"))

    def test_rig_check_requires_glb(self):
        payload = t.build_payload(parse("rig-check", "--input", GLB))
        self.assertEqual(payload, {"model": "tripo-3d-rigging-check", "input": GLB})
        with self.assertRaises(t.TripoError):
            t.build_payload(parse("rig-check", "--input", "https://example.com/m.fbx"))

    def test_animation_payload(self):
        payload = t.build_payload(parse("animate", "--rigged-task-id", "123", "--preset", "walk"))
        self.assertEqual(payload, {"model": "tripo-3d-animation", "input": "123", "animation": "preset:walk"})

    def test_format_uppercases_format(self):
        payload = t.build_payload(parse("format", "--input", "https://example.com/m.obj", "--format", "gltf"))
        self.assertEqual(payload, {"model": "tripo-3d-format", "format": "GLTF", "input": "https://example.com/m.obj"})

    def test_format_rejects_unknown_format(self):
        with self.assertRaises(t.TripoError):
            t.build_payload(parse("format", "--input", GLB, "--format", "USDZ"))


class KeyAndOutputTests(unittest.TestCase):
    def test_dry_run_needs_no_key_and_prints_no_key(self):
        env = {k: v for k, v in os.environ.items() if k != "TOKENHUB_API_KEY"}
        out = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), redirect_stdout(out):
            code = t.main(["generate", "--prompt", "猫", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("tripo-3d-3.1", out.getvalue())
        self.assertNotIn("Bearer", out.getvalue())

    def test_live_call_without_key_fails_cleanly(self):
        env = {k: v for k, v in os.environ.items() if k != "TOKENHUB_API_KEY"}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch("sys.stderr", new=io.StringIO()) as err:
            code = t.main(["generate", "--prompt", "猫"])
        self.assertEqual(code, 2)
        self.assertIn("TOKENHUB_API_KEY", err.getvalue())

    def test_download_urls_found_in_nested_result(self):
        body = {"data": [{"type": "glb", "url": "https://cdn.example.com/a.glb", "preview_image_url": "x"}],
                "meta": {"download_url": "https://cdn.example.com/a.glb"}}
        self.assertEqual(t._download_urls(body), ["https://cdn.example.com/a.glb"])


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class SubmitFlowTests(unittest.TestCase):
    def test_submit_without_wait_returns_job_id(self):
        calls = []

        def fake_urlopen(request, timeout=None):
            calls.append(json.loads(request.data))
            self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
            return FakeResponse(json.dumps({"id": "job-1", "status": "queued"}).encode())

        out = io.StringIO()
        with mock.patch.dict(os.environ, {"TOKENHUB_API_KEY": "test-key"}), \
                mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), redirect_stdout(out):
            code = t.main(["rig", "--input", GLB])
        self.assertEqual(code, 0)
        self.assertEqual(calls, [{"model": "tripo-3d-rigging", "input": GLB}])
        self.assertIn('"job_id": "job-1"', out.getvalue())
        self.assertNotIn("test-key", out.getvalue())


if __name__ == "__main__":
    unittest.main()
