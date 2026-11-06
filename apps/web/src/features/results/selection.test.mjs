import test from "node:test";
import assert from "node:assert/strict";
import {
  compareTimes,
  defaultPhase,
  eligible,
  initialSelection,
  lapTime,
  phaseLabel,
  phaseTime,
  roster,
  selectionSearch,
  yearRanges,
} from "./selection.ts";

const driver = (id, position, times, extras = {}) => ({
  driver_id: id,
  driver_name: id,
  team_name: "Team at this event",
  position,
  phase_times_ms: times,
  status: "timed",
  ...extras,
});
const qualifying = {
  session_id: "2026-19-qualifying",
  session_type: "qualifying",
  phases: ["Q1", "Q2", "Q3"],
  drivers: [
    driver("hamilton", 1, { Q1: 77341, Q2: 76953, Q3: 76514 }),
    driver("rival", 2, { Q1: 77100, Q2: 76800, Q3: 76633 }),
    driver("eliminated", 19, { Q1: 78500, Q2: null, Q3: null }),
    driver(
      "disqualified",
      null,
      { Q1: 76000, Q2: 75900, Q3: 75800 },
      { status: "disqualified" },
    ),
  ],
};

test("default phase uses highest phase with two eligible times, excluding disqualified records", () => {
  assert.equal(defaultPhase(qualifying), "Q3");
  const oneQ3 = {
    ...qualifying,
    drivers: qualifying.drivers.map((d) =>
      d.driver_id === "rival"
        ? { ...d, phase_times_ms: { ...d.phase_times_ms, Q3: null } }
        : d,
    ),
  };
  assert.equal(defaultPhase(oneQ3), "Q2");
  assert.deepEqual(initialSelection([qualifying]), {
    sessionId: qualifying.session_id,
    phase: "Q3",
    a: "hamilton",
    b: "rival",
    warning: null,
  });
});

test("a missing later phase never substitutes a faster earlier phase", () => {
  assert.equal(phaseTime(qualifying.drivers[2], "Q3"), null);
  assert.equal(
    compareTimes(76514, phaseTime(qualifying.drivers[2], "Q3")),
    null,
  );
  assert.equal(eligible(qualifying.drivers[3], "Q3"), false);
  assert.equal(phaseTime(qualifying.drivers[3], "Q3"), 75800); // Preserve source value in classification table.
});

test("session and phase selection survives URL restoration with event-specific driver identity", () => {
  const sprint = {
    ...qualifying,
    session_id: "2026-6-sprint-qualifying",
    session_type: "sprint_qualifying",
    phases: ["SQ1", "SQ2", "SQ3"],
    drivers: [
      driver(
        "hamilton",
        2,
        { SQ1: 80000, SQ2: 79000, SQ3: 78000 },
        { team_name: "Earlier team" },
      ),
      driver("rival", 1, { SQ1: 79000, SQ2: 78000, SQ3: 77000 }),
    ],
  };
  const choice = {
    sessionId: sprint.session_id,
    phase: "SQ2",
    a: "rival",
    b: "hamilton",
    warning: null,
  };
  const query = selectionSearch("?year=2026&race=2026-6&view=studio", choice);
  assert.match(query, /year=2026&race=2026-6&view=studio/);
  assert.deepEqual(initialSelection([qualifying, sprint], query), choice);
  assert.equal(
    sprint.drivers.find((d) => d.driver_id === choice.b).team_name,
    "Earlier team",
  );
});

test("invalid saved session, phase and duplicate driver choices are disclosed and cannot form a same-driver pair", () => {
  const choice = initialSelection(
    [qualifying],
    "?session=missing&phase=SQ3&a=hamilton&b=hamilton",
  );
  assert.equal(choice.sessionId, qualifying.session_id);
  assert.equal(choice.phase, "Q3");
  assert.notEqual(choice.a, choice.b);
  assert.ok(choice.warning);
});

test("historical single-session format stays QUALIFYING and source duplicate positions are preserved", () => {
  const legacy = {
    session_id: "1994-1-qualifying",
    session_type: "qualifying",
    phases: ["QUALIFYING"],
    drivers: [
      driver("old-a", 21, { QUALIFYING: 80001 }),
      driver("old-b", 21, { QUALIFYING: 80002 }),
    ],
  };
  assert.equal(defaultPhase(legacy), "QUALIFYING");
  assert.deepEqual(
    roster(legacy).map((d) => d.position),
    [21, 21],
  );
});

test("recorded gap uses B-minus-A, swaps exactly and preserves a timing tie", () => {
  assert.equal(compareTimes(76514, 76633).deltaMs, 119);
  assert.equal(compareTimes(76633, 76514).deltaMs, -119);
  assert.equal(compareTimes(76514, 76633).winner, "a");
  assert.equal(compareTimes(76514, 76514).winner, "tie");
  assert.equal(lapTime(76514), "1:16.514");
  assert.equal(lapTime(null), "No recorded time");
});

test("two-component historical qualifying retains its actual phases rather than modern knockout labels", () => {
  const historical = {
    session_id: "2005-1-qualifying",
    session_type: "qualifying",
    phases: ["QUALIFYING_1", "QUALIFYING_2"],
    drivers: [
      driver("old-a", 1, { QUALIFYING_1: 80000, QUALIFYING_2: 81000 }),
      driver("old-b", 2, { QUALIFYING_1: 80500, QUALIFYING_2: 81500 }),
    ],
  };
  assert.equal(defaultPhase(historical), "QUALIFYING_2");
  assert.equal(phaseLabel("QUALIFYING_1"), "First qualifying");
  assert.equal(phaseLabel("QUALIFYING_2"), "Second qualifying");
  const choice = initialSelection([historical], "?phase=QUALIFYING_1");
  assert.equal(choice.phase, "QUALIFYING_1");
  assert.equal(phaseTime(historical.drivers[0], choice.phase), 80000);
});

test("year coverage does not imply missing intervening years are imported", () => {
  assert.equal(yearRanges([2026, 2023, 2024, 2024]), "2023–2024, 2026");
  assert.equal(yearRanges([]), "None imported");
});
