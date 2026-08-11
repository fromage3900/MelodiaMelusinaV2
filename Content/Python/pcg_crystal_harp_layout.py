"""Pure deterministic layout helpers for the Crystal Harp Grove.

The grove is five small harp gates on one height-aware curve. Each gate has
four pluck lanes, so the same authored graph can be regenerated in any chunk
without losing the station/lane/MIDI identity encoded in PCGPoint.Seed.
"""
from __future__ import annotations

from math import pi, sin, sqrt
from typing import Iterable


CRYSTAL_HARP_PATTERN = (60, 62, 64, 67, 69, 72, 74, 76, 79, 81)


def crystal_harp_midi_pattern(count: int = 20) -> tuple[int, ...]:
    return tuple(CRYSTAL_HARP_PATTERN[index % len(CRYSTAL_HARP_PATTERN)] for index in range(max(1, int(count))))


def _arc_length_resampler(points: list[tuple[float, float, float]]):
    cumulative = [0.0]
    for previous, current in zip(points, points[1:]):
        cumulative.append(
            cumulative[-1]
            + sqrt(sum((current[axis] - previous[axis]) ** 2 for axis in range(3)))
        )
    total = cumulative[-1]

    def sample(distance: float) -> tuple[float, float, float]:
        if total <= 1e-6:
            return points[0]
        target = max(0.0, min(total, distance))
        low, high = 0, len(cumulative) - 1
        while low < high:
            middle = (low + high) // 2
            if cumulative[middle] < target:
                low = middle + 1
            else:
                high = middle
        upper = max(1, low)
        lower = upper - 1
        span = max(1e-6, cumulative[upper] - cumulative[lower])
        alpha = (target - cumulative[lower]) / span
        return tuple(
            points[lower][axis] + (points[upper][axis] - points[lower][axis]) * alpha
            for axis in range(3)
        )

    return sample, total


def build_crystal_harp_layout(
    node_count: int = 20,
    station_count: int = 5,
    step_spacing: float = 520.0,
    grove_rise: float = 760.0,
    walk_width: float = 280.0,
) -> tuple[tuple[tuple[float, float, float, int, int, int, int], ...], tuple[tuple[float, float, float, int], ...]]:
    """Return 4-lane harp strings plus station landmark points.

    Nodes are distributed by curve distance rather than by raw X distance,
    keeping the route evenly spaced even while it bends and climbs.
    """
    node_count = max(1, int(node_count))
    station_count = max(1, int(station_count))
    step_spacing = max(1.0, float(step_spacing))
    grove_rise = max(1.0, float(grove_rise))
    walk_width = max(1.0, float(walk_width))
    lane_count = 4
    per_station = lane_count
    node_count = station_count * per_station
    total_span = (station_count - 1) * step_spacing
    x_origin = -total_span * 0.5

    def guide(alpha: float) -> tuple[float, float, float]:
        alpha = max(0.0, min(1.0, float(alpha)))
        x = x_origin + total_span * alpha
        y = sin(alpha * pi * 2.0) * walk_width * 0.48 + sin(alpha * pi * 5.0) * walk_width * 0.12
        z = 48.0 + alpha * grove_rise
        return x, y, z

    samples = [guide(index / 511.0) for index in range(512)]
    sample, total_length = _arc_length_resampler(samples)
    lane_offsets = (-0.42, -0.14, 0.14, 0.42)
    interactive: list[tuple[float, float, float, int, int, int, int]] = []
    midi_notes = crystal_harp_midi_pattern(node_count)
    for index, midi in enumerate(midi_notes):
        station = index // per_station
        lane = index % per_station
        center = sample(total_length * station / max(1, station_count - 1))
        x, y, z = center
        interactive.append((x, y + lane_offsets[lane] * walk_width, z + 48.0, index, lane, midi, station))

    landmarks: list[tuple[float, float, float, int]] = []
    for station in range(station_count):
        x, y, z = sample(total_length * station / max(1, station_count - 1))
        landmarks.append((x, y, z, 0xF10000 + station))
    return tuple(interactive), tuple(landmarks)


def build_crystal_harp_curve_points(
    station_count: int = 5,
    step_spacing: float = 520.0,
    grove_rise: float = 760.0,
    walk_width: float = 280.0,
    side: float = 1.0,
) -> tuple[tuple[float, float, float], ...]:
    nodes, _ = build_crystal_harp_layout(station_count=station_count, step_spacing=step_spacing, grove_rise=grove_rise, walk_width=walk_width)
    return tuple(
        (nodes[station * 4][0], nodes[station * 4][1] + float(side) * walk_width * 0.92, nodes[station * 4][2] + 260.0)
        for station in range(station_count)
    )


def validate_crystal_harp_layout(nodes: Iterable[tuple[float, float, float, int, int, int, int]]) -> list[str]:
    nodes = tuple(nodes)
    errors: list[str] = []
    if not nodes:
        return ["layout is empty"]
    seeds = [(node[3] << 16) | ((node[4] + 1) << 8) | node[5] for node in nodes]
    if len(seeds) != len(set(seeds)):
        errors.append("seed identities are not unique")
    if len({(node[3], node[5]) for node in nodes}) != len(nodes):
        errors.append("MIDI identities are not unique per node")
    if any(node[6] < 0 for node in nodes):
        errors.append("station identity is negative")
    for previous, current in zip(nodes, nodes[1:]):
        if current[0] < previous[0]:
            errors.append("curve order is not monotonic in X")
            break
    return errors
