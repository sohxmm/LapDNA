import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { loadCalendar, loadSeasons } from "./api";
import type { CalendarRace, RaceCalendar, SeasonList } from "./api";
import { parseRoute, routeSearch } from "./routing";
import type { StudioRoute } from "./routing";
import "./navigation.css";

const SessionBrowser = lazy(() => import("../comparison/SessionBrowser"));
const ResultsBrowser = lazy(() => import("../results/ResultsBrowser"));
type Resource<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: T };
const message = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "The calendar service is unavailable.";
function dateLabel(value: string | null) {
  if (!value) return "Date unavailable";
  const date = new Date(value + "T12:00:00Z");
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(undefined, {
        day: "numeric",
        month: "short",
        timeZone: "UTC",
      });
}
function timestamp(value: string | null) {
  if (!value) return "Start time not published";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Start time unavailable"
    : date.toLocaleString(undefined, { timeZone: "UTC" }) + " UTC";
}
function qualifyingLabel(race: CalendarRace) {
  return race.qualifying_status === "upcoming"
    ? "Qualifying scheduled"
    : race.qualifying_status === "start_time_passed"
      ? "Scheduled qualifying start has passed"
      : race.qualifying_date
        ? "Qualifying date published · start time unavailable"
      : "Scheduled qualifying start not published";
}

