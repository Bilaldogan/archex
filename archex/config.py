"""Profile loading + validation.

A *profile* is the only source-specific thing in archex. Everything the engine
needs to adapt to a new archive (OCR settings, LLM prompt, output schema,
taxonomy, export columns) lives in one YAML file. The engine never changes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

REQUIRED = ["name", "llm"]


@dataclass
class Profile:
    name: str
    raw: dict
    path: str

    # convenience accessors -------------------------------------------------
    @property
    def input(self) -> dict:
        return self.raw.get("input", {})

    @property
    def ocr(self) -> dict:
        return self.raw.get("ocr", {})

    @property
    def llm(self) -> dict:
        return self.raw.get("llm", {})

    @property
    def normalize(self) -> dict:
        return self.raw.get("normalize", {})

    @property
    def export(self) -> dict:
        return self.raw.get("export", {})

    @property
    def extract(self) -> dict:
        return self.raw.get("extract", {})

    @property
    def validate(self) -> dict:
        return self.raw.get("validate", {})

    @property
    def reconcile(self) -> dict:
        return self.raw.get("reconcile", {})

    def out_dir(self) -> str:
        """Per-profile output directory for extracted JSON records."""
        base = self.input.get("out_dir") or f"{self.name}_out"
        os.makedirs(base, exist_ok=True)
        return base


def load_profile(path: str) -> Profile:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Profile not found: {path}")
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    missing = [k for k in REQUIRED if k not in raw]
    if missing:
        raise ValueError(f"Profile {path} missing required keys: {missing}")

    name = raw.get("name") or os.path.splitext(os.path.basename(path))[0]
    return Profile(name=name, raw=raw, path=path)


def resolve_profile_path(name_or_path: str) -> str:
    """Accept either a path to a .yaml or a bare profile name (looked up in
    ./profiles/<name>.yaml)."""
    if os.path.exists(name_or_path):
        return name_or_path
    for cand in (
        os.path.join("profiles", f"{name_or_path}.yaml"),
        os.path.join("profiles", f"{name_or_path}.yml"),
        f"{name_or_path}.yaml",
    ):
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(f"No profile '{name_or_path}' (looked in ./profiles/)")
