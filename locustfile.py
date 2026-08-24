"""Load / Stress / E2E-flow test suite against the ReqRes.in demo API.

The user behavior defined below (log in, browse, occasionally submit — with a
random 1-3s pause between actions, like a real person) is the SAME for both
Load and Stress testing. In Locust, "load" vs "stress" isn't different code —
it's the same behavior run at a different scale:

    Load Testing (steady 50-100 concurrent users):
        locust -f locustfile.py --headless -u 100 -r 10 --run-time 2m \
            --csv=reports/load --html=reports/load.html

    Stress Testing (ramp up to 500+ users to find the breaking point):
        locust -f locustfile.py --headless -u 500 -r 50 --run-time 3m \
            --csv=reports/stress --html=reports/stress.html

    Interactive mode (with the web UI):
        locust -f locustfile.py
        # then open http://localhost:8089 and set user count / spawn rate there
"""

import random

from locust import HttpUser, task, between

from utils import thresholds  # noqa: F401  (importing registers the threshold hooks)


class ApiUser(HttpUser):
    """A realistic end-to-end user: log in once, then repeatedly browse data and
    occasionally submit a new record, pausing 1-3 seconds between actions.
    """

    host = "https://reqres.in"
    wait_time = between(1, 3)

    def on_start(self):
        """Runs once per simulated user before it starts picking tasks — logs in
        and stores the token, the way a real client authenticates before making
        further calls."""
        response = self.client.post(
            "/api/login",
            json={"email": "eve.holt@reqres.in", "password": "cityslicka"},
            name="/api/login",
        )
        self.token = response.json().get("token") if response.ok else None

    @task(5)
    def browse_user_list(self):
        """Highest weight: most real traffic is reads, not writes."""
        page = random.randint(1, 2)
        self.client.get(f"/api/users?page={page}", name="/api/users?page=[n]")

    @task(3)
    def view_single_user(self):
        user_id = random.randint(1, 12)
        self.client.get(f"/api/users/{user_id}", name="/api/users/[id]")

    @task(1)
    def submit_new_record(self):
        """Lowest weight: writes are rarer than reads in most real traffic mixes."""
        self.client.post(
            "/api/users",
            json={"name": "Load Test User", "job": "QA Engineer"},
            name="/api/users [POST]",
        )
