import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { loadCalendar, loadSeasons } from "./api";
import type { CalendarRace, RaceCalendar, SeasonList } from "./api";
import { parseRoute, routeSearch } from "./routing";
import type { StudioRoute } from "./routing";
import "./navigation.css";
import {loadSessions} from '../comparison/api';

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
      {calendar.stale && (
        <strong>Saved calendar · source refresh unavailable</strong>
      )}
      <details><summary>Calendar details</summary>
      <p>
        Calendar via{" "}
        <a href={calendar.source_url} target="_blank" rel="noreferrer">
          Jolpica
        </a>{" "}
        · Retrieved {timestamp(calendar.retrieved_at)}
      </p>
      {calendar.warnings.map((text) => (
        <p className="calendar-warning" key={text}>
          {text}
        </p>
      ))}
      </details>
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
          <p className="eyebrow">02 / RACE</p>
          <h2 id="race-calendar-title">The calendar.</h2>
        </div>
        <span>{calendar.year} · {calendar.races.length} events</span>
      </div>
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
              <span className="race-quali">{race.qualifying_status === "upcoming" ? "Upcoming qualifying" : "Qualifying · " + dateLabel(race.qualifying_date)}</span>
              <span className="race-enter">
                Compare <span aria-hidden="true">↗</span>
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
  const [availability,setAvailability]=useState<'loading'|'available'|'missing'|'error'>('loading');
  const [mode,setMode]=useState<'timing'|'telemetry'|null>(()=>{
    const value=new URLSearchParams(window.location.search).get('analysis');
    return value==='timing'||value==='telemetry'?value:null;
  });
  useEffect(()=>{
    const controller=new AbortController();setAvailability('loading');
    loadSessions(controller.signal).then(data=>{
      if(!controller.signal.aborted)setAvailability(data.sessions.some(entry=>entry.session.year===race.year&&entry.session.round===race.round)?'available':'missing');
    }).catch(()=>{if(!controller.signal.aborted)setAvailability('error');});
    return()=>controller.abort();
  },[race.year,race.round]);
  useEffect(()=>{
    const restore=()=>{const value=new URLSearchParams(window.location.search).get('analysis');setMode(value==='timing'||value==='telemetry'?value:null);};
    window.addEventListener('popstate',restore);return()=>window.removeEventListener('popstate',restore);
  },[]);
  const activeMode=mode??(availability==='available'?'telemetry':'timing');
  function changeView(next:'timing'|'telemetry') {
    const query=new URLSearchParams(window.location.search);query.set('analysis',next);
    window.history.pushState({},'',window.location.pathname+'?'+query.toString());setMode(next);
  }
  useEffect(() => title.current?.focus({ preventScroll: true }), []);
  return (
    <section className="selected-studio" aria-labelledby="studio-title">
      <div className="studio-event">
        <p className="eyebrow">{race.year} / ROUND {String(race.round).padStart(2,"0")}</p>
        <h1 id="studio-title" ref={title} tabIndex={-1}>
          {race.name}
        </h1>
        <p>
          {race.circuit_name} · {race.country}
        </p>
        <div className="studio-links">
          <button type="button" className="calendar-button" onClick={onBack}>
            ← Race calendar
          </button>
          <a className="calendar-button" href="?preview=1">
            Synthetic demo ↗
          </a>
        </div>
      </div>
      {race.year < 2018 && (
        <p className="calendar-tier">Timing only · telemetry coverage begins in 2018.</p>
      )}
      <div className="studio-view-tabs" role="group" aria-label="Comparison view">
        <button type="button" aria-pressed={activeMode==='timing'} onClick={()=>changeView('timing')}>Recorded timings</button>
        <button type="button" aria-pressed={activeMode==='telemetry'} disabled={availability==='missing'||race.year<2018} title={availability==='missing'?'Lap telemetry is not imported for this event':undefined} onClick={()=>changeView('telemetry')}>Lap telemetry{availability==='available'?' · Available':''}</button>
      </div>
      {availability==='loading'&&!mode?<p role="status">Loading available comparisons…</p>:activeMode==='telemetry'?<Suspense fallback={<p role="status">Loading lap comparison…</p>}><SessionBrowser year={race.year} round={race.round} eventName={race.name}/></Suspense>:
      <Suspense
        fallback={<p role="status">Loading this race's recorded results…</p>}
      >
        <ResultsBrowser
          key={race.race_id}
          year={race.year}
          round={race.round}
        />
      </Suspense>}
      <details className="calendar-schedule-details"><summary>Session schedule</summary><p>{qualifyingLabel(race)} · {timestamp(race.qualifying_start_at)}</p></details>
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
            <p className="eyebrow">01 / SEASON</p>
            <h1>Pick your season.</h1>
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
          key={selected.race_id}
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
