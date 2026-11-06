import { useEffect, useState } from "react";
import { loadClassification, loadCoverage } from "./api";
import type {
  ClassificationCoverage,
  ClassificationDriver,
  ClassificationEvent,
  ClassificationSession,
} from "./api";
import {
  compareTimes,
  defaultPhase,
  eligible,
  initialSelection,
  lapTime,
  phaseLabel,
  phaseTime,
  roster,
  seconds,
  selectionSearch,
  signedGap,
  yearRanges,
} from "./selection";
import type { ResultSelection } from "./selection";
import "./results.css";

type Resource<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: T };
const errorMessage = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "Recorded qualifying results are unavailable.";
const driverLabel = (driver: ClassificationDriver) =>
  driver.driver_name + " · " + (driver.team_name ?? "Team not recorded");
const retrieval = (value: string) =>
  new Date(value).toLocaleString(undefined, { timeZone: "UTC" }) + " UTC";

function Coverage({
  resource,
}: {
  resource: Resource<ClassificationCoverage>;
}) {
  if (resource.status === "loading")
    return (
      <p className="results-muted" role="status">
        Checking imported year coverage…
      </p>
    );
  if (resource.status === "error")
    return (
      <p className="results-muted">
        Year coverage could not be loaded. This race's recorded results can
        still be compared.
      </p>
    );
  const coverage = resource.data;
  return (
    <>
      <p className="results-muted">
        Historical formats and missing values vary; see imported coverage.
        Current-season calendars may include upcoming events.
      </p>
      <details className="results-coverage">
        <summary>
          Imported years · Qualifying {yearRanges(coverage.qualifying_years)} ·
          Sprint Qualifying {yearRanges(coverage.sprint_qualifying_years)}
        </summary>
        <p>
          Coverage describes imported classifications. A recorded phase best is
          not an inventory of individual runs. Earlier formats and missing
          phases keep their source limitations.
        </p>
        <div className="results-table-wrap">
          <table>
            <caption>Imported results by season</caption>
            <thead>
              <tr>
                <th>Year</th>
                <th>Imported events</th>
                <th>Qualifying / calendar</th>
                <th>Sprint Qualifying</th>
                <th>Driver results</th>
              </tr>
            </thead>
            <tbody>
              {[...coverage.seasons]
                .sort((a, b) => b.year - a.year)
                .map((season) => (
                  <tr key={season.year}>
                    <th scope="row">{season.year}</th>
                    <td>{season.event_count}</td>
                    <td>
                      {season.qualifying_sessions} /{" "}
                      {season.calendar_events ?? "unknown"}
                    </td>
                    <td>{season.sprint_qualifying_sessions}</td>
                    <td>{season.driver_results}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        {coverage.warnings.map((text, i) => (
          <p className="results-warning" key={i}>
            {text}
          </p>
        ))}
      </details>
    </>
  );
}

function TimingCard({
  driver,
  phase,
  slot,
}: {
  driver: ClassificationDriver;
  phase: ResultSelection["phase"];
  slot: "a" | "b";
}) {
  const value = phaseTime(driver, phase);
  return (
    <article className={"results-time-card results-slot-" + slot}>
      <p>
        {slot.toUpperCase()} / {phaseLabel(phase)} BEST
      </p>
      <h3>{driver.driver_name}</h3>
      <span>
        {driver.team_name ?? "Team not recorded"}
        {driver.driver_number ? " · #" + driver.driver_number : ""}
      </span>
      <strong>{lapTime(value)}</strong>
      {driver.status !== "timed" && (
        <small>{driver.reason ?? driver.status.replaceAll("_", " ")}</small>
      )}
      {value === null && (
        <small>
          {driver.reason ??
            "No recorded " + phaseLabel(phase) + " time for this driver."}
        </small>
      )}
    </article>
  );
}

function GapChart({
  session,
  a,
  b,
  phase,
}: {
  session: ClassificationSession;
  a: ClassificationDriver;
  b: ClassificationDriver;
  phase: ResultSelection["phase"];
}) {
  const times = session.drivers
    .filter((driver) => eligible(driver, phase))
    .map((driver) => phaseTime(driver, phase))
    .filter((value): value is number => value !== null);
  const fastest = Math.min(...times);
  const selected = [
    { driver: a, slot: "a" },
    { driver: b, slot: "b" },
  ] as const;
  const max = Math.max(
    50,
    ...selected.map(({ driver }) => phaseTime(driver, phase)! - fastest),
  );
  return (
    <figure className="results-gap-chart">
      <figcaption>
        Gap to fastest recorded {phaseLabel(phase)} time{" "}
        <span>{lapTime(fastest)} · same-phase timing only</span>
      </figcaption>
      <div className="results-gap-axis">
        <span>0.000 s</span>
        <span>+{seconds(max)} s</span>
      </div>
      {selected.map(({ driver, slot }) => {
        const gap = phaseTime(driver, phase)! - fastest;
        return (
          <div className={"results-gap-row results-slot-" + slot} key={slot}>
            <div>
              <strong>{driver.driver_code ?? driver.driver_name}</strong>
              <span>{signedGap(gap)}</span>
            </div>
            <div className="results-gap-track" aria-hidden="true">
              <span style={{ width: (100 * gap) / max + "%" }} />
              <i style={{ left: (100 * gap) / max + "%" }} />
            </div>
          </div>
        );
      })}
      <p className="results-muted">
        These bars compare recorded phase-best durations. They do not show where
        the time was gained on track.
      </p>
    </figure>
  );
}

function ClassificationTable({
  session,
  selected,
}: {
  session: ClassificationSession;
  selected: ResultSelection;
}) {
  return (
    <section
      className="results-classification"
      aria-labelledby="classification-title"
    >
      <div className="results-section-heading">
        <div>
          <p className="eyebrow">SOURCE CLASSIFICATION</p>
          <h3 id="classification-title">
            Every driver, their team, each recorded phase
          </h3>
        </div>
        <span>{session.drivers.length} drivers</span>
      </div>
      <p className="results-muted">
        Position is the source's session classification. An empty phase means no
        recorded time; it is never filled from another phase.
      </p>
      <div className="results-table-wrap">
        <table>
          <caption>{session.label} · recorded phase-best times</caption>
          <thead>
            <tr>
              <th>Pos</th>
              <th>Driver</th>
              <th>Team at this event</th>
              {session.phases.map((phase) => (
                <th key={phase}>{phaseLabel(phase)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {roster(session).map((driver) => (
              <tr
                key={driver.driver_id}
                className={
                  driver.driver_id === selected.a
                    ? "results-selected-a"
                    : driver.driver_id === selected.b
                      ? "results-selected-b"
                      : ""
                }
              >
                <td>{driver.position ?? "—"}</td>
                <th scope="row">
                  {driver.driver_name}
                  <small>
                    {driver.driver_code ?? ""}
                    {driver.driver_number ? " · #" + driver.driver_number : ""}
                    {driver.status !== "timed"
                      ? " · " + driver.status.replaceAll("_", " ")
                      : ""}
                  </small>
                  {driver.reason && <small>{driver.reason}</small>}
                </th>
                <td>{driver.team_name ?? "Not recorded"}</td>
                {session.phases.map((phase) => (
                  <td
                    key={phase}
                    className={
                      phase === selected.phase ? "results-active-phase" : ""
                    }
                    title={
                      phaseTime(driver, phase) === null
                        ? (driver.reason ?? "No recorded time for this phase")
                        : undefined
                    }
                  >
                    {phaseTime(driver, phase) === null
                      ? "—"
                      : lapTime(phaseTime(driver, phase))}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function EventResults({ event }: { event: ClassificationEvent }) {
  const [selected, setSelected] = useState<ResultSelection>(() =>
    initialSelection(event.sessions, window.location.search),
  );
  useEffect(() => {
    const restore = () =>
      setSelected(initialSelection(event.sessions, window.location.search));
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, [event]);
  const session =
    event.sessions.find((item) => item.session_id === selected.sessionId) ??
    event.sessions[0];
  if (!session)
    return (
      <section className="recorded-results results-empty">
        <p className="eyebrow">RECORDED RESULTS</p>
        <h2>No qualifying classification imported for this race</h2>
        <p>
          Choose another race or retry after the source publishes its results.
          Calendar scheduling does not establish data availability.
        </p>
        {event.warnings.map((text, i) => (
          <p className="results-muted" key={i}>
            {text}
          </p>
        ))}
      </section>
    );
  const ordered = roster(session),
    a = session.drivers.find((driver) => driver.driver_id === selected.a),
    b = session.drivers.find((driver) => driver.driver_id === selected.b);
  const timeA = a ? phaseTime(a, selected.phase) : null,
    timeB = b ? phaseTime(b, selected.phase) : null;
  const comparison =
    a &&
    b &&
    a.driver_id !== b.driver_id &&
    eligible(a, selected.phase) &&
    eligible(b, selected.phase)
      ? compareTimes(timeA, timeB)
      : null;
  function update(next: ResultSelection) {
    setSelected({ ...next, warning: null });
    window.history.pushState(
      {},
      "",
      window.location.pathname + selectionSearch(window.location.search, next),
    );
  }
  function changeSession(id: string) {
    const next = event.sessions.find((item) => item.session_id === id);
    if (!next) return;
    const phase = defaultPhase(next),
      timed = roster(next).filter((driver) => eligible(driver, phase));
    update({
      sessionId: id,
      phase,
      a: timed[0]?.driver_id ?? "",
      b: timed[1]?.driver_id ?? "",
      warning: null,
    });
  }
  const label = phaseLabel(selected.phase);
  const notices = [...new Set([...event.warnings, ...session.warnings])]
    .filter((text) => !text.startsWith("F1DB ") && text !== "Published classification facts; individual laps and runs are not imported.")
    .map((text) => text.includes("native exclusion/disqualification status")
      ? "Disqualified and excluded results remain visible in the table but cannot be selected for comparison."
      : text);
  return (
    <section
      className="recorded-results"
      aria-labelledby="recorded-results-title"
    >
      <div className="results-section-heading">
        <div>
          <p className="eyebrow">RECORDED QUALIFYING / PHASE BESTS</p>
          <h2 id="recorded-results-title">Compare the recorded times</h2>
        </div>
        <span className="results-real-tag">Imported source results</span>
      </div>
      <p className="results-intro">
        Choose a session, a qualifying phase and two drivers. Each time is that
        driver's recorded best in the selected phase. Individual runs and
        telemetry are the next stage.
      </p>
      <div className="results-session-controls">
        <label>
          Session
          <select
            aria-label="Results session"
            value={session.session_id}
            onChange={(e) => changeSession(e.target.value)}
          >
            {event.sessions.map((item) => (
              <option key={item.session_id} value={item.session_id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Phase
          <select
            aria-label="Qualifying phase"
            value={selected.phase}
            onChange={(e) =>
              update({
                ...selected,
                phase: e.target.value as ResultSelection["phase"],
              })
            }
          >
            {session.phases.map((phase) => (
              <option
                key={phase}
                value={phase}
                disabled={
                  !session.drivers.some(
                    (driver) => phaseTime(driver, phase) !== null,
                  )
                }
              >
                {phaseLabel(phase)} · best recorded time
                {session.drivers.some(
                  (driver) => phaseTime(driver, phase) !== null,
                )
                  ? ""
                  : " · unavailable"}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!event.sessions.some(
        (item) => item.session_type === "sprint_qualifying",
      ) && (
        <p className="results-muted">
          No Sprint Qualifying classification is imported for this event.
          Sessions that are absent are not created from regular qualifying
          results.
        </p>
      )}
      {selected.warning && (
        <p className="results-warning" role="alert">
          {selected.warning}
        </p>
      )}
      {notices.map((text, i) => (
        <p className="results-warning" key={i}>
          {text}
        </p>
      ))}
      {session.status === "partial" && (
        <p className="results-warning">
          This imported classification is partial. Only recorded times can be
          compared.
        </p>
      )}
      <div className="results-driver-controls">
        {(["a", "b"] as const).map((slot) => (
          <label className={"results-slot-" + slot} key={slot}>
            Driver {slot.toUpperCase()}
            <select
              aria-label={"Driver " + slot.toUpperCase()}
              value={selected[slot]}
              onChange={(e) => update({ ...selected, [slot]: e.target.value })}
            >
              {!selected[slot] && (
                <option value="">Choose a driver with a recorded time</option>
              )}
              {ordered.map((driver) => (
                <option
                  key={driver.driver_id}
                  value={driver.driver_id}
                  disabled={
                    driver.driver_id === selected[slot === "a" ? "b" : "a"] ||
                    !eligible(driver, selected.phase)
                  }
                >
                  {driverLabel(driver)}
                  {driver.status === "disqualified" ||
                  driver.status === "did_not_start"
                    ? " · " + driver.status.replaceAll("_", " ")
                    : phaseTime(driver, selected.phase) === null
                      ? " · no " + label + " time"
                      : ""}
                </option>
              ))}
            </select>
          </label>
        ))}
        <button
          type="button"
          className="results-swap"
          disabled={!selected.a || !selected.b}
          onClick={() => update({ ...selected, a: selected.b, b: selected.a })}
        >
          Swap drivers ⇄
        </button>
      </div>
      <div className="results-time-cards">
        {a && <TimingCard driver={a} phase={selected.phase} slot="a" />}
        {b && <TimingCard driver={b} phase={selected.phase} slot="b" />}
      </div>
      {comparison && a && b ? (
        <div className="results-comparison" aria-live="polite">
          <p className="results-gap-label">{label} / RECORDED GAP</p>
          <strong
            className={
              comparison.winner === "tie"
                ? ""
                : "results-slot-" + comparison.winner
            }
          >
            {comparison.winner === "tie"
              ? "Equal recorded times"
              : seconds(comparison.deltaMs) + " s"}
          </strong>
          <h3>
            {comparison.winner === "tie"
              ? a.driver_name +
                " and " +
                b.driver_name +
                " recorded the same time."
              : (comparison.winner === "a" ? a.driver_name : b.driver_name) +
                " was faster in " +
                label +
                "."}
          </h3>
          <p>
            {a.driver_name}: {lapTime(timeA)} · {b.driver_name}:{" "}
            {lapTime(timeB)}. B − A: {signedGap(comparison.deltaMs)}; positive
            favours {a.driver_code ?? a.driver_name}.
          </p>
          <GapChart session={session} a={a} b={b} phase={selected.phase} />
          <p className="results-analysis-note">
            Recorded timing establishes this phase's gap. It cannot identify a
            corner loss, braking pattern or cause without the corresponding lap
            telemetry. These phase bests are not matched “run 1” or “run 2”
            attempts.
          </p>
        </div>
      ) : (
        <div className="results-empty" role="status">
          <h3>A same-phase comparison needs two eligible recorded times</h3>
          <p>
            {!a || !b
              ? "Choose two different drivers with a recorded " +
                label +
                " time."
              : "A selected driver has no eligible recorded " +
                label +
                " time. Choose another phase or driver; an earlier phase will not be substituted."}
          </p>
        </div>
      )}
      <ClassificationTable session={session} selected={selected} />
      <div className="results-source">
        <p>
          Source:{" "}
          <a href={session.source_url} target="_blank" rel="noreferrer">
            {
              { jolpica: "Jolpica", openf1: "OpenF1", f1db: "F1DB" }[
                session.source
              ]
            }
          </a>{" "}
          · Retrieved {retrieval(session.retrieved_at)} ·{" "}
          {session.status === "completed"
            ? "Completed classification snapshot"
            : "Partial classification snapshot"}
        </p>
        <p>
          Drivers and teams come from this event's results, including historical
          team changes. Qualifying classification can differ from the race
          starting grid.
        </p>
        {session.source === "f1db" && (
          <p>
            F1DB data ·{" "}
            <a
              href="https://creativecommons.org/licenses/by/4.0/"
              target="_blank"
              rel="noreferrer"
            >
              CC BY 4.0
            </a>{" "}
            · normalized for LapDNA.
          </p>
        )}
      </div>
    </section>
  );
}

export default function ResultsBrowser({
  year,
  round,
}: {
  year: number;
  round: number;
}) {
  const [results, setResults] = useState<Resource<ClassificationEvent>>({
    status: "loading",
  });
  const [coverage, setCoverage] = useState<Resource<ClassificationCoverage>>({
    status: "loading",
  });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setResults({ status: "loading" });
    loadClassification(year, round, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setResults({ status: "ready", data });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setResults({ status: "error", message: errorMessage(error) });
      });
    return () => controller.abort();
  }, [year, round, attempt]);
  useEffect(() => {
    const controller = new AbortController();
    loadCoverage(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setCoverage({ status: "ready", data });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setCoverage({ status: "error", message: errorMessage(error) });
      });
    return () => controller.abort();
  }, []);
  return (
    <div className="results-workspace">
      <Coverage resource={coverage} />
      {results.status === "loading" ? (
        <section className="recorded-results" role="status">
          Loading this race's recorded qualifying results…
        </section>
      ) : results.status === "error" ? (
        <section className="recorded-results results-empty">
          <h2>Recorded results unavailable</h2>
          <p role="alert">{results.message}</p>
          <button
            className="results-swap"
            onClick={() => setAttempt((value) => value + 1)}
          >
            Retry recorded results
          </button>
        </section>
      ) : (
        <EventResults key={year + "-" + round} event={results.data} />
      )}
    </div>
  );
}
