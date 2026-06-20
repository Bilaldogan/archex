"""Deterministic post-processing of extracted records, driven by
profile.normalize. Two operations:

  taxonomy  — canonicalise a label field across list items (fix accents /
              off-schema variants via an alias map)
  recompute — rebuild a summary object from raw items by counting buckets,
              so an LLM-written summary can never drift from the actual data

Runs in-place over the profile's out_dir and prints a change report.
"""
from __future__ import annotations

import json
import os

from .config import Profile


def _apply_taxonomy(record: dict, rule: dict) -> int:
    field = rule["field"]
    item_key = rule.get("item_key")
    canonical = set(rule.get("canonical", []))
    aliases = rule.get("aliases", {})
    default = rule.get("default", "Belirsiz")
    items = record.get(field)
    if not isinstance(items, list):
        return 0

    def fix(v):
        if v in aliases:
            return aliases[v]
        if v in canonical:
            return v
        return default

    changed = 0
    for it in items:
        if item_key and isinstance(it, dict):
            old = it.get(item_key)
            new = fix(old)
            if new != old:
                it[item_key] = new
                changed += 1
    return changed


def _apply_recompute(record: dict, rule: dict) -> bool:
    src = record.get(rule["from"])
    if not isinstance(src, list):
        return False
    key = rule["key"]
    buckets = rule["buckets"]
    counts = {b: 0 for b in buckets}
    for it in src:
        val = it.get(key) if isinstance(it, dict) else it
        for bname, members in buckets.items():
            if members == "*" or (isinstance(members, list) and val in members):
                counts[bname] += 1
    target = rule["target"]
    old = record.get(target)
    record[target] = counts
    return old != counts


def run_normalize(profile: Profile) -> None:
    out = profile.out_dir()
    cfg = profile.normalize
    tax_rules = cfg.get("taxonomy", [])
    recompute_rules = cfg.get("recompute", [])
    if not tax_rules and not recompute_rules:
        print("normalize: nothing configured in profile.normalize")
        return

    files = sorted(f for f in os.listdir(out) if f.endswith(".json"))
    tax_total = 0
    recompute_total = 0
    for fn in files:
        path = os.path.join(out, fn)
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
        tc = sum(_apply_taxonomy(rec, r) for r in tax_rules)
        rc = sum(1 for r in recompute_rules if _apply_recompute(rec, r))
        if tc or rc:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False, indent=1)
            tax_total += tc
            recompute_total += rc
            print(f"  {fn[:-5]}: {tc} label(s) fixed, {rc} summary(ies) recomputed")
    print(f"normalize: {tax_total} labels fixed, {recompute_total} summaries recomputed across {len(files)} records")
