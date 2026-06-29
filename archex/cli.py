"""archex command-line entry point."""
from __future__ import annotations

import argparse
import os
import sys

from . import compile as compile_mod
from . import normalize as normalize_mod
from . import pipeline
from . import validate as validate_mod
from .config import load_profile, resolve_profile_path

PROFILE_TEMPLATE = """\
# archex profile — the only source-specific file. The engine never changes.
name: {name}
description: ""

input:
  image_dir: /tmp/{name}        # where the page images live
  worklist: {name}.worklist.json # [{{ "id": "...", "images": ["p1.jpg"], ... }}]
  out_dir: {name}_out           # extracted JSON records land here

ocr:
  engine: tesseract             # tesseract | easyocr
  lang: fra                     # tesseract language code
  psm: 6
  preprocess:
    grayscale: true
    contrast: 1.8
    sharpen: true
    max_width: 2500

llm:
  provider: groq                # groq | openai | ollama | anthropic
  model: llama-3.3-70b-versatile
  temperature: 0.3
  max_tokens: 8192
  rate_limit_delay: 6.0         # seconds between records (free-tier friendly)
  system_prompt: |
    You are a historical-archive data extraction expert. Return ONLY JSON.
  user_template: |
    RECORD: {{name}}
    OCR TEXT:
    {{ocr_text}}

    JSON output:

# Optional: deterministic cleanup after extraction
normalize:
  taxonomy: []                  # see profiles/pech-1911.yaml for an example
  recompute: []

# Required for `archex export`
export:
  fields:
    - {{col: ID, path: _id}}
"""


def cmd_init(args):
    os.makedirs("profiles", exist_ok=True)
    path = os.path.join("profiles", f"{args.name}.yaml")
    if os.path.exists(path) and not args.force:
        sys.exit(f"{path} already exists (use --force to overwrite)")
    with open(path, "w", encoding="utf-8") as f:
        f.write(PROFILE_TEMPLATE.format(name=args.name))
    print(f"created {path}")


def _profile(args):
    return load_profile(resolve_profile_path(args.profile))


def cmd_extract(args):
    pipeline.run_extract(_profile(args), only=args.only)


def cmd_status(args):
    pipeline.status(_profile(args))


def cmd_normalize(args):
    normalize_mod.run_normalize(_profile(args))


def cmd_validate(args):
    validate_mod.run_validate(_profile(args), write=not args.no_write)


def cmd_export(args):
    formats = [s.strip() for s in args.format.split(",") if s.strip()]
    compile_mod.run_export(_profile(args), formats, out_base=args.out)


def main(argv=None):
    p = argparse.ArgumentParser(prog="archex", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="scaffold a new profile")
    pi.add_argument("name")
    pi.add_argument("--force", action="store_true")
    pi.set_defaults(func=cmd_init)

    pe = sub.add_parser("extract", help="OCR -> LLM -> JSON (resumable)")
    pe.add_argument("--profile", required=True)
    pe.add_argument("--only", help="process a single record id")
    pe.set_defaults(func=cmd_extract)

    ps = sub.add_parser("status", help="show extraction progress")
    ps.add_argument("--profile", required=True)
    ps.set_defaults(func=cmd_status)

    pn = sub.add_parser("normalize", help="deterministic label/summary cleanup")
    pn.add_argument("--profile", required=True)
    pn.set_defaults(func=cmd_normalize)

    pv = sub.add_parser("validate", help="flag records that violate field rules")
    pv.add_argument("--profile", required=True)
    pv.add_argument("--no-write", action="store_true", help="report only, don't write _flags")
    pv.set_defaults(func=cmd_validate)

    px = sub.add_parser("export", help="flatten records to csv/xlsx/json")
    px.add_argument("--profile", required=True)
    px.add_argument("--format", default="csv,xlsx")
    px.add_argument("--out", help="output basename (default: profile name)")
    px.set_defaults(func=cmd_export)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
