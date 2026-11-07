export type StudioRoute = {
  year: number;
  raceId: string | null;
  view: "calendar" | "studio";
  warning: string | null;
};

export function isWorkspaceRoute(search: string) {
  const query = new URLSearchParams(search);
  return query.has("year") || query.has("race") || query.get("view") === "calendar" || query.get("view") === "studio";
}

export function parseRoute(
  search: string,
  currentYear: number,
  minYear = 1950,
): StudioRoute {
  const query = new URLSearchParams(search),
    rawYear = query.get("year");
  const requested =
    rawYear === null
      ? currentYear
      : /^\d{4}$/.test(rawYear)
        ? Number(rawYear)
        : NaN;
  const validYear =
    Number.isInteger(requested) &&
    requested >= minYear &&
    requested <= currentYear;
  const year = validYear ? requested : currentYear,
    rawRace = query.get("race");
  const match = rawRace?.match(/^(\d{4})-([1-9]\d?)$/);
  const validRace =
    !!match && Number(match[1]) === year && Number(match[2]) <= 30;
  const raceId = validYear && validRace ? rawRace : null,
    wantsStudio = query.get("view") === "studio";
  const warning = !validYear
    ? "That season is unavailable. Showing the current season."
    : rawRace && !validRace
      ? "That race link is invalid for this season. Choose a race below."
      : wantsStudio && !raceId
        ? "Choose a calendar race to open Telemetry Studio."
        : null;
  return {
    year,
    raceId,
    view: wantsStudio && raceId ? "studio" : "calendar",
    warning,
  };
}

export function routeSearch(year: number, raceId: string | null = null) {
  const query = new URLSearchParams({ year: String(year) });
  if (raceId) {
    query.set("race", raceId);
    query.set("view", "studio");
  }
  return "?" + query.toString();
}

export function sessionsForRace<
  T extends { session: { year: number; round: number } },
>(sessions: T[], year?: number, round?: number): T[] {
  return sessions.filter(
    (entry) =>
      (year === undefined || entry.session.year === year) &&
      (round === undefined || entry.session.round === round),
  );
}
