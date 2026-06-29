"""Deterministic field validation, driven by profile.validate.rules.

Flags extracted records that violate sanity rules — missing required fields,
out-of-range dates, malformed values — so a human reviewer can focus only on
the suspect rows instead of re-reading everything. Writes `_flags` onto each
record and prints a summary. Pairs with provenance to make output trustworthy.

Rule types:
  required  — value must be present (not null/""/[])
  range     — numeric, within [min, max]
  regex     — string matches pattern
  enum      — value is one of `values`
  max_len   — string length <= n
"""
from __future__ import annotations

import json
import os
import re

from .config import Profile
from .util import dget


def _passes(value, rule) -> bool:
    t = rule.get("type")
    if t == "required":
        return value not in (None, "", [], {})
    if t == "range":
        try:
            n = float(value)
        except (TypeError, ValueError):
            return False
        if "min" in rule and n < rule["min"]:
            return False
        if "max" in rule and n > rule["max"]:
            return False
        return True
    if t == "regex":
        return re.search(rule["pattern"], str(value)) is not None
    if t == "enum":
        return value in rule.get("values", [])
    if t == "max_len":
        return len(str(value)) <= rule["max_len"]
    return True  # unknown rule type → never flags


def validate_record(rec: dict, rules: list) -> list:
    """Return a list of flag dicts for the rules this record violates."""
    flags = []
    for rule in rules:
        val = dget(rec, rule["field"])
        # absent values only fail the `required` rule; other rules skip them
        if val is None and rule.get("type") != "required":
            continue
        if not _passes(val, rule):
            flags.append(
                {
                    "field": rule["field"],
                    "rule": rule.get("type"),
                    "msg": rule.get("msg") or f"{rule['field']} failed {rule.get('type')}",
                }
            )
    return flags


def run_validate(profile: Profile, write: bool = True) -> None:
    rules = profile.validate.get("rules", [])
    if not rules:
        print("validate: no rules in profile.validate")
        return
    out = profile.out_dir()
    multi = profile.extract.get("mode") == "multi"
    rkey = profile.extract.get("records_key", "records")

    files = sorted(f for f in os.listdir(out) if f.endswith(".json"))
    total = flagged = 0
    by_rule: dict = {}
    for fn in files:
        path = os.path.join(out, fn)
        with open(path, encoding="utf-8") as f:
            wrapper = json.load(f)

        items = dget(wrapper, rkey) if multi else [wrapper]
        for item in items or []:
            ctx = item
            if multi:  # let rules reach page-level provenance
                ctx = {**item, "_id": wrapper.get("_id"), "_source": wrapper.get("_source")}
            flags = validate_record(ctx, rules)
            total += 1
            if flags:
                flagged += 1
                for fl in flags:
                    by_rule[fl["field"]] = by_rule.get(fl["field"], 0) + 1
            if write:
                item["_flags"] = flags

        if write:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(wrapper, f, ensure_ascii=False, indent=1)

    print(f"validate: {flagged}/{total} record(s) flagged across {len(files)} file(s)")
    for field, n in sorted(by_rule.items(), key=lambda x: -x[1]):
        print(f"  {field}: {n}")
