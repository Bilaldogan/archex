# archex — Handoff

## Durum: building
Son guncelleme: 2026-06-29

## Yapilan
- Generic, profil-tabanli motor: config/ocr/llm/pipeline/normalize/compile/cli
- Pluggable OCR (tesseract/easyocr), multi-provider LLM (groq/openai/ollama/anthropic)
- **Multi-record mode** eklendi: bir sayfa → N kayit (profile.extract.mode: multi),
  compile her kaydi ayri satir yapar + page-level provenance (_source) ekler
- **json_mode** eklendi (groq/openai response_format) → buyuk sayfalarda gecerli-JSON garantisi
- **Field validation** eklendi: profile.validate.rules (required/range/regex/enum/max_len),
  multi-record uyumlu, kayitlara _flags yazar + ozet rapor, CLI `validate` komutu.
  Boston demo: 3/68 kayit flagged (adres eksik), export'ta Flags kolonu
- **Calisan demo (uctan uca dogrulandi):** profiles/boston-1916.yaml — 1916 Boston
  City Directory (kamu mali) bir sayfa → 68 yapilandirilmis kayit (ad/meslek/adres).
  examples/ : gorsel + worklist + sample-output.csv
- Ikinci ornek profil: profiles/pech-1911.yaml (single-record, sirket + kurul)
- README SEO-optimize (genealogy/OCR/structured-data anahtar kelimeleri + quickstart)

## Siradaki
1. **public yap** (test edilebilir + demo hazir; repo Bilal adiyla public olacak)
2. GitHub topics ekle: ocr, genealogy, city-directory, document-extraction, llm,
   data-extraction, digital-humanities, historical-records
3. Daha fazla ornek profil (passenger list, census) — SEO genisletme
4. Roadmap: cross-source reconciliation · human-in-the-loop review (validate-flag'li kayitlar)

## Notlar
- Free-tier LLM tek istekte ~110 kayit cikaramiyor (413/token). Demo sayfayi
  ust %40'a kirpti (~68 kayit). Tam sayfa icin: sayfa-parcalama veya yuksek-limit tier.
- API key SADECE env'den (GROQ_API_KEY). Repoda/profilde key yok.

## Otomasyon Notu
- Pipeline tam otomatik (resumable, rate-limit, json_mode). Insan mudahalesi:
  worklist hazirlama + dusuk-guven kayit review'u. Multi-record + reconciliation
  ile coklu-kaynak isleri de otomatiklesir.
