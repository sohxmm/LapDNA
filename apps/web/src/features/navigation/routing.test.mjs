import test from "node:test";
import assert from "node:assert/strict";
import { parseRoute, routeSearch, sessionsForRace } from "./routing.ts";
test("current server-provided year defaults and historical links survive reload", () => {
  assert.deepEqual(parseRoute("", 2026), {
    year: 2026,
    raceId: null,
    view: "calendar",
    warning: null,
  });
  assert.deepEqual(parseRoute("?year=2024&race=2024-16&view=studio", 2026), {
    year: 2024,
    raceId: "2024-16",
    view: "studio",
    warning: null,
  });
  assert.equal(
    routeSearch(2024, "2024-16"),
    "?year=2024&race=2024-16&view=studio",
  );
});
test("invalid years and mismatched or malformed races cannot silently select another event", () => {
  for (const search of [
    "?year=2027&race=2027-1&view=studio",
    "?year=oops",
    "?year=1949",
  ]) {
    const r = parseRoute(search, 2026);
    assert.equal(r.year, 2026);
    assert.equal(r.view, "calendar");
    assert.ok(r.warning);
  }
  for (const id of ["2023-1", "2024-0", "2024-31", "../../private"]) {
    const r = parseRoute(
      "?year=2024&race=" + encodeURIComponent(id) + "&view=studio",
      2026,
    );
    assert.equal(r.raceId, null);
    assert.equal(r.view, "calendar");
    assert.ok(r.warning);
  }
});
test("changing year clears studio selection and a missing race requires an explicit choice", () => {
  assert.equal(routeSearch(2025), "?year=2025");
  assert.equal(parseRoute("?view=studio", 2026).view, "calendar");
  // A syntactically valid race ID is matched against the fetched source calendar in the component.
  assert.equal(
    parseRoute("?year=2024&race=2024-29&view=studio", 2026).raceId,
    "2024-29",
  );
});
test("imported sessions match exact year and round rather than mutable event names", () => {
  const rows = [
    { session: { year: 2024, round: 16, name: "Same" } },
    { session: { year: 2026, round: 16, name: "Same" } },
    { session: { year: 2024, round: 17, name: "Other" } },
  ];
  assert.deepEqual(sessionsForRace(rows, 2024, 16), [rows[0]]);
  assert.deepEqual(sessionsForRace(rows, 2024, 18), []);
  assert.equal(sessionsForRace(rows).length, 3);
});
