# Data and API contracts

Python is authoritative: `services/api/src/lapdna/models.py` and `inventory.py`. Run `npm run contracts` to regenerate OpenAPI, comparison/catalog JSON Schema and TypeScript. Version **1.1.0** replaces the unpublished 1.0 scaffold contract; no real published dataset needs migration.

## Endpoints implemented in the scaffold

| Endpoint | Behavior |
| --- | --- |
| GET /api/v1/health | Process health only |
| GET /api/v1/catalog | Summaries of schema-valid prepared telemetry and sector-only artifacts |
| GET /api/v1/comparisons/{id} | Discriminated immutable result |
| GET /api/v1/sessions | Imported event inventory, initially empty |
| GET /api/v1/sessions/{id}/laps | Full roster, per-lap phase, timings, capability and reasons |
| POST /api/v1/compare | Validate selection and return matching cached local artifact plus requested orientation |
| GET /openapi.json, /docs | Generated API documentation |

No upstream request is made by these routes. A cache miss is HTTP 409 until the T05 local normalized-data engine is implemented. This is explicit unfinished behavior, not a silently substituted sample.

POST body:

```json
{
  "session_id": "event-id",
  "lap_a_id": "lap-id-a",
  "lap_b_id": "lap-id-b",
  "allow_cross_phase": false,
  "detail_level": "auto"
}
```

`detail_level` is auto, telemetry or sector_only. Response is `{artifact: <telemetry-or-sector-only>, swapped: boolean}`. Artifact A/B remains canonical; swapped tells the view to exchange columns/channels and negate differences. Stored text uses actual driver identities and remains unchanged.

## Inventory and selection

SessionIdentity holds session_id, year, round, Q, circuit key and event name. **Phase belongs to each lap**, not to the event. LapIdentity supplies lap ID, phase, driver code/name/number and lap number. LapMetadata adds recorded duration, three sectors, compound, tyre age and track status.

SessionLapIndex holds session, source snapshot SHA-256, full driver roster and lap options. A LapOption includes nullable timing, capability telemetry/sector_only/unavailable and reasons. Selectable laps require complete positive recorded timing. Roster drivers with no eligible laps remain visible. Unique driver/lap identity and roster consistency are validated.

POST checks both lap IDs belong to the index, drivers differ, eligibility/capability permits the request, and cross-phase opt-in is present when needed. Cached artifacts must agree with the event, source digest, identities, phase, lap numbers and all recorded times. Auto prefers telemetry if both laps support it and a valid artifact exists; otherwise a prepared sector-only result may be returned.

Application errors use `{error:{code,message}}`. Codes include data_not_imported (409), lap_not_found (404), same_driver (422), cross_phase_not_enabled (422), lap_unavailable (422), telemetry_unavailable (422), comparison_not_prepared (409), artifact_invalid (503), quality_blocked (503) and invalid_request (422). Framework unknown-route errors need not have this envelope.

## Shared numerical conventions

Distance m, speed km/h, throttle %, time/delta ms. Finite floating values may retain fractional milliseconds; only display rounds them. Null means unsupported. Gear is strict integer 0–8; brake strict boolean/null. No pressure or steering channel exists.

Telemetry sample arrays match one increasing distance grid, beginning at zero with at most 5000 points. Important boundaries are inserted, so index × 5 is invalid. Delta is B raw elapsed minus A raw elapsed; positive favours A. The raw curve is interpolated but never corrected to fit recorded sector timing. Valid masks concern elapsed-time support; optional-channel holes remain independent.

## Result variants

Both results have schema_version, comparison_id, detail_level, event, lap_a/b and pairing. Pairing mode is same_phase/cross_phase; a cross-phase result requires a warning.

### Telemetry

ComparisonArtifact adds provenance, aligned channels, geometry, raw delta, support mask, reference sector distances, quality, segment partition, turn markers, estimated mini-sectors, class analysis, evidence and observations.

Provenance records source FastF1 version, pipeline/method versions, source snapshot/reference hashes, UTC generation, source session, circuit revision/reference lap. TimingProvenance is the smaller base for sector-only results. Additional source/import/review/config metadata below remains T01–T05 work.

