"""Application-layer contracts and deterministic background-job lifecycle tests."""

import threading
import time
import unittest
from argumentation.examples import EXAMPLES
from argumentation.webapp import create_server
from argumentation.webapp.jobs import ExperimentJobs
from argumentation.webapp.services import analyse, strategic
from argumentation.webapp.validation import ExperimentRequest


def wait_for_job(jobs, job_id):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job = jobs.get(job_id)
        if job["status"] != "running":
            return job
        time.sleep(0.005)
    raise AssertionError("Job did not reach a terminal status.")


class ServiceTests(unittest.TestCase):
    def test_serialized_acceptance_matches_selected_extensions(self):
        for semantics in ["grounded", "complete", "preferred", "stable", "semi-stable"]:
            result = analyse({**EXAMPLES["book-5.2"], "semantics": semantics})
            self.assertEqual(result["acceptance"]["a3"], "skeptically accepted")
            self.assertEqual(
                result["acceptance"]["a1"],
                "rejected" if semantics == "grounded" else "credulously accepted",
            )

    def test_strategy_uses_explicit_other_reports(self):
        result = strategic(
            {**EXAMPLES["book-5.10"], "reports": {"x": ["a4", "a5"], "y": ["a2"], "z": ["a3"]}}
        )
        self.assertEqual(result["utilities"], {"x": 2, "y": 1, "z": 0})
        self.assertEqual(result["best_responses"]["maximum_utility"], 2)

    def test_job_parameters_reject_invalid_types_and_ranges(self):
        for config in [
            {"count": True},
            {"count": 1001},
            {"probabilities": []},
            {"probabilities": [True]},
            {"probabilities": [float("nan")]},
            {"probabilities": [1.1]},
            {"seed": False},
            {"self_attacks": "false"},
        ]:
            with self.subTest(config=config), self.assertRaises(ValueError):
                ExperimentRequest.from_json(config)

    def test_validated_request_is_immutable(self):
        data = {"count": 1, "probabilities": [0.2], "seed": 0, "self_attacks": False}
        request = ExperimentRequest.from_json(data)
        data["probabilities"].append(0.3)
        self.assertEqual(request.probabilities, (0.2,))


class JobLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.request = ExperimentRequest.from_json({"count": 1, "probabilities": [0], "seed": 1})

    def test_one_running_job_and_progress_visibility(self):
        entered, release = threading.Event(), threading.Event()

        def runner(count, probabilities, seed, self_attacks, progress):
            progress(1, 2)
            entered.set()
            if not release.wait(5):
                raise RuntimeError("Test failed to release the runner.")
            return {"records": []}

        jobs = ExperimentJobs(runner=runner)
        job_id = jobs.start(self.request)["job_id"]
        try:
            self.assertTrue(entered.wait(5))
            self.assertEqual(jobs.get(job_id)["done"], 1)
            with self.assertRaisesRegex(ValueError, "already running"):
                jobs.start(self.request)
        finally:
            release.set()
        self.assertEqual(wait_for_job(jobs, job_id)["status"], "completed")

    def test_completed_jobs_are_bounded_and_snapshots_are_isolated(self):
        jobs = ExperimentJobs(max_jobs=2, runner=lambda *args: {"records": []})
        ids = []
        for _ in range(3):
            job_id = jobs.start(self.request)["job_id"]
            wait_for_job(jobs, job_id)
            ids.append(job_id)
        self.assertIsNone(jobs.get(ids[0]))
        snapshot = jobs.get(ids[-1])
        snapshot["result"]["records"].append("external mutation")
        self.assertEqual(jobs.get(ids[-1])["result"]["records"], [])

    def test_failed_job_is_terminal_and_does_not_block_next_run(self):
        attempts = []

        def runner(*args):
            attempts.append(1)
            if len(attempts) == 1:
                raise RuntimeError("Simulated computation failure")
            return {"records": []}

        jobs = ExperimentJobs(runner=runner)
        with self.assertLogs("argumentation.webapp.jobs", level="ERROR") as logs:
            first = jobs.start(self.request)["job_id"]
            failed = wait_for_job(jobs, first)
        self.assertEqual(failed["status"], "failed")
        self.assertIn("server log", failed["error"])
        self.assertIn("Simulated computation failure", "\n".join(logs.output))
        second = jobs.start(self.request)["job_id"]
        self.assertEqual(wait_for_job(jobs, second)["status"], "completed")

    def test_servers_have_independent_job_state(self):
        first, second = create_server(0), create_server(0)
        try:
            self.assertIsNot(first.jobs, second.jobs)
            job_id = first.jobs.start(self.request)["job_id"]
            wait_for_job(first.jobs, job_id)
            self.assertIsNone(second.jobs.get(job_id))
        finally:
            first.server_close()
            second.server_close()


if __name__ == "__main__":
    unittest.main()
