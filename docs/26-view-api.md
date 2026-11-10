# Opt-in native view API

Backend checkpoint for owner-approved Steps 1-4. The production studio still
uses the unchanged v5 route. Do not switch the UI or deployment at this checkpoint.

## Compatibility and tier resolution

`POST /api/v1/compare` retains its existing request, `detail_level`, model fields,
IDs, canonical ordering and serialized outputs. No new defaults are injected into
legacy models. An explicit new endpoint, `POST /api/v1/views/compare`, accepts:

```json
{
  "session_id": "2026-19-rodriguez-Q",
  "lap_a_id": "fastf1_2026_19_Q_44_19",
  "lap_b_id": "fastf1_2026_19_Q_16_20",
  "allow_cross_phase": false,
  "requested_tier": "aligned_delta"
}
```

Lap IDs are examples of the native ID format; always obtain actual IDs from the
session inventory. The endpoint does not substitute a fastest lap. Its response
is `{artifact, swapped}`; the artifact uses canonical lexicographic lap ordering,
and `swapped` indicates that the requested A/B order was reversed. Delta is B-A.
The new `detail_level` stays `telemetry`; `view_tier` distinguishes:

- `telemetry_view`: real native channels against elapsed time, no delta or claims.
- `aligned_delta`: native-speed distance alignment and diagnostic uncertainty.
- `analysis`: the exact accepted legacy v5 analysis nested as `legacy_analysis`.

If a higher tier is unavailable, the endpoint returns the lower available tier
and explicit `unavailable_reasons`. Tier 0 failure returns an explicit error;
there is no fabricated trace or silent substitution. The same-driver restriction
and cross-phase opt-in remain until Step 5. Only the unchanged timing-eligible
cohort is included in these publications; flagged-lap visibility is also Step 5.

## Native samples and masks

`lap_a` and `lap_b` contain source timestamp offsets and speed, throttle, RPM,
gear and binary brake arrays. Values are not a resampled car-data stream. Real
padding observations may precede zero or follow `source_duration_ms`; clip their
display to the lap, while retaining them for edge interpolation. Optional missing,
invalid or contradictory duplicate channel values remain null. Zero/false are
valid measurements, never missing-data sentinels.

Each channel has a per-sample `measured`/`gap` mask and explicit span overlays.
Continuous channels can have a labelled `dashed_connector` over a flagged native
interval up to 2 s; these are derived connectors, never additional source samples.
Longer intervals are `blank_gap`. Gear/brake interpolation is `none`; unsupported
spans use `hatched_no_data`, with no held values. Trust spacing is 750 ms for
speed and 500 ms for the other channels. Null runs are explicit even if their
endpoints are closer than these limits. Entirely absent optional channels do
not make other native channels unavailable.

## Distance and elapsed time

The speed estimator calls the unchanged v5 trapezoidal integration and partial
integral functions. Speed is linear between native endpoints. Distance progress
nodes include the source timing edges and interior native speed observations;
elapsed lookup over those distance nodes is linear, as in v5. Speed gaps over
2 s, unbracketed speed or non-increasing progress disable Tier 1, never Tier 0.

Only distance is normalized to the session's frozen integrated reference length.
Elapsed time is never stretched, shifted internally or fitted to official sectors.
Each lap's elapsed endpoints are exactly zero and its source-clock duration. The
recorded official gap and endpoint residual are separate fields: source-clock
floating point precision or small source timing discrepancies are not hidden.

`alignment.lap_a/lap_b` contain the progress nodes, cumulative raw bound and
distance bands. The shared distance grid carries nominal elapsed A/B, B-A delta
and its lower/upper band. Sector annotations retain official and estimated
crossings, raw residuals and whether the crossing is a reference timing
constraint or a shared-progress estimate. Absolute interior residuals above
150 ms receive C annotations without rejecting Tier 1. Distance normalization
over 3% is also warned about, without rejecting Tier 1. Pair-gap/sector validation
rules remain unchanged inside the legacy Tier 2 computation.

