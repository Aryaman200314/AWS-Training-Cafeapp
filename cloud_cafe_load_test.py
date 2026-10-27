#!/usr/bin/env python3
"""A small, bounded HTTP load generator for your Cloud Cafe training ALB.

Requires Python 3.10+; uses only the Python standard library.
Run this on your laptop, not on the application EC2 instances.

Windows PowerShell:
    py cloud_cafe_load_test.py --url http://Cafe-Demo-SLB-1143506718.us-east-1.elb.amazonaws.com --rps 500 --users 100 --minutes 2
    py cloud_cafe_load_test.py --url http://Cafe-Demo-SLB-1143506718.us-east-1.elb.amazonaws.com --rps 1 --users 1 --minutes 10

Ubuntu: use python3 instead of py.

The default target is 500 requests per second TOTAL across all users, not per
user. Requests are paced evenly rather than sent in one batch each second.
Each user handles one request at a time; --users controls concurrency. Actual
throughput can be lower if responses or the load-generating computer are slow.
Ctrl+C stops the test. It also stops automatically after the specified duration.
Maximums: 500 requests/second, 500 users, and 60 minutes.
This script does not install anything or change your application or AWS setup.

Suggested lab ASG: minimum=1, desired=1, maximum=2; target tracking using
ALBRequestCountPerTarget with target=300 (requests per target per minute).
Select the application's target group. Allow time for monitoring, policy
evaluation, EC2 startup, and target health checks. These settings demonstrate
the scaling mechanism; 300 is a teaching value, not measured server capacity.

For scale-in practice, use --rps 1 --users 1 and keep that low traffic running so
CloudWatch keeps receiving data. Scale-in can take longer than scale-out.
"""

import argparse
import concurrent.futures
import threading
import time
import urllib.error
import urllib.parse
import urllib.request


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", required=True, help="Your application's ALB URL")
    parser.add_argument("--rps", type=int, default=500,
                        help="Total target requests per second, 1-500 (default: 500)")
    parser.add_argument("--users", type=int, default=100,
                        help="Concurrent simulated users, 1-500 (default: 100)")
    parser.add_argument("--minutes", type=float, default=10,
                        help="Test duration in minutes, >0 and <=60 (default: 10)")
    args = parser.parse_args(argv)
    parsed = urllib.parse.urlsplit(args.url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        parser.error("--url must be an absolute http:// or https:// URL")
    if parsed.username is not None or parsed.password is not None:
        parser.error("Use a URL without embedded login credentials")
    if not 1 <= args.rps <= 500:
        parser.error("--rps must be between 1 and 500")
    if not 1 <= args.users <= 500:
        parser.error("--users must be between 1 and 500")
    if not 0 < args.minutes <= 60:
        parser.error("--minutes must be greater than 0 and at most 60")

    stop = threading.Event()
    lock = threading.Lock()
    counts = {"sent": 0, "total": 0, "ok": 0, "failed": 0, "latency": 0.0, "last_error": ""}
    started = time.monotonic()
    deadline = started + args.minutes * 60
    rate_lock = threading.Lock()
    next_request = started
    request_interval = 1.0 / args.rps

    def user():
        nonlocal next_request
        while not stop.is_set() and time.monotonic() < deadline:
            # Reserve one slot on a shared schedule. Workers do not each get
            # their own 500 RPS allowance. Idle time never builds up credits.
            with rate_lock:
                scheduled = max(time.monotonic(), next_request)
                if scheduled >= deadline:
                    return
                next_request = scheduled + request_interval
            if stop.wait(max(0, scheduled - time.monotonic())):
                return
            if time.monotonic() >= deadline:
                return

            request_started = time.monotonic()
            with lock:
                counts["sent"] += 1
            success = False
            error = ""
            request = urllib.request.Request(args.url, headers={
                "User-Agent": "CloudCafeTrainingLoadTest/1.0",
                "Cache-Control": "no-cache",
            })
            try:
                with urllib.request.urlopen(request, timeout=5) as response:
                    response.read(1024 * 1024)
                    success = 200 <= response.status < 400
                    if not success:
                        error = "HTTP " + str(response.status)
            except urllib.error.HTTPError as exc:
                error = "HTTP " + str(exc.code)
                exc.close()
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                error = str(exc)[:180]
            with lock:
                counts["total"] += 1
                counts["ok"] += int(success)
                counts["failed"] += int(not success)
                counts["latency"] += time.monotonic() - request_started
                if error:
                    counts["last_error"] = error

    print("Cloud Cafe load test: %d users, %.1f minutes" % (args.users, args.minutes), flush=True)
    print("Target request rate: %d/second (%d/minute), shared across all users." %
          (args.rps, args.rps * 60), flush=True)
    print("Actual throughput depends on response times and available concurrency.", flush=True)
    print("Press Ctrl+C to stop. Watch ALB metrics and ASG Activity in AWS.", flush=True)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=args.users)
    futures = [pool.submit(user) for _ in range(args.users)]
    previous_time, previous_sent, previous_total = started, 0, 0
    interrupted = False
    try:
        while time.monotonic() < deadline:
            stop.wait(min(5, max(0, deadline - time.monotonic())))
            now = time.monotonic()
            with lock:
                snapshot = counts.copy()
            rps = (snapshot["total"] - previous_total) / max(now - previous_time, 0.001)
            sent_rps = (snapshot["sent"] - previous_sent) / max(now - previous_time, 0.001)
            print("%5.0fs | Sent/sec: %5.1f | Completed/sec: %5.1f | Total: %5d | OK: %5d | Failed: %d" %
                  (now - started, sent_rps, rps, snapshot["total"], snapshot["ok"], snapshot["failed"]), flush=True)
            previous_time, previous_sent, previous_total = now, snapshot["sent"], snapshot["total"]
            if all(future.done() for future in futures):
                break
    except KeyboardInterrupt:
        interrupted = True
        print("\nStopping; waiting for in-flight requests...", flush=True)
    finally:
        stop.set()
        pool.shutdown(wait=True)

    worker_errors = [future.exception() for future in futures if future.exception() is not None]
    elapsed = time.monotonic() - started
    average_rps = counts["total"] / max(elapsed, 0.001)
    average_ms = 1000 * counts["latency"] / max(counts["total"], 1)
    print("Finished | OK: %d | Failed: %d | Average: %.1f requests/sec | Mean response: %.0f ms" %
          (counts["ok"], counts["failed"], average_rps, average_ms), flush=True)
    if counts["last_error"]:
        print("Last request error:", counts["last_error"], flush=True)
    if worker_errors:
        print("Worker error:", str(worker_errors[0])[:180], flush=True)
    return 130 if interrupted else int(bool(counts["failed"] or worker_errors))


if __name__ == "__main__":
    raise SystemExit(main())
