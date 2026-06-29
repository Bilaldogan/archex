"""Cross-source reconciliation: match the same entity across two extracted
sources, diff the fields you care about, and surface conflicts.

This automates the manual "two sources disagree — which is right?" table:
e.g. the same person in two city-directory years (did they move?), or the same
company in two catalogues (different founding date?). Matching is by a key
(one or more fields, normalized); comparison is field-by-field.

Output: a summary + a conflicts CSV (key, field, value_A, value_B).
"""
from __future__ import annotations

import csv

from .config import Profile
from .util import dget, iter_records


def _key(rec: dict, key_fields: list) -> str:
    parts = []
    for f in key_fields:
        v = dget(rec, f)
        parts.append(str(v).strip().lower() if v is not None else "")
    return "|".join(parts)


def _empty(v) -> bool:
    return v is None or v == ""


def run_reconcile(
    prof_a: Profile,
    prof_b: Profile,
    key_fields: list,
    compare_fields: list,
    out_base: str | None = None,
) -> None:
    if not key_fields:
        raise ValueError("reconcile needs key fields (--key or profile.reconcile.key)")
    A = list(iter_records(prof_a))
    B = list(iter_records(prof_b))

    b_index: dict = {}
    for b in B:
        b_index.setdefault(_key(b, key_fields), []).append(b)

    matched = 0
    conflicts = []
    only_a = 0
    matched_keys = set()
    homonyms = 0
    for a in A:
        k = _key(a, key_fields)
        if not k.strip("|"):
            continue
        bucket = b_index.get(k)
        if not bucket:
            only_a += 1
            continue
        matched += 1
        matched_keys.add(k)
        if len(bucket) > 1:
            # ambiguous key (homonyms) — can't trust the pairing, so don't emit
            # field conflicts; just report the count for the user to handle.
            homonyms += 1
            continue
        b = bucket[0]
        for fld in compare_fields:
            av, bv = dget(a, fld), dget(b, fld)
            if _empty(av) and _empty(bv):
                continue
            if (av or None) != (bv or None):
                conflicts.append({"key": k, "field": fld, "a": av, "b": bv})

    only_b = sum(len(v) for kk, v in b_index.items() if kk not in matched_keys and kk.strip("|"))

    print(f"reconcile: A({prof_a.name})={len(A)}  B({prof_b.name})={len(B)}")
    print(f"  matched entities:      {matched}")
    print(f"  field conflicts:       {len(conflicts)}")
    print(f"  only in A:             {only_a}")
    print(f"  only in B:             {only_b}")
    if homonyms:
        print(f"  ambiguous keys (>1 B match, skipped): {homonyms}")

    base = out_base or f"{prof_a.name}_vs_{prof_b.name}"
    path = f"{base}.conflicts.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "field", f"A:{prof_a.name}", f"B:{prof_b.name}"])
        for c in conflicts:
            w.writerow([c["key"], c["field"], c["a"], c["b"]])
    print(f"wrote {path} ({len(conflicts)} conflicts)")
