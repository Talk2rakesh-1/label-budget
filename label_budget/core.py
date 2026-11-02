"""Bounded, deterministic k-nearest-neighbor active learning over supplied features."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

MAX_BYTES = 2 * 1024 * 1024


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input exceeds 2 MiB")
    try:
        data = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid JSON encoding or nesting") from error
    return validate(data)


def validate(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != {"labeled", "pool"}:
        raise ValueError("expected labeled and pool arrays")
    seen: set[str] = set()
    dimension = None
    labels: dict[str, int] = {}
    for group, low, high in (("labeled", 4, 200), ("pool", 1, 500)):
        rows = data[group]
        if not isinstance(rows, list) or not low <= len(rows) <= high:
            raise ValueError(f"{group} row count out of bounds")
        for row in rows:
            fields = {"id", "features", "label"} if group == "labeled" else {"id", "features"}
            if not isinstance(row, dict) or set(row) != fields:
                raise ValueError("unexpected row fields")
            identifier = row["id"]
            if not isinstance(identifier, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{1,64}", identifier
            ):
                raise ValueError("invalid row ID")
            if identifier in seen:
                raise ValueError("row IDs must be globally unique")
            seen.add(identifier)
            vector = row["features"]
            if not isinstance(vector, list) or not 1 <= len(vector) <= 32:
                raise ValueError("features must have 1-32 dimensions")
            if dimension is None:
                dimension = len(vector)
            if len(vector) != dimension:
                raise ValueError("feature dimensions differ")
            if any(
                type(x) not in (int, float) or abs(x) > 1e6 or not math.isfinite(x) for x in vector
            ):
                raise ValueError("features must be finite bounded numbers")
            if group == "labeled":
                label = row["label"]
                if not isinstance(label, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", label):
                    raise ValueError("invalid label")
                labels[label] = labels.get(label, 0) + 1
    if not 2 <= len(labels) <= 10 or min(labels.values()) < 2:
        raise ValueError("need 2-10 classes with at least two examples each")
    return data


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def select(data: dict[str, Any], budget: int = 5, diversity: float = 0.35) -> dict[str, Any]:
    validate(data)
    if type(budget) is not int or not 1 <= budget <= min(50, len(data["pool"])):
        raise ValueError("budget must be 1-50 and no greater than pool size")
    if (
        type(diversity) not in (int, float)
        or not math.isfinite(diversity)
        or not 0 <= diversity <= 1
    ):
        raise ValueError("diversity must be between zero and one")
    labeled = sorted(data["labeled"], key=lambda row: row["id"])
    pool = sorted(data["pool"], key=lambda row: row["id"])
    classes = sorted({row["label"] for row in labeled})
    columns = list(zip(*(row["features"] for row in labeled)))
    means = [sum(col) / len(col) for col in columns]
    scales = [
        max(math.sqrt(sum((x - mean) ** 2 for x in col) / len(col)), 1e-12)
        for col, mean in zip(columns, means)
    ]

    def normalize(vector: list[float]) -> list[float]:
        return [(x - mean) / scale for x, mean, scale in zip(vector, means, scales)]

    training = [normalize(row["features"]) for row in labeled]
    vectors = [normalize(row["features"]) for row in pool]
    candidates = []
    k = min(3, len(labeled))
    for row, vector in zip(pool, vectors):
        neighbors = sorted(
            (distance(vector, v), item["id"], item["label"]) for item, v in zip(labeled, training)
        )[:k]
        # Uniform neighbor votes with Laplace smoothing. Scores are not calibrated probabilities.
        scores = {
            label: (1 + sum(n[2] == label for n in neighbors)) / (k + len(classes))
            for label in classes
        }
        entropy = -sum(p * math.log(p) for p in scores.values()) / math.log(len(classes))
        candidates.append({"id": row["id"], "uncertainty": entropy, "class_scores": scores})
    selected: list[int] = []
    result = []
    while len(selected) < budget:
        ranked = []
        for i, candidate in enumerate(candidates):
            if i in selected:
                continue
            # First pick is uncertainty-only. Subsequent distances saturate into [0,1).
            nearest = min((distance(vectors[i], vectors[j]) for j in selected), default=0.0)
            novelty = nearest / (1 + nearest)
            score = (
                candidate["uncertainty"]
                if not selected
                else (1 - diversity) * candidate["uncertainty"] + diversity * novelty
            )
            ranked.append((-score, candidate["id"], i, novelty))
        negative, _, index, novelty = min(ranked)
        selected.append(index)
        result.append({**candidates[index], "selection_score": -negative, "diversity": novelty})
    return {
        "method": "knn-entropy-greedy-diversity",
        "k": k,
        "selected": result,
        "human_label_required": True,
        "pool_size": len(pool),
        "budget": budget,
    }