## Prescribed bound

For each native speed interval exceeding 750 ms and no longer than 2 s:

`full_bound_m = dt_seconds * abs(v2_kph - v1_kph) / 7.2`

The full-interval diagnostic is retained. If a native interval crosses a timing
edge, its in-lap contribution is proportional to its overlap; accumulation is
linear through that overlap. Raw cumulative bound starts at zero and remains
accumulated at the finish. It is not reset when the displayed endpoints are pinned.

Let integrated progress be D, lap length L, cumulative bound E and final bound F.
On a frozen axis of length R, normalization is propagated as:

`lower = max(0, D-E) / (L+F) * R`

`upper = min(1, (D+E) / (L-F)) * R`

If `F >= L`, Tier 1 is unavailable rather than dividing by a nonpositive value.
Monotonic progress supplies a prefix maximum for the lower envelope. Distance
endpoints are pinned to the shared edges. Delta bands invert the *unpinned*
envelopes, so interpolation of a forced finish node cannot invent confidence
before the finish. Earliest/latest crossings combine as
`earliest_B - latest_A` / `latest_B - earliest_A`. Exact lap edges have exact
source-clock crossing times.

This is the owner's specified endpoint-speed model diagnostic, **not a rigorous
physical bound, calibrated probability or independent validation**. Equal speed
endpoints yield a zero formula bound despite potentially unobserved dynamics.
Always retain bridge flags. Newly bridged data never enters Tier 2: only the
original accepted v5 payload can appear in `legacy_analysis`.

## Offline publications and reproducibility

Retained source snapshots feed ignored `services/api/src/lapdna/view_data`, with
content-addressed compressed publications and a digest-checked catalogue. The
read-only endpoint does no network import or raw session parsing. Local caches
are bounded and disposable. The v5 `pilot_data` catalogue is never modified.

Step 3b uses original v5 references. Step 4 chooses the fastest speed-ready,
timing-eligible source lap, ties broken by driver number, lap number and stable
ID. No marker, geometry or position predicate participates. Reference sector
distances come from that lap's source timing constraints. Geometry/markers from
a different reference frame are never claimed to belong to the new reference.
Legacy Tier 2 analysis retains its original, independently frozen reference.

For the future renderer: Tier 0 has no distance estimate, so use elapsed time
and disable the distance toggle with its supplied reason. Tier 1 plots the v6
alignment frame and its bands. When rendering Tier 2 observations/maps, use
the nested legacy artifact's own grid, geometry, delta and evidence together.
Never place legacy corner boundaries or observations directly on a different
v6 reference axis. The wrapper carries both explicitly; it does not certify a
new projection between them. Existing accepted pairs retain the complete old
artifact, including its original analysis/map frame.

Commands and receipts:

```text
.venv/Scripts/python scripts/attribute_telemetry_gates.py --method v6
.venv/Scripts/python scripts/verify_v5_view_compatibility.py
.venv/Scripts/python scripts/recover_view_references.py
.venv/Scripts/python scripts/prepare_view_publications.py --sessions SESSION_ID
```

The first command is the Step 3b audit and can be expensive. It writes isolated
legacy-reference v6 views and does not activate v5 data. Step 4 retains the old
view catalogue and compressed blobs in ignored checkpoint storage before
publishing speed-only references. Committed coverage ledgers contain only derived
diagnostics and hashes, never native arrays or authentication data. Resume a
Step 3b measurement from its unchanged implementation/source cache; do not run it
over the Step 4 catalogue without deliberately restoring the old view checkpoint.
The normal preparation command defaults to `--reference-mode speed_only` after
Step 4; `legacy_v5` is an explicit diagnostic option. Source rainfall/tyre/phase
warnings are retained independently of reference eligibility; absent rainfall
context is unknown and is never interpreted as a dry track.
