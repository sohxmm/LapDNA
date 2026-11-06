import type { components } from "../../../../../packages/contracts/api";

export type ClassificationEvent = components["schemas"]["ClassificationEvent"];
export type ClassificationSession =
  components["schemas"]["ClassificationSession"];
export type ClassificationDriver =
  components["schemas"]["ClassificationDriver"];
export type ClassificationCoverage =
  components["schemas"]["ClassificationCoverage"];
export type ResultPhase = ClassificationSession["phases"][number];

const phases = new Set([
  "Q1",
  "Q2",
  "Q3",
  "SQ1",
  "SQ2",
  "SQ3",
  "QUALIFYING",
  "QUALIFYING_1",
  "QUALIFYING_2",
]);
const object = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const strings = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((item) => typeof item === "string");
const nullableString = (value: unknown) =>
  value === null || typeof value === "string";
const time = (value: unknown) =>
  value === null ||
  (typeof value === "number" && Number.isSafeInteger(value) && value > 0);

async function read(path: string, signal: AbortSignal) {
  const response = await fetch("/api/v1/classifications/" + path, { signal });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      object(body) && object(body.error) ? body.error.message : null;
    throw new Error(
      typeof message === "string"
        ? message
        : "Recorded results are unavailable (HTTP " + response.status + ").",
    );
  }
  if (!object(body) || body.schema_version !== "1.0.0")
    throw new Error("Unsupported recorded-results response.");
  return body;
}

export async function loadClassification(
  year: number,
  round: number,
  signal: AbortSignal,
): Promise<ClassificationEvent> {
  const body = await read(year + "/" + round, signal);
  if (
    body.year !== year ||
    body.round !== round ||
    !strings(body.warnings) ||
    !Array.isArray(body.sessions) ||
    !body.sessions.every(
      (session) =>
        object(session) &&
        typeof session.session_id === "string" &&
        typeof session.label === "string" &&
        ["qualifying", "sprint_qualifying"].includes(
          String(session.session_type),
        ) &&
        strings(session.phases) &&
        session.phases.length > 0 &&
        session.phases.every((phase) => phases.has(phase)) &&
        new Set(session.phases).size === session.phases.length &&
        typeof session.source_url === "string" &&
        typeof session.retrieved_at === "string" &&
        ["jolpica", "openf1", "f1db"].includes(String(session.source)) &&
        strings(session.warnings) &&
        Array.isArray(session.drivers) &&
        session.drivers.every(
          (driver) =>
            object(driver) &&
            typeof driver.driver_id === "string" &&
            typeof driver.driver_name === "string" &&
            ["timed", "no_time", "disqualified", "did_not_start"].includes(
              String(driver.status),
            ) &&
            nullableString(driver.driver_number) &&
            nullableString(driver.driver_code) &&
            nullableString(driver.team_id) &&
            nullableString(driver.team_name) &&
            (driver.position === null ||
              (Number.isInteger(driver.position) &&
                Number(driver.position) > 0)) &&
            object(driver.phase_times_ms) &&
            (session.phases as string[]).every(
              (phase) =>
                Object.hasOwn(driver.phase_times_ms as object, phase) &&
                time((driver.phase_times_ms as Record<string, unknown>)[phase]),
            ),
        ) &&
        new Set(
          session.drivers.map(
            (driver) => (driver as Record<string, unknown>).driver_id,
          ),
        ).size === session.drivers.length,
    ) ||
    new Set(
      body.sessions.map(
        (session) => (session as Record<string, unknown>).session_id,
      ),
    ).size !== body.sessions.length
  ) {
    throw new Error(
      "Recorded results do not match this race or contain unsupported timing data.",
    );
  }
  return body as ClassificationEvent;
}

export async function loadCoverage(
  signal: AbortSignal,
): Promise<ClassificationCoverage> {
  const body = await read("coverage", signal);
  const years = (value: unknown) =>
    Array.isArray(value) &&
    value.every(
      (year) =>
        typeof year === "number" &&
        Number.isInteger(year) &&
        year >= 1950 &&
        year <= 2100,
    );
  if (
    !years(body.years) ||
    !years(body.qualifying_years) ||
    !years(body.sprint_qualifying_years) ||
    !Array.isArray(body.seasons) ||
    !Array.isArray(body.sources) ||
    !strings(body.warnings)
  ) {
    throw new Error("Recorded-results coverage is unavailable.");
  }
  return body as ClassificationCoverage;
}
