# Local data layout

Only this guide and `artifacts/.gitkeep` belong in Git. Create the following folders as needed:

- `cache/`: upstream FastF1 cache; disposable and version-sensitive.
- `raw/`: normalized adapter snapshots plus source manifest; private by default.
- `processed/`: cleaned per-lap arrays and frozen reference products.
- `artifacts/`: validated `<comparison_id>.json` served by the API.
- `reports/`: rejected-lap reasons, reconciliation reports and QA evidence.

The scaffold contains no real data. Do not copy downloaded caches into fixtures or commits. A synthetic fixture must identify itself as synthetic and use invented driver codes. Circuit geometry/profile configurations can be committed only after checking their provenance and intended distribution.
