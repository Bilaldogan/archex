# archex — Handoff

## Durum: building
Son guncelleme: 2026-06-20

## Yapilan
- Repo kuruldu (private), ideas'a `PR_archex/` submodule olarak eklendi
- Generic, profil-tabanli motor yazildi (osmanli-sirketler extraction kodundan turetildi):
  - `archex/config.py` — profil yukleme/dogrulama
  - `archex/ocr.py` — tesseract + easyocr (pluggable), preprocess
  - `archex/llm.py` — multi-provider (groq/openai/ollama/anthropic), JSON parse + retry
  - `archex/pipeline.py` — worklist → OCR → LLM → JSON, resumable
  - `archex/normalize.py` — taxonomy canonical + deterministic recompute
  - `archex/compile.py` — JSON → csv/xlsx/json (dot-path field mapping)
  - `archex/cli.py` — init/extract/status/normalize/export
- Referans profil: `profiles/pech-1911.yaml` (Pech 1911 mantigi tamamen YAML'e tasindi)
- **Secret hijyeni:** API key'ler sadece env'den, repoda yok. Eski osmanli kodundaki
  GROQ key sizintisi bu temiz repo'ya tasinMADI.

## Siradaki
1. Sanity test: `pip install -e .` + sahte worklist/gorsel ile uctan uca dene
2. Gercek dogrulama: Pech worklist + birkac gorsel ile extract → normalize → export,
   ciktinin eski `pech-1911-96-sirket.xlsx` ile esdeger oldugunu teyit et
3. v2 — multi-record pages (Annuaire gibi sayfada N kayit) motor destegi
4. v2 — cross-source reconciliation (bugun elle yapilan Pech↔Enes eslestirmesi)

## Otomasyon Notu
- Pipeline tamamen otomatize (resumable, rate-limit'li). Insan mudahalesi:
  worklist hazirlama (gorsel→kayit eslestirme) + dusuk-guven kayitlarin review'u
- Multi-record + reconciliation eklenince Annuaire/coklu-kaynak isleri de otomatiklesir
