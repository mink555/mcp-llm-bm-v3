#!/usr/bin/env python3
"""
Merge TAU2 simulation JSON files safely.

- Keeps base["info"] as-is (prefers the base file's metadata).
- Merges tasks by task.id (base wins on conflicts).
- Merges simulations by (task_id, trial) unique key (base wins on conflicts).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_tasks(tasks: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for t in tasks or []:
        if not isinstance(t, dict):
            continue
        tid = t.get("id")
        if tid is None:
            continue
        out[str(tid)] = t
    return out


def _index_sims(sims: list[dict]) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    for s in sims or []:
        if not isinstance(s, dict):
            continue
        task_id = str(s.get("task_id", ""))
        trial = s.get("trial")
        if trial is None:
            trial = s.get("info_trial_num")
        try:
            trial_i = int(trial) if trial is not None else 0
        except Exception:
            trial_i = 0
        out[(task_id, trial_i)] = s
    return out


def merge(*, base: dict[str, Any], add: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}

    merged["info"] = base.get("info") or add.get("info") or {}

    base_tasks = _index_tasks(base.get("tasks") or [])
    add_tasks = _index_tasks(add.get("tasks") or [])
    # base wins
    for k, v in add_tasks.items():
        if k not in base_tasks:
            base_tasks[k] = v
    merged["tasks"] = list(base_tasks.values())

    base_sims = _index_sims(base.get("simulations") or [])
    add_sims = _index_sims(add.get("simulations") or [])
    # base wins
    for k, v in add_sims.items():
        if k not in base_sims:
            base_sims[k] = v

    merged["simulations"] = list(base_sims.values())

    return merged


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--add", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    base = _load(args.base) if args.base.exists() else {"info": {}, "tasks": [], "simulations": []}
    add = _load(args.add)

    out = merge(base=base, add=add)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

