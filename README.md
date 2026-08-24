# Performance & Load Testing — ReqRes.in API

A Locust-based performance test suite against the [ReqRes.in](https://reqres.in) demo API, covering Load Testing, Stress Testing, and a realistic end-to-end user flow — plus custom pass/fail thresholds so a run can gate a CI pipeline like a functional test suite does.

## Design note: Load vs. Stress testing

This project deliberately does **not** duplicate the test logic for "load" and "stress." In Locust, both are the same simulated user behavior — the only thing that changes is scale (`-u` user count, `-r` spawn rate). Writing separate scripts for each would just be the same code twice with different numbers. Instead, `locustfile.py` defines one realistic `ApiUser`, and the two scenarios are two different **run configurations** against it (see commands below).

## The simulated user flow

`ApiUser` behaves like a real client:

1. **Logs in once** (`on_start`) and stores the returned token
2. Waits a **random 1–3 seconds** between every action (`wait_time = between(1, 3)`), like a real person reading a page before clicking again
3. Randomly picks weighted tasks:
   - `browse_user_list` (weight 5) — most traffic is reads
   - `view_single_user` (weight 3)
   - `submit_new_record` (weight 1) — writes are rarer than reads

## Custom Thresholds

`utils/thresholds.py` hooks into Locust's `quitting` event and fails the run (non-zero exit code) if, across the whole run:

- the **average response time exceeds 500ms**, or
- the **error rate exceeds 1%**

This is what makes the suite usable as an automated performance gate, not just a manual reporting tool.

## Project Structure

```
performance-load-testing/
├── locustfile.py        Locust entry point — the ApiUser behavior
├── utils/
│   └── thresholds.py    custom pass/fail thresholds (response time & error rate)
├── reports/              generated CSV/HTML reports land here (gitignored)
└── requirements.txt
```

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

**Load Testing** — steady 50–100 concurrent users:
```bash
locust -f locustfile.py --headless -u 100 -r 10 --run-time 2m \
    --csv=reports/load --html=reports/load.html
```

**Stress Testing** — ramp up to 500+ users to find the breaking point:
```bash
locust -f locustfile.py --headless -u 500 -r 50 --run-time 3m \
    --csv=reports/stress --html=reports/stress.html
```

**Interactive mode** (web UI, set user count/spawn rate yourself):
```bash
locust -f locustfile.py
# open http://localhost:8089
```

> Note: ReqRes.in is a shared public demo API. Start with small numbers (e.g. `-u 20`) before running the full 500-user stress scenario, out of courtesy to a service other people are also using for free.

## Reading the reports

- **`reports/*.html`** — the easiest to read. Open it in a browser: it has a summary table (requests, failures, average/median/percentile response times per endpoint) and interactive charts of RPS and response time over the run.
- **`reports/*_stats.csv`** — one row per endpoint with request count, failure count, and response time percentiles (50/66/75/80/90/95/98/99%). Good for pulling numbers into a spreadsheet or another dashboard.
- **`reports/*_stats_history.csv`** — a time series snapshot (every few seconds) of the run, useful for plotting how response times and RPS changed as more users ramped up — this is what shows a stress test "breaking point" if there is one.
- **`reports/*_failures.csv`** — every distinct error, with a count. Empty file = zero failures.
- **Console output** — at the very end of any headless run, look for either:
  - `Thresholds passed: X% errors, Yms avg response time`, or
  - `THRESHOLD FAILED: ...` (and the process exits with code `1`)
