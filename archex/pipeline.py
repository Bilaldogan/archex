"""Extraction orchestration: worklist -> OCR -> LLM -> JSON, resumable.

A *worklist* is a JSON array of records. Each record MUST have:
  id      — unique string, used as the output filename
  images  — list of image filenames (resolved against input.image_dir)
Any other fields (name, page_start, sector, ...) are passed to the profile's
`user_template` and preserved under `_source` in the output.
"""
from __future__ import annotations

import json
import os
import time

from . import llm, ocr
from .config import Profile


def _load_worklist(profile: Profile) -> list[dict]:
    wl_path = profile.input.get("worklist")
    if not wl_path:
        raise ValueError("profile.input.worklist not set")
    with open(wl_path, encoding="utf-8") as f:
        return json.load(f)


def _format_user(template: str, record: dict, ocr_text: str) -> str:
    ctx = dict(record)
    ctx["ocr_text"] = ocr_text
    if "page_range" not in ctx and "page_start" in record:
        ctx["page_range"] = f"{record.get('page_start')}-{record.get('page_end')}"
    try:
        return template.format(**ctx)
    except KeyError as e:
        raise ValueError(f"user_template references {e} not in record {record.get('id')}")


def _ocr_record(profile: Profile, record: dict) -> str:
    img_dir = profile.input.get("image_dir", "")
    parts = []
    found = False
    for im in record.get("images", []):
        path = os.path.join(img_dir, im)
        if not os.path.exists(path):
            parts.append(f"--- {im} ---\n(missing)")
            continue
        found = True
        text = ocr.ocr_image(path, profile.ocr)
        parts.append(f"--- {im} ---\n{text or '(empty)'}")
        time.sleep(0.3)
    if not found:
        raise FileNotFoundError("no images found for record")
    return "\n\n".join(parts)


def run_extract(profile: Profile, only: str | None = None) -> None:
    wl = _load_worklist(profile)
    out = profile.out_dir()
    delay = profile.llm.get("rate_limit_delay", 2.0)
    system = profile.llm.get("system_prompt", "")
    template = profile.llm.get("user_template", "{ocr_text}")

    targets = [r for r in wl if only is None or r.get("id") == only]
    for rec in targets:
        rid = rec["id"]
        outpath = os.path.join(out, f"{rid}.json")
        if os.path.exists(outpath):
            print(f"[skip] {rid}")
            continue
        print(f"[ocr ] {rid} ({len(rec.get('images', []))} img) ...", flush=True)
        try:
            ocr_text = _ocr_record(profile, rec)
            user = _format_user(template, rec, ocr_text)
            data = llm.chat_json(profile.llm, system, user)
        except Exception as e:  # noqa: BLE001 — record-level isolation
            msg = f"{type(e).__name__}: {e}"
            print(f"  FAIL {rid}: {msg[:140]}")
            with open(os.path.join(out, f"{rid}.ERROR.txt"), "w") as f:
                f.write(msg)
            continue

        data["_id"] = rid
        data["_source"] = rec
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        # clear any stale error marker
        err = os.path.join(out, f"{rid}.ERROR.txt")
        if os.path.exists(err):
            os.remove(err)
        print(f"  OK   {rid}")
        time.sleep(delay)


def status(profile: Profile) -> None:
    wl = _load_worklist(profile)
    out = profile.out_dir()
    done = {f[:-5] for f in os.listdir(out) if f.endswith(".json")}
    errs = {f[:-10] for f in os.listdir(out) if f.endswith(".ERROR.txt")}
    pending = [r["id"] for r in wl if r["id"] not in done]
    print(f"done {len(done)}/{len(wl)}")
    if pending:
        print(f"pending ({len(pending)}): {' '.join(pending[:30])}{' …' if len(pending) > 30 else ''}")
    if errs:
        print(f"errored ({len(errs)}): {' '.join(sorted(errs)[:30])}")
