# archex

**Config-driven historical document → structured data extractor.**

Point archex at scanned pages of a historical catalogue, almanac, registry, or
directory; describe what you want in a single YAML *profile*; get back clean,
provenance-tagged JSON/CSV/XLSX. The OCR → LLM → normalize → export engine never
changes — only the profile does.

Built for digital-humanities / archival research where generic PDF parsers fall
short: bad OCR on old print, domain-specific schemas, per-record classification,
and **page-level citations** you can actually footnote.

---

## How it works

```
page images ──▶ OCR ──▶ LLM (your schema) ──▶ JSON ──▶ normalize ──▶ csv / xlsx
                 │                                         │
            ocr: block                              normalize: block
            in profile                              in profile
```

Everything source-specific lives in `profiles/<name>.yaml`:

- **`ocr`** — engine (tesseract/easyocr), language, preprocessing
- **`llm`** — provider/model + your extraction prompt and output JSON shape
- **`normalize`** — canonicalise labels + deterministically recompute summaries
- **`export`** — which fields become which columns

A *worklist* (`[{id, images, ...}]`) lists the records to process. Each entry's
extra fields are fed to your prompt template and preserved under `_source`.

## Install

```bash
pip install -e .                  # core (tesseract + groq/openai/ollama)
pip install -e ".[easyocr]"       # optional EasyOCR backend
pip install -e ".[export]"        # optional XLSX export (openpyxl)
```

Requires the `tesseract` binary for the default OCR engine
(`brew install tesseract tesseract-lang`).

## Use

```bash
archex init my-source                          # scaffold profiles/my-source.yaml
# edit the profile + create the worklist json

export GROQ_API_KEY=...                         # keys come from env, never the repo
archex extract  --profile my-source            # OCR → LLM → JSON (resumable)
archex status   --profile my-source            # progress
archex normalize --profile my-source           # canonical labels + recomputed summaries
archex export   --profile my-source --format csv,xlsx
```

`extract` is **resumable**: already-extracted records are skipped, failures are
written as `<id>.ERROR.txt` and retried on the next run.

## LLM providers

| provider    | env var             | notes                       |
|-------------|---------------------|-----------------------------|
| `groq`      | `GROQ_API_KEY`      | default, free-tier friendly |
| `openai`    | `OPENAI_API_KEY`    | OpenAI-compatible           |
| `ollama`    | —                   | local, no key (`base_url`)  |
| `anthropic` | `ANTHROPIC_API_KEY` | native messages API         |

## Reference profile

`profiles/pech-1911.yaml` is a worked example: extracting Ottoman joint-stock
companies from Edgar Pech's 1911 *Manuel des Sociétés Anonymes*, including full
board rosters with per-member classification and page provenance. Use it as a
template for your own source.

## Roadmap

- **Multi-record pages** — N records per scanned page (almanac/directory layouts)
- **Cross-source reconciliation** — match the same entity across two sources,
  diff field-by-field, flag conflicts (automates manual source-conflict tables)
- **Field-level confidence + validation rules** (e.g. year range sanity checks)
- **Human-in-the-loop review** — flag low-confidence records for correction

## License

MIT
