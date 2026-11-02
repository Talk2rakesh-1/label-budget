import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from label_budget.core import load, select, validate

FIXTURE = Path(__file__).resolve().parents[1] / "examples/shapes.json"


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())

    def test_budget_unique_finite(self):
        report = select(self.data, 5)
        self.assertEqual(len({r["id"] for r in report["selected"]}), 5)
        for row in report["selected"]:
            self.assertAlmostEqual(sum(row["class_scores"].values()), 1)
            self.assertTrue(0 <= row["uncertainty"] <= 1)

    def test_permutation_invariance(self):
        original = select(self.data, 5)
        self.data["pool"].reverse()
        self.data["labeled"].reverse()
        self.assertEqual(original, select(self.data, 5))

    def test_no_mutation(self):
        before = copy.deepcopy(self.data)
        select(self.data, 3)
        self.assertEqual(before, self.data)

    def test_boundary_is_first(self):
        self.assertEqual(select(self.data, 1)["selected"][0]["id"], "candidate-0")

    def test_diversity_avoids_near_duplicate(self):
        rows = select(self.data, 2, 1)["selected"]
        self.assertNotEqual(rows[1]["id"], "candidate-1")

    def test_budget_rejected(self):
        for value in (0, -1, True, 9):
            with self.assertRaises(ValueError):
                select(self.data, value)

    def test_bad_numbers(self):
        for value in (True, float("nan"), float("inf"), 1000001, "0"):
            self.data["pool"][0]["features"][0] = value
            with self.assertRaises(ValueError):
                validate(self.data)

    def test_dimension_and_duplicate_id(self):
        self.data["pool"][0]["features"] = [1]
        with self.assertRaises(ValueError):
            validate(self.data)
        self.setUp()
        self.data["pool"][0]["id"] = "seed-0"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_classes(self):
        for row in self.data["labeled"]:
            row["label"] = "one"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_constant_features(self):
        for row in self.data["labeled"] + self.data["pool"]:
            row["features"] = [0, 0]
        self.assertEqual(len(select(self.data, 2)["selected"]), 2)

    def test_duplicate_keys_and_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for raw in ('{"pool":[],"pool":[]}', " " * (2 * 1024 * 1024 + 1)):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    load(path)

    def test_extreme_scale_and_integer(self):
        for row in self.data["labeled"]:
            row["features"] = [1e-150, 0]
        self.assertEqual(len(select(self.data, 2)["selected"]), 2)
        self.data["pool"][0]["features"][0] = 10**400
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_cli(self):
        result = subprocess.run(
            [sys.executable, "-m", "label_budget", str(FIXTURE), "--budget", "2"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["budget"], 2)
        result = subprocess.run(
            [sys.executable, "-m", "label_budget", str(FIXTURE), "--budget", "99"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
