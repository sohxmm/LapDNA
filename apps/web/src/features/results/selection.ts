import type {
  ClassificationDriver,
  ClassificationSession,
  ResultPhase,
} from "./api";

export type ResultSelection = {
  sessionId: string;
  phase: ResultPhase;
  a: string;
  b: string;
  warning: string | null;
};

export function lapTime(ms: number | null | undefined) {
  if (ms == null) return "No recorded time";
  return (
    Math.floor(ms / 60000) +
    ":" +
    ((ms % 60000) / 1000).toFixed(3).padStart(6, "0")
  );
}

export function seconds(ms: number) {
  return (Math.abs(ms) / 1000).toFixed(3);
}
export function signedGap(ms: number) {
  return (ms < 0 ? "−" : "+") + seconds(ms) + " s";
}
export function phaseLabel(phase: ResultPhase) {
  return phase === "QUALIFYING"
    ? "Qualifying"
    : phase === "QUALIFYING_1"
      ? "First qualifying"
      : phase === "QUALIFYING_2"
        ? "Second qualifying"
        : phase;
}
export function phaseTime(driver: ClassificationDriver, phase: ResultPhase) {
  return driver.phase_times_ms[phase] ?? null;
}
export function eligible(driver: ClassificationDriver, phase: ResultPhase) {
  return driver.status === "timed" && phaseTime(driver, phase) !== null;
}

export function roster(session: ClassificationSession) {
  return [...session.drivers].sort(
    (a, b) =>
      (a.position ?? Infinity) - (b.position ?? Infinity) ||
      a.driver_name.localeCompare(b.driver_name),
  );
}

export function defaultPhase(session: ClassificationSession): ResultPhase {
  return (
    [...session.phases]
      .reverse()
      .find(
        (phase) =>
          session.drivers.filter((driver) => eligible(driver, phase)).length >=
          2,
      ) ?? session.phases[0]
  );
}

export function initialSelection(
  sessions: ClassificationSession[],
  search = "",
): ResultSelection {
  const query = new URLSearchParams(search);
  const savedSession = query.get("session");
  const session =
    sessions.find((item) => item.session_id === savedSession) ??
    sessions.find((item) => item.session_type === "qualifying") ??
    sessions[0];
  if (!session)
    return { sessionId: "", phase: "QUALIFYING", a: "", b: "", warning: null };
  const savedPhase = query.get("phase");
  const phase =
    session.phases.find((item) => item === savedPhase) ?? defaultPhase(session);
  const available = roster(session).filter((driver) => eligible(driver, phase));
  const savedA = query.get("a"),
    savedB = query.get("b");
  const a =
    session.drivers.find((driver) => driver.driver_id === savedA)?.driver_id ??
    available[0]?.driver_id ??
    "";
  const b =
    session.drivers.find(
      (driver) => driver.driver_id === savedB && driver.driver_id !== a,
    )?.driver_id ??
    available.find((driver) => driver.driver_id !== a)?.driver_id ??
    "";
  const invalid =
    (savedSession !== null && savedSession !== session.session_id) ||
    (savedPhase !== null && savedPhase !== phase) ||
    (savedA !== null && savedA !== a) ||
    (savedB !== null && savedB !== b);
  return {
    sessionId: session.session_id,
    phase,
    a,
    b,
    warning: invalid
      ? "Some saved choices are unavailable for this session. Select from its recorded results below."
      : null,
  };
}

export function selectionSearch(search: string, selection: ResultSelection) {
  const query = new URLSearchParams(search);
  query.set("session", selection.sessionId);
  query.set("phase", selection.phase);
  if (selection.a) query.set("a", selection.a);
  else query.delete("a");
  if (selection.b) query.set("b", selection.b);
  else query.delete("b");
  return "?" + query.toString();
}

export function compareTimes(a: number | null, b: number | null) {
  if (a === null || b === null) return null;
  return {
    deltaMs: b - a,
    winner: a === b ? "tie" : a < b ? "a" : "b",
    percent: (100 * Math.abs(b - a)) / Math.min(a, b),
  };
}

export function yearRanges(years: number[]) {
  const sorted = [...new Set(years)].sort((a, b) => a - b);
  if (!sorted.length) return "None imported";
  const groups: string[] = [];
  let start = sorted[0],
    end = start;
  for (const year of sorted.slice(1)) {
    if (year === end + 1) {
      end = year;
      continue;
    }
    groups.push(start === end ? String(start) : start + "–" + end);
    start = end = year;
  }
  groups.push(start === end ? String(start) : start + "–" + end);
  return groups.join(", ");
}