Segments form an additive partition of 0..L. Gain equals endpoint delta difference and needs full timing support. Sensitivity bounds contain the unshifted gain. Wrapped complexes use linked non-wrapping pieces and count once per independent unit.

Corners contain marker_id, number, label, distance_m, segment_id, reference_speed_kph and speed_class. Marker class must match reference thresholds. Segment classes include low/medium/high/mixed/unknown; straights have no speed class.

EstimatedMiniSector has source=derived_telemetry, start_m, end_m and nullable gain_ms. Bins partition 0,100,...,L separately from corner windows. Their bounds must occur on the shared grid, supported gains must equal endpoint changes, and this separate partition reaches the finish. Never add mini-sector totals to corner totals.

AnalysisSummary contains exactly three class rows, the reference classification rule/thresholds, structured pattern, optional pattern driver, text, evidence IDs and limitations. Each row supplies included/excluded segment IDs, independent units, distance coverage, gross gains for A/B, net contribution, material win counts, sensitivity and assessment. Model validators account for linked units and check gross/net arithmetic, coverage and evidence references. Strong high/medium-gain-low-loss patterns require consistent fully covered classes. T05 still computes eligibility, support and templates from actual source arrays.

MetricEvidence retains range, values/units, B−A differences, native support and optional transition intervals. Observations reference evidence and a segment. Zero to three findings are permitted; fewer requires insufficient_evidence_reason.

### Sector-only

SectorComparisonArtifact has TimingProvenance, SectorQuality, fallback_reason, three sector_delta_ms values and three cumulative_delta_ms values. Two per-driver sector-sum checks are required and compared with actual metadata. Deltas must match recorded sectors.

This variant has **no distance array, turn markers, local gains, synthetic geometry or class findings**. Render separate points at Start/S1 end/S2 end/Finish, with an ordinal crossing axis and no joining curve. Timing data alone cannot locate the difference inside a sector.

## Reconciliation and validation boundary

Telemetry requires 11 unique checks: A and B sector_sum, sliced_duration, cumulative_sector_1, cumulative_sector_2; pair cumulative_sector_1, cumulative_sector_2, lap_gap. Checks retain timing_record_consistency, timing_constraint, cross_lap_consistency or calibration basis. Residual is observed minus recorded, and overall severity cannot understate any check.

Wire validators protect shape, arithmetic, partitioning and references. T04/T05 must additionally verify numbers against native data, derive threshold severity, evaluate eligibility/support, check template text, and require a reviewed source/config dataset. A schema-valid artifact alone is not verified science.

## Storage and security

Default directories: data/artifacts and data/sessions, separately overridable by LAPDNA_ARTIFACT_DIR/LAPDNA_SESSION_DIR. IDs permit 1–100 ASCII letters/digits/underscores/hyphens. Local readers enforce root confinement, safe identifiers, matching filename identities and a 20 MiB size limit. Corrupt artifacts/indexes fail visibly; intentionally blocked results are withheld.

The current readers enumerate flat JSON files. T05 introduces a published manifest and changes discovery in that same commit. Do not place catalog.json in the current artifact directory. Production generated-result cache storage is a separate T05/T12 concern.

## Planned additions before publication

| Ticket | Required addition |
| --- | --- |
| T01 | source_retrieved_at, source URLs, adapter/access metadata and source terms scope |
| T02 | lap_start_utc, eligibility summary and lap-condition context |
| T03 | circuit_config_sha256; reviewed geometry label positions in the circuit profile |
| T04 | settings_sha256, actual analysis settings and typed channel/interval quality reasons |
| T05 | reviewed dataset record, official-source verification scope, observation template_version, publication/cache manifest digest fields |

Add actual fields in Python and regenerate, never derive retrieval time from generation time. User-facing OpenF1 support beyond the availability probe requires a deliberate source adapter/provenance extension; current served sources are FastF1.

`npm run contracts:check` regenerates all four files and fails on drift. It may leave changed outputs for review. Browser code imports generated types, never a copied second scientific schema.
