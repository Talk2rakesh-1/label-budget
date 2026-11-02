# LabelBudget

[![CI](https://github.com/Talk2rakesh-1/label-budget/actions/workflows/ci.yml/badge.svg)](https://github.com/Talk2rakesh-1/label-budget/actions/workflows/ci.yml)

A local active-learning CLI that selects a small batch of examples for **human annotation**. It fits a nearest-neighbor model from labeled feature vectors, measures vote entropy, and greedily balances uncertainty with diversity. No paid API, model download, runtime dependency, or outbound request.

**Functional portfolio MVP, not a validated annotation optimizer.** It does not label data automatically, guarantee label savings, or understand raw images/text. You supply meaningful numeric features and legally obtained examples.

## Try it

Python 3.11+:

```sh
python -m label_budget examples/shapes.json --budget 3
python -m label_budget examples/shapes.json --budget 3 --diversity 0
```

Optional installation: `python -m pip install .`, then `label-budget examples/shapes.json --budget 3`.

JSON goes to stdout, failures to stderr. Exit codes: 0 success, 2 invalid input or I/O. No files are modified. Redirect stdout to save a report.

## Input and annotation loop

```json
{
  "labeled": [
    {"id":"a1","features":[-2,-1],"label":"round"},
    {"id":"a2","features":[-1,-2],"label":"round"},
    {"id":"b1","features":[2,1],"label":"angular"},
    {"id":"b2","features":[1,2],"label":"angular"}
  ],
  "pool": [{"id":"p1","features":[0,0]}]
}
```

Use `--budget 1` with this minimal input. Default budget is 5 and must not exceed the pool size.

1. Start with at least two seed examples per class and a separate unlabeled pool.
2. Select a batch. Reports include IDs, entropy, neighbor class scores, diversity contribution and selection score.
3. Have a human inspect the original items using the IDs. The scores are diagnostic; **do not convert the highest score into a human label**.
4. Move genuinely annotated rows from `pool` to `labeled`, adding their labels; then rerun. Keep a separate fixed test set that is never included in either selection pool or training.

Bounds: 2 MiB JSON; 4–200 labeled rows; 1–500 pool rows; 2–10 classes with at least two seeds each; 1–32 equal-length features; finite numeric values within ±1e6; globally unique IDs using ASCII letters/digits/underscore/hyphen (1–64 characters); labels use the same character set (1–32). Duplicate object keys, unknown fields, booleans as numbers, mismatched dimensions, and invalid budgets are rejected. Budget is 1–50. Diversity is 0–1 (default 0.35).

## Model

- Fit feature means and population standard deviations on labeled data only. Scale floor is 1e-12 to avoid division instability.
- Use the three nearest labeled vectors in standardized Euclidean space. Distance ties resolve by ID.
- Apply add-one smoothing to class votes, then normalize entropy by log(class count).
- First select maximum entropy. For later picks, combine `(1-diversity)*entropy + diversity*d/(1+d)`, where `d` is distance to the nearest selected candidate.
- Resolve selection ties lexicographically by ID. Input row order does not change results.

Scores are **not calibrated confidence probabilities**. Features with near-zero training variance can dominate distance; inappropriate scaling, imbalanced seeds, outliers and high dimensionality can make selection unhelpful. Diversity can overselect outliers. There is no guarantee of improvement over random sampling. See the [model card](docs/MODEL_CARD.md).

## Validation

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
mypy label_budget
bandit -r label_budget -ll
pip-audit -r requirements.txt
```

Thirteen tests cover deterministic selection, boundary selection, diversity, score normalization, invalid data, extreme scaling, duplicate JSON keys, byte bounds, nonmutation and subprocess CLI behavior. Original synthetic shape vectors are regression fixtures, not a benchmark. No real-world accuracy or savings have been measured. [Executed checks](docs/VERIFICATION.md).

## Security and licensing

Inputs are bounded and parsed as data. No pickle, eval, shell execution, model serialization, database or web service. Reports omit feature vectors but IDs and model scores can still be sensitive. File permissions are inherited from your OS. Python's standard library is the only runtime dependency. Source and original fixtures are MIT licensed. [Resource review](THIRD_PARTY.md), [research](docs/RESEARCH.md), [security](SECURITY.md).