function Metadata({ calendar }: { calendar: RaceCalendar }) {
  return (
    <div className="calendar-provenance">
      <p>
        Calendar via{" "}
        <a href={calendar.source_url} target="_blank" rel="noreferrer">
          Jolpica
        </a>{" "}
        · Retrieved {timestamp(calendar.retrieved_at)}
      </p>
      {calendar.stale && (
        <strong>Saved calendar · source refresh unavailable</strong>
      )}
      {calendar.warnings.map((text) => (
        <p className="calendar-warning" key={text}>
          {text}
        </p>
      ))}
    </div>
  );
}
function RaceCards({
  calendar,
  onRace,
}: {
  calendar: RaceCalendar;
  onRace: (race: CalendarRace) => void;
}) {
  return (
    <section aria-labelledby="race-calendar-title">
      <div className="calendar-section-title">
        <div>
          <p className="eyebrow">02 / SELECT A RACE</p>
          <h2 id="race-calendar-title">{calendar.year} race calendar</h2>
        </div>
        <span>{calendar.races.length} events in source calendar</span>
      </div>
      <p className="calendar-explanation">
        Choose a race to compare its recorded qualifying results. Calendar
        entries may include upcoming events.
      </p>
      {!calendar.races.length ? (
        <div className="calendar-empty">
          <h3>No races published for this season</h3>
          <p>
            The source returned an empty calendar. Select another year or retry
            later.
          </p>
        </div>
      ) : (
        <div className="race-grid">
          {calendar.races.map((race) => (
            <button
              type="button"
              className="race-card"
              key={race.race_id}
              onClick={() => onRace(race)}
            >
              <span className="race-card-top">
                <span>ROUND {String(race.round).padStart(2, "0")}</span>
                <span>{dateLabel(race.race_date)}</span>
              </span>
              <strong>{race.name}</strong>
              <span className="race-circuit">{race.circuit_name}</span>
              <span className="race-place">
                {race.locality}, {race.country}
              </span>
              <span className="race-quali">{qualifyingLabel(race)}</span>
              <span className="race-enter">
                Open qualifying studio <span aria-hidden="true">↗</span>
              </span>
            </button>
          ))}
        </div>
      )}
      <Metadata calendar={calendar} />
    </section>
  );
}
function Studio({
  race,
  calendar,
  onBack,
}: {
  race: CalendarRace;
  calendar: RaceCalendar;
  onBack: () => void;
}) {
  const title = useRef<HTMLHeadingElement>(null);
  const [showLapWorkspace, setShowLapWorkspace] = useState(false);
  useEffect(() => title.current?.focus({ preventScroll: true }), []);
  return (
    <section className="selected-studio" aria-labelledby="studio-title">
      <div className="studio-event">
        <p className="eyebrow">03 / QUALIFYING STUDIO</p>
        <h1 id="studio-title" ref={title} tabIndex={-1}>
          Qualifying studio
        </h1>
        <h2>
          {race.year} · {race.name}
        </h2>
        <p>
          {race.circuit_name} · Round {race.round} · {race.country}
        </p>
        <p className="calendar-quali-context">
          {qualifyingLabel(race)} · {timestamp(race.qualifying_start_at)}
        </p>
        <p className="calendar-explanation">
          Compare imported session and phase-best timings first. Individual runs
          and distance-aligned telemetry will follow as separate data stages.
        </p>
        <div className="studio-links">
          <button type="button" className="calendar-button" onClick={onBack}>
            ← Back to race calendar
          </button>
          <a className="calendar-button" href="?preview=1">
            Explore the fictional demo ↗
          </a>
        </div>
      </div>
      {race.year < 2018 && (
        <p className="calendar-warning">
          This season predates the usual FastF1 telemetry archive. Calendar
          coverage does not promise car-channel data. Recorded qualifying
          classifications can cover earlier years; see imported coverage below.
        </p>
      )}
      <Suspense
        fallback={<p role="status">Loading this race's recorded results…</p>}
      >
        <ResultsBrowser
          key={race.race_id}
          year={race.year}
          round={race.round}
        />
      </Suspense>
      <details
        className="results-later"
        onToggle={(event) => setShowLapWorkspace(event.currentTarget.open)}
      >
        <summary>Individual laps and telemetry · next stage</summary>
        <p>
          Phase-best classifications do not identify matched run 1 or run 2
          attempts. The detailed lap workspace remains separate until actual
          laps and telemetry have been imported and validated.
        </p>
        {showLapWorkspace && (
          <Suspense
            fallback={<p role="status">Loading detailed lap workspace…</p>}
          >
            <SessionBrowser
              year={race.year}
              round={race.round}
              eventName={race.name}
            />
          </Suspense>
        )}
      </details>
      <Metadata calendar={calendar} />
    </section>
  );
}

export default function CalendarWorkspace() {
  const [seasons, setSeasons] = useState<Resource<SeasonList>>({
      status: "loading",
    }),
    [calendar, setCalendar] = useState<Resource<RaceCalendar>>({
      status: "loading",
    });
  const [route, setRoute] = useState<StudioRoute | null>(null),
    [seasonAttempt, setSeasonAttempt] = useState(0),
    [calendarAttempt, setCalendarAttempt] = useState(0);
  const yearControl = useRef<HTMLSelectElement>(null);
  useEffect(() => {
    const c = new AbortController();
    setSeasons({ status: "loading" });
    loadSeasons(c.signal)
      .then((data) => {
        if (!c.signal.aborted) {
          setSeasons({ status: "ready", data });
          setRoute(
            parseRoute(
              window.location.search,
              data.current_year,
              data.min_year,
            ),
          );
        }
      })
      .catch((error) => {
        if (!c.signal.aborted)
          setSeasons({ status: "error", message: message(error) });
      });
    return () => c.abort();
  }, [seasonAttempt]);
  useEffect(() => {
    if (seasons.status !== "ready") return;
    const change = () =>
      setRoute(
        parseRoute(
          window.location.search,
          seasons.data.current_year,
          seasons.data.min_year,
        ),
      );
    window.addEventListener("popstate", change);
    return () => window.removeEventListener("popstate", change);
  }, [seasons]);
  const year = route?.year;
  useEffect(() => {
    if (year === undefined) return;
    const c = new AbortController();
    setCalendar({ status: "loading" });
    loadCalendar(year, c.signal)
      .then((data) => {
        if (!c.signal.aborted) setCalendar({ status: "ready", data });
      })
      .catch((error) => {
        if (!c.signal.aborted)
          setCalendar({ status: "error", message: message(error) });
      });
    return () => c.abort();
  }, [year, calendarAttempt]);
  function navigate(nextYear: number, raceId: string | null = null) {
    if (seasons.status !== "ready") return;
    const search = routeSearch(nextYear, raceId);
    window.history.pushState({}, "", window.location.pathname + search);
    setRoute(
      parseRoute(search, seasons.data.current_year, seasons.data.min_year),
    );
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }
  function backToYear() {
    if (route) navigate(route.year);
    yearControl.current?.focus();
  }
  if (seasons.status === "loading")
    return (
      <section className="calendar-loading" role="status">
        Loading seasons…
      </section>
    );
  if (seasons.status === "error")
    return (
      <section className="calendar-empty">
        <h1>Season list unavailable</h1>
        <p role="alert">{seasons.message}</p>
        <button
          className="calendar-button"
          onClick={() => setSeasonAttempt((n) => n + 1)}
        >
          Retry seasons
        </button>
        <p>
          <a href="?preview=1">Open the explicitly synthetic design preview</a>
        </p>
      </section>
    );
  if (!route) return <p role="status">Selecting the current season…</p>;
  const loaded =
    calendar.status === "ready" && calendar.data.year === route.year;
  const selected = loaded
      ? calendar.data.races.find((race) => race.race_id === route.raceId)
      : undefined,
    studio = route.view === "studio";
  return (
    <div className="calendar-workspace">
      <nav className="calendar-progress" aria-label="Selection progress">
        <ol>
          <li>
            <button type="button" onClick={backToYear}>
              01 <span>Year</span>
            </button>
          </li>
          <li>
            <button
              type="button"
              aria-current={!studio ? "step" : undefined}
              onClick={() => navigate(route.year)}
            >
              02 <span>Race</span>
            </button>
          </li>
          <li>
            <span aria-current={studio ? "step" : undefined}>
              03 <span>Studio</span>
            </span>
          </li>
        </ol>
      </nav>
      <section
        className={
          studio ? "year-selection year-selection-compact" : "year-selection"
        }
      >
        {!studio && (
          <div>
            <p className="eyebrow">01 / CHOOSE A YEAR</p>
            <h1>Start with a season.</h1>
            <p>
              The current year is selected by default. Browse that year's
              calendar, then choose a race.
            </p>
          </div>
        )}
        <label>
          Season
          <select
            id="year-select"
            aria-label="Season year"
            ref={yearControl}
            value={route.year}
            onChange={(e) => navigate(Number(e.target.value))}
          >
            {seasons.data.years.map((y) => (
              <option key={y} value={y}>
                {y}
                {y === seasons.data.current_year ? " · Current year" : ""}
              </option>
            ))}
          </select>
        </label>
      </section>
      {route.warning && (
        <p className="calendar-warning" role="alert">
          {route.warning}
        </p>
      )}
      {calendar.status === "loading" ||
      (calendar.status === "ready" && !loaded) ? (
        <div className="calendar-loading" role="status">
          Loading the {route.year} calendar…
        </div>
      ) : calendar.status === "error" ? (
        <section className="calendar-empty">
          <h2>Calendar unavailable</h2>
          <p role="alert">{calendar.message}</p>
          <button
            className="calendar-button"
            onClick={() => setCalendarAttempt((n) => n + 1)}
          >
            Retry calendar
          </button>
        </section>
      ) : studio && !selected ? (
        <section className="calendar-empty">
          <h2>Race absent from this calendar</h2>
          <p>
            This link does not match a race in the source's {route.year}{" "}
            calendar. The calendar may have changed.
          </p>
          <button
            className="calendar-button"
            onClick={() => navigate(route.year)}
          >
            Choose a listed race
          </button>
        </section>
      ) : studio && selected ? (
        <Studio
          race={selected}
          calendar={calendar.data}
          onBack={() => navigate(route.year)}
        />
      ) : (
        <RaceCards
          calendar={calendar.data}
          onRace={(race) => navigate(route.year, race.race_id)}
        />
      )}
    </div>
  );
}
