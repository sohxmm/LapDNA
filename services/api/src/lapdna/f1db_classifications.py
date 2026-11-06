"""Normalize F1DB's published historical classifications without inventing lap identities."""
from datetime import datetime

from lapdna.classifications import ClassificationDriver, ClassificationEvent, ClassificationSession


def source_millis(value):
    if value is None:
        return None
    if type(value) is not int or not 0 < value <= 1_800_000:
        raise ValueError("F1DB duration must be a positive integer millisecond value or null")
    return value


def normalize_f1db_race(race, rows, drivers, constructors, retrieved_at: datetime,
                       source_url: str, release: str, first_rows=(), second_rows=()):
    year, number, race_id = int(race["year"]), int(race["round"]), int(race["id"])
    modern = year >= 2006
    components = not modern and (bool(first_rows) or bool(second_rows))
    phases = ["Q1", "Q2", "Q3"] if modern else (
        ["QUALIFYING_1", "QUALIFYING_2", "QUALIFYING"] if components else ["QUALIFYING"])
    first = {row["driverId"]: row for row in first_rows}
    second = {row["driverId"]: row for row in second_rows}
    if len(first) != len(first_rows) or len(second) != len(second_rows):
        raise ValueError("Duplicate historical component driver identity")
    records = []
    for row in rows:
        if (row["raceId"], row["year"], row["round"]) != (race_id, year, number):
            raise ValueError("F1DB classification does not match its race metadata")
        driver, constructor = drivers[row["driverId"]], constructors[row["constructorId"]]
        notes = []
        def supported_value(value, label):
            try:
                return source_millis(value)
            except ValueError:
                notes.append(f"{label}: source duration is outside the supported qualifying range; left unavailable, raw value retained in the import cache.")
                return None
        if modern:
            times = {phase: supported_value(row.get(phase.lower() + "Millis"), phase) for phase in phases}
        else:
            times = {"QUALIFYING": supported_value(row.get("timeMillis"), "Overall qualifying")}
            if components:
                times = {"QUALIFYING_1": supported_value(first.get(row["driverId"], {}).get("timeMillis"), "First qualifying"),
                    "QUALIFYING_2": supported_value(second.get(row["driverId"], {}).get("timeMillis"), "Second qualifying"),
                    **times}
        recorded = [phase for phase in phases if times[phase] is not None]
        latest = recorded[-1] if recorded else None
        native_status = row.get("positionText")
        if native_status in {"DSQ", "EX"}:
            status = "disqualified"
            notes.append(f"Source classification status: {native_status}.")
        elif native_status == "DNS":
            status = "did_not_start"
            notes.append("Source classification status: DNS.")
        else:
            status = "timed" if recorded else "no_time"
            if native_status and not str(native_status).isdigit():
                notes.append(f"Source classification status: {native_status}.")
        if not recorded:
            notes.append("No recorded timing value is available for this driver in the source.")
        records.append(ClassificationDriver(
            driver_id="f1db_" + row["driverId"], driver_number=row.get("driverNumber"),
            driver_code=driver.get("abbreviation"), driver_name=driver["name"],
            team_id=constructor["id"], team_name=constructor["name"],
            position=row.get("positionNumber"), phase_times_ms=times,
            latest_timed_phase=latest, latest_time_ms=times[latest] if latest else None,
            status=status, reason=" ".join(notes) or None))
    warnings = [f"F1DB {release} · CC BY 4.0 · normalized for LapDNA.",
        "Published classification facts; individual laps and runs are not imported."]
    if not modern:
        warnings.append("Historical qualifying format: " + race["qualifyingFormat"].replace("_", " ").lower()
                        + ". This is not modern Q1/Q2/Q3.")
    if components:
        warnings.append("First and second qualifying are source session components; Qualifying is the separately published overall classification time.")
    if race["qualifyingFormat"] in {"AGGREGATE", "FOUR_LAPS"}:
        warnings.append("This format's overall qualifying duration is not a single flying-lap time.")
    session = ClassificationSession(session_id=f"{year}-{number}-qualifying", label="Qualifying",
        session_type="qualifying", phases=phases, source="f1db", source_url=source_url,
        retrieved_at=retrieved_at, status="completed", drivers=records, warnings=warnings)
    return ClassificationEvent(year=year, round=number, event_name=race["officialName"],
        circuit_id=race["circuitId"], sessions=[session], warnings=[])
