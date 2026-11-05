import type { components } from '../../../../../packages/contracts/api';
import type { Samples, TraceView } from '../telemetry/view';

type Schema = components['schemas'];
export type PairResponse = Schema['CompareResponse'];
export type Telemetry = Schema['ComparisonArtifact'];

export function orient(value: number | null, swapped: boolean) {
  return value === null ? null : swapped ? -value : value;
}

function samples(channels: Schema['DriverChannels']): Samples {
  return { speed: channels.speed_kph, throttle: channels.throttle_pct, gear: channels.gear, brake: channels.brake };
}

export function traceView(artifact: Telemetry, swapped: boolean): TraceView {
  const regions = new Map(artifact.segments.map(segment => [segment.segment_id, segment]));
  const first = swapped ? artifact.lap_b : artifact.lap_a;
  const second = swapped ? artifact.lap_a : artifact.lap_b;
  return {
    nameA: first.driver_code, nameB: second.driver_code, distance: artifact.distance_m,
    a: samples(swapped ? artifact.channels_b : artifact.channels_a),
    b: samples(swapped ? artifact.channels_a : artifact.channels_b),
    delta: artifact.delta_ms.map(ms => orient(ms, swapped)), boundaries: artifact.sector_boundaries_m,
    turns: artifact.corners.flatMap(corner => {
      const region = regions.get(corner.segment_id);
      return region ? [{ label: corner.label, at: corner.distance_m, start: region.start_m,
        end: region.end_m, speedClass: corner.speed_class }] : [];
    }),
    bins: artifact.estimated_minisectors.map(bin => ({ start: bin.start_m, end: bin.end_m, gain: orient(bin.gain_ms, swapped) })),
  };
}
