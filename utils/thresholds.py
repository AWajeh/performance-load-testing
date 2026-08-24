"""Custom pass/fail thresholds for Locust.

By default, Locust doesn't "fail" a run just because response times were slow —
it just reports the numbers. This module hooks into Locust's `quitting` event
(fired once, right before the process exits) to turn those numbers into a real
pass/fail verdict: if the average response time or the error rate crosses a
threshold, the process exits with a non-zero code — exactly what you want if
this is ever wired into a CI pipeline as a performance gate.
"""

from locust import events

MAX_RESPONSE_TIME_MS = 500
MAX_ERROR_RATE_PERCENT = 1.0


@events.quitting.add_listener
def enforce_thresholds(environment, **kwargs):
    stats = environment.stats.total

    if stats.num_requests == 0:
        print("No requests were made — skipping threshold checks.")
        return

    error_rate = (stats.num_failures / stats.num_requests) * 100
    avg_response_time = stats.avg_response_time

    failed = False

    if error_rate > MAX_ERROR_RATE_PERCENT:
        print(
            f"THRESHOLD FAILED: error rate {error_rate:.2f}% "
            f"exceeds the {MAX_ERROR_RATE_PERCENT}% limit"
        )
        failed = True

    if avg_response_time > MAX_RESPONSE_TIME_MS:
        print(
            f"THRESHOLD FAILED: avg response time {avg_response_time:.0f}ms "
            f"exceeds the {MAX_RESPONSE_TIME_MS}ms limit"
        )
        failed = True

    if failed:
        environment.process_exit_code = 1
    else:
        print(
            f"Thresholds passed: {error_rate:.2f}% errors, "
            f"{avg_response_time:.0f}ms avg response time"
        )
