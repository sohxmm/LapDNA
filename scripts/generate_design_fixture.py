"""Generate only the deliberately fictional chart fixture. No external data or API."""
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "apps/web/src/features/telemetry/design-fixture.json"
LENGTH = 2400
STEP = 10
# marker, corner center, half-window, reference minimum, constructed B-A speed offset
TURNS = [(220, 120, 108, 9), (600, 130, 192, -13), (980, 150, 260, -16),
         (1380, 120, 120, 8), (1750, 140, 206, -14), (2120, 150, 265, -17)]


def make():
    distance = list(range(0, LENGTH + STEP, STEP))
    a, b = [], []
    turns = []
    for n, (center, width, ref, _) in enumerate(TURNS, 1):
        turns.append(dict(label=f"T{n}", at=center, start=center-width, end=center+width,
                          speedClass="low" if ref < 150 else "medium" if ref < 250 else "high"))
    for s in distance:
        va = vb = 315.0
        for center, width, ref, offset in TURNS:
            w = (1 + math.cos(math.pi * (s-center) / width)) / 2 if abs(s-center) < width else 0
            va -= (315 - ref) * w
            vb -= (315 - ref - offset) * w
        a.append(round(va, 3))
        b.append(round(vb, 3))

    def channel(speed):
        elapsed = [0.0]
        for u, v in zip(speed, speed[1:]):
            elapsed.append(elapsed[-1] + 3600 * STEP * (1 / u + 1 / v) / 2)
        slope = [0.0] + [v-u for u,v in zip(speed, speed[1:])]
        return dict(speed=speed, throttle=[max(0, min(100, round(100+10*x))) for x in slope],
                    gear=[max(1, min(8, int(v/40))) for v in speed],
                    brake=[x < -3 for x in slope]), elapsed

    ca, ta = channel(a)
    cb, tb = channel(b)
    delta = [round(y-x, 4) for x,y in zip(ta,tb)]
    def gain(start, end):
        return round(delta[end//STEP]-delta[start//STEP], 4)
    rows = []
    for category in ("low", "medium", "high"):
        members = [t for t in turns if t["speedClass"] == category]
        vals = [gain(t["start"], t["end"]) for t in members]
        rows.append(dict(category=category, labels=[t["label"] for t in members],
                         netMs=round(sum(vals), 4), forAMs=round(sum(max(0,v) for v in vals),4),
                         forBMs=round(sum(max(0,-v) for v in vals),4)))
    return dict(source="synthetic", distance=distance, a=ca, b=cb, delta=delta, turns=turns,
                bins=[dict(start=x,end=x+100,gain=gain(x,x+100)) for x in range(0,LENGTH,100)],
                boundaries=[800,1600], categories=rows,
                sectorAMs=[round(ta[y//STEP]-ta[x//STEP],3) for x,y in [(0,800),(800,1600),(1600,2400)]],
                sectorBMs=[round(tb[y//STEP]-tb[x//STEP],3) for x,y in [(0,800),(800,1600),(1600,2400)]],
                elapsedAMs=round(ta[-1],3), elapsedBMs=round(tb[-1],3))


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(make(), separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8", newline="\n")
