"""Flatten extracted JSON records into CSV (always) and XLSX (if openpyxl
present), driven by profile.export.fields.

Each field is:
  {col: "Column Name", path: "dotted.path"}                 # scalar
  {col: "Board", path: "board", list: "{name} ({title})",   # list -> joined
   sep: " | "}
"""
from __future__ import annotations

import csv
import json
import os

from .config import Profile
from .util import dget


def _cell(record: dict, field: dict):
    val = dget(record, field["path"])
    if val is None:
        return ""
    tmpl = field.get("list")
    if tmpl is not None:
        if not isinstance(val, list):
            return str(val)
        sep = field.get("sep", " | ")
        out = []
        for it in val:
            if isinstance(it, dict):
                out.append(tmpl.format_map(_SafeDict(it)))
            else:
                out.append(str(it))
        return sep.join(out)
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    return val


class _SafeDict(dict):
    def __missing__(self, key):
        return "?"


def _load_records(profile: Profile) -> list[dict]:
    out = profile.out_dir()
    recs = []
    for fn in sorted(f for f in os.listdir(out) if f.endswith(".json")):
        with open(os.path.join(out, fn), encoding="utf-8") as f:
            recs.append(json.load(f))
    return recs


def run_export(profile: Profile, formats: list[str], out_base: str | None = None) -> None:
    fields = profile.export.get("fields")
    if not fields:
        raise ValueError("profile.export.fields not set")
    records = _load_records(profile)
    cols = [f["col"] for f in fields]
    rows = [[_cell(r, f) for f in fields] for r in records]
    base = out_base or profile.name

    if "csv" in formats or "json" in formats or not formats:
        pass  # csv default below

    if "csv" in formats:
        path = f"{base}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        print(f"wrote {path} ({len(rows)} rows)")

    if "json" in formats:
        path = f"{base}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=1)
        print(f"wrote {path} ({len(records)} records)")

    if "xlsx" in formats:
        try:
            import openpyxl
        except ImportError:
            print("xlsx skipped — `pip install archex[export]` for openpyxl")
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = profile.name[:31]
            ws.append(cols)
            for row in rows:
                ws.append(row)
            path = f"{base}.xlsx"
            wb.save(path)
            print(f"wrote {path} ({len(rows)} rows)")
