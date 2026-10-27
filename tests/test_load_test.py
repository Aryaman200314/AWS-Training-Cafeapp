"""Verify request pacing with fake responses; never send traffic to AWS."""

import contextlib
import io
import math
import threading
import time
import unittest
from unittest.mock import patch

import cloud_cafe_load_test


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return b"OK"


class LoadTestChecks(unittest.TestCase):
    def run_fake_test(self, options, response_delay=0):
        calls = []
        lock = threading.Lock()
        output = io.StringIO()

        def fake_urlopen(request, timeout):
            with lock:
                calls.append(time.monotonic())
            time.sleep(response_delay)
            return FakeResponse()

        with patch.object(cloud_cafe_load_test.urllib.request, "urlopen", side_effect=fake_urlopen):
            with contextlib.redirect_stdout(output):
                result = cloud_cafe_load_test.main(["--url", "http://example.invalid", *options])
        self.assertEqual(result, 0, output.getvalue())
        return calls, output.getvalue()

    def test_default_500_rps_is_shared_across_workers(self):
        duration = 1.2
        calls, output = self.run_fake_test(["--minutes", str(duration / 60), "--users", "20"], 0.005)
        self.assertIn("Target request rate: 500/second (30000/minute)", output)
        # A single global rate limit must hold despite concurrent fake requests.
        self.assertLessEqual(len(calls), math.ceil(500 * duration) + 1)
        self.assertGreater(len(calls), 100)
        self.assertGreater(max(calls) - min(calls), 0.8)
        self.assertIn("Sent/sec:", output)
        self.assertIn("Completed/sec:", output)

    def test_custom_rate_does_not_send_all_requests_at_once(self):
        calls, output = self.run_fake_test(["--rps", "20", "--users", "10", "--minutes", "0.02"])
        self.assertLessEqual(len(calls), 25)
        self.assertGreater(len(calls), 5)
        self.assertGreater(max(calls) - min(calls), 0.8)
        self.assertIn("Target request rate: 20/second", output)

    def test_slow_responses_reduce_throughput_without_a_request_backlog(self):
        calls, _ = self.run_fake_test(["--rps", "500", "--users", "1", "--minutes", "0.01"], 0.15)
        self.assertGreaterEqual(len(calls), 1)
        self.assertLessEqual(len(calls), 5)

    def test_invalid_rate_is_rejected_without_network_calls(self):
        for rate in ("0", "-1", "501"):
            with self.subTest(rate=rate):
                with patch.object(cloud_cafe_load_test.urllib.request, "urlopen") as request:
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as error:
                            cloud_cafe_load_test.main(["--url", "http://example.invalid", "--rps", rate])
                    self.assertEqual(error.exception.code, 2)
                    request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
