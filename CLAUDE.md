# archex — AI Context

## Ne
Config-driven historical document → structured data extractor (OCR + LLM).
Tarihsel basili kaynaklardan (katalog/yillik/rehber) yapilandirilmis veri cikarir.
Motor kaynaktan bagimsiz; tum kaynak-spesifik sey `profiles/<name>.yaml`'de.

## Koken
`docs/osmanli-sirketler/extraction/` altindaki Pech 1911 / Annuaire cikarim
kodundan generic'lestirildi. Enes ile akademik isbirligi hatti (Osmanli sirketler).
Para hedefi degil — arastirma araci, ileride FOSS olabilir.

## Mimari kural
- **Motora kaynak-spesifik kod EKLEME.** Yeni kaynak = yeni profil YAML.
- Sema/prompt/taksonomi/export hep profilde. Kod sadece akisi calistirir.
- API key'ler SADECE env'den. Repoda/profilde asla key olmaz.

## Moduller
- `config.py` profil · `ocr.py` OCR · `llm.py` provider · `pipeline.py` orkestra
- `normalize.py` deterministik temizlik · `compile.py` export · `cli.py` giris

## Test
- `pip install -e .` sonrasi `archex --help`
- Degisiklik sonrasi: en az import + CLI smoke + ornek profil ile export testi

## Roadmap (HANDOFF'ta detay)
multi-record pages · cross-source reconciliation · field confidence · HITL review
