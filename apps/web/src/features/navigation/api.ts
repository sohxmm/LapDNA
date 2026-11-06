import type { components } from "../../../../../packages/contracts/api";
export type SeasonList = components["schemas"]["Seasons"];
export type RaceCalendar = components["schemas"]["CalendarSeason"];
export type CalendarRace = components["schemas"]["CalendarRace"];
function object(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === "object";
}
async function read(
  path: string,
  signal: AbortSignal,
): Promise<Record<string, unknown>> {
  const response = await fetch("/api/v1/" + path, { signal }),
    body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error =
      object(body) && object(body.error) ? body.error.message : null;
    throw new Error(
      typeof error === "string"
        ? error
        : "The calendar service returned HTTP " + response.status + ".",
    );
  }
  if (!object(body) || body.schema_version !== "1.0.0")
    throw new Error("Unsupported calendar response.");
  return body;
}
export async function loadSeasons(signal: AbortSignal): Promise<SeasonList> {
  const body = await read("seasons", signal);
  if (
    !Number.isInteger(body.current_year) ||
    body.min_year !== 1950 ||
    !Array.isArray(body.years) ||
    body.years[0] !== body.current_year ||
    body.years.at(-1) !== 1950 ||
    !body.years.every(
      (year: unknown) =>
        typeof year === "number" &&
        Number.isInteger(year) &&
        year >= 1950 &&
        year <= Number(body.current_year),
    )
  )
    throw new Error("Unsupported season list.");
  return body as SeasonList;
}
export async function loadCalendar(
  year: number,
  signal: AbortSignal,
): Promise<RaceCalendar> {
  const body = await read("calendar/" + year, signal);
  if (
    body.year !== year ||
    body.source !== "jolpica" ||
    typeof body.retrieved_at !== "string" ||
    typeof body.stale !== "boolean" ||
    !Array.isArray(body.warnings) ||
    !Array.isArray(body.races) ||
    !body.races.every(
      (race: unknown) =>
        object(race) &&
        race.year === year &&
        typeof race.round === "number" &&
        race.race_id === year + "-" + race.round &&
        typeof race.name === "string",
    )
  )
    throw new Error("The calendar does not match the selected season.");
  return body as RaceCalendar;
}
