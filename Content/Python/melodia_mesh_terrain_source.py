"""Build a metric Mesh Terrain source from Gaea or a public DEM endpoint.

This module deliberately stops at a source mesh and provenance manifest. The
UE 5.8 editor owns Mesh Terrain partition creation/import; this script never
creates or edits a classic Landscape actor or a production map.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import time
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable, Sequence


METERS_PER_DEGREE_LAT = 110_540.0
DEFAULT_ENDPOINT = "https://api.opentopodata.org/v1"
DEFAULT_DATASET = "aster30m"
MAX_LOCATIONS_PER_REQUEST = 100


@dataclass(frozen=True)
class TerrainSourceSpec:
    """A bounded, local ENU terrain request with explicit real-world scale."""

    center_lat: float
    center_lon: float
    width_m: float
    depth_m: float
    samples_x: int
    samples_y: int
    dataset: str = DEFAULT_DATASET
    vertical_scale: float = 1.0
    source_tool: str = "Open Topo Data / ASTER GDEM"
    anchor_name: str = "Petal Cantata / Yoshino region"

    def __post_init__(self) -> None:
        if not (-90.0 <= self.center_lat <= 90.0):
            raise ValueError("center_lat must be in [-90, 90]")
        if not (-180.0 <= self.center_lon <= 180.0):
            raise ValueError("center_lon must be in [-180, 180]")
        if self.width_m <= 0 or self.depth_m <= 0:
            raise ValueError("terrain extents must be positive meters")
        if self.samples_x < 2 or self.samples_y < 2:
            raise ValueError("terrain requires at least a 2x2 sample grid")
        if self.vertical_scale <= 0:
            raise ValueError("vertical_scale must be positive")


def _grid_locations(spec: TerrainSourceSpec) -> list[tuple[float, float, float, float]]:
    """Return (local_x_m, local_y_m, latitude, longitude) row-major."""

    lon_m = METERS_PER_DEGREE_LAT * max(0.01, math.cos(math.radians(spec.center_lat)))
    locations: list[tuple[float, float, float, float]] = []
    for y_index in range(spec.samples_y):
        y_m = (y_index / (spec.samples_y - 1) - 0.5) * spec.depth_m
        latitude = spec.center_lat + y_m / METERS_PER_DEGREE_LAT
        for x_index in range(spec.samples_x):
            x_m = (x_index / (spec.samples_x - 1) - 0.5) * spec.width_m
            longitude = spec.center_lon + x_m / lon_m
            locations.append((x_m, y_m, latitude, longitude))
    return locations


def _chunks(values: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def query_open_topo_data(
    spec: TerrainSourceSpec,
    *,
    endpoint: str = DEFAULT_ENDPOINT,
    request_fn: Callable[[urllib.request.Request], bytes] | None = None,
    request_delay_s: float = 1.05,
) -> list[float]:
    """Fetch real elevations in row-major order from Open Topo Data.

    ``request_fn`` is injectable so offline tests can use recorded responses.
    The public service documents a 100-location/request and 1-request/second
    sustainability limit; the default delay respects that limit.
    """

    locations = _grid_locations(spec)
    request_fn = request_fn or (lambda request: urllib.request.urlopen(request, timeout=60).read())
    elevations: list[float] = []
    for batch_index, batch in enumerate(_chunks(locations, MAX_LOCATIONS_PER_REQUEST)):
        query = "|".join(f"{lat:.7f},{lon:.7f}" for _, _, lat, lon in batch)
        url = f"{endpoint.rstrip('/')}/{spec.dataset}"
        request = urllib.request.Request(
            url,
            data=json.dumps({"locations": query, "interpolation": "bilinear"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "MelodiaMeshTerrain/1.0"},
            method="POST",
        )
        response_bytes: bytes | None = None
        last_error: Exception | None = None
        for attempt in range(5):
            try:
                response_bytes = request_fn(request)
                break
            except (OSError, TimeoutError) as exc:
                last_error = exc
                if attempt == 4:
                    raise RuntimeError(f"elevation request failed after retries: {exc}") from exc
                time.sleep(min(30.0, 2.0**attempt))
        if response_bytes is None:
            raise RuntimeError(f"elevation request failed: {last_error}")
        payload = json.loads(response_bytes.decode("utf-8"))
        if payload.get("status") != "OK":
            raise RuntimeError(f"elevation request failed: {payload.get('error', payload)}")
        results = payload.get("results") or []
        if len(results) != len(batch):
            raise RuntimeError(f"elevation response length {len(results)} != request length {len(batch)}")
        for result in results:
            elevation = result.get("elevation")
            if elevation is None or not math.isfinite(float(elevation)):
                raise RuntimeError("elevation source returned null/non-finite data")
            elevations.append(float(elevation))
        if batch_index and request_delay_s > 0:
            time.sleep(request_delay_s)
    return elevations


def load_recorded_elevations(path: str | pathlib.Path) -> list[float]:
    """Load a recorded Open Topo Data response or a plain numeric list."""

    payload = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [float(value) for value in payload]
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("recorded elevations must be a numeric list or Open Topo Data response")
    return [float(result["elevation"]) for result in results]


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_metric_obj(spec: TerrainSourceSpec, elevations: Sequence[float], output_path: str | pathlib.Path) -> dict[str, Any]:
    """Write a grid mesh in meters, suitable for Mesh Terrain import at 100x."""

    expected = spec.samples_x * spec.samples_y
    if len(elevations) != expected:
        raise ValueError(f"expected {expected} elevations, received {len(elevations)}")
    values = [float(value) * spec.vertical_scale for value in elevations]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("elevations must be finite")

    output = pathlib.Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Melodia Mesh Terrain source",
        "# Units: meters; import into UE 5.8 Mesh Terrain with 100 cm/m",
    ]
    for index, elevation in enumerate(values):
        x = (index % spec.samples_x) / (spec.samples_x - 1) * spec.width_m - spec.width_m / 2
        y = (index // spec.samples_x) / (spec.samples_y - 1) * spec.depth_m - spec.depth_m / 2
        lines.append(f"v {x:.6f} {y:.6f} {elevation:.6f}")
    for index in range(expected):
        u = (index % spec.samples_x) / (spec.samples_x - 1)
        v = (index // spec.samples_x) / (spec.samples_y - 1)
        lines.append(f"vt {u:.8f} {v:.8f}")
    for row in range(spec.samples_y - 1):
        for column in range(spec.samples_x - 1):
            a = row * spec.samples_x + column + 1
            b = a + 1
            d = a + spec.samples_x
            c = d + 1
            lines.append(f"f {a}/{a} {b}/{b} {c}/{c}")
            lines.append(f"f {a}/{a} {c}/{c} {d}/{d}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return {
        "path": output.as_posix(),
        "sha256": _sha256(output),
        "vertex_count": expected,
        "triangle_count": (spec.samples_x - 1) * (spec.samples_y - 1) * 2,
        "elevation_min_m": min(values),
        "elevation_max_m": max(values),
    }


def export_mesh_terrain_source(
    spec: TerrainSourceSpec,
    elevations: Sequence[float],
    *,
    obj_path: str | pathlib.Path,
    manifest_path: str | pathlib.Path,
    source_url: str = f"{DEFAULT_ENDPOINT}/{DEFAULT_DATASET}",
    source_kind: str = "public_dem",
) -> dict[str, Any]:
    """Write the metric mesh and its import/provenance manifest."""

    mesh = write_metric_obj(spec, elevations, obj_path)
    manifest = {
        "format": "melodia_mesh_terrain_source",
        "schema_version": 1,
        "source": {
            "kind": source_kind,
            "tool": spec.source_tool,
            "dataset": spec.dataset,
            "url": source_url,
            "anchor_name": spec.anchor_name,
            "center_lat": spec.center_lat,
            "center_lon": spec.center_lon,
            "vertical_scale": spec.vertical_scale,
        },
        "geometry": {
            "units": "meters",
            "coordinate_system": "local ENU around source anchor",
            "width_m": spec.width_m,
            "depth_m": spec.depth_m,
            "samples_x": spec.samples_x,
            "samples_y": spec.samples_y,
            **mesh,
        },
        "unreal": {
            "engine": "5.8",
            "target": "Mesh Terrain",
            "import_scale_cm_per_meter": 100.0,
            "required_plugins": ["MeshPartition", "MeshTerrainMode", "PCGMeshPartitionInterop"],
            "classic_landscape_used": False,
        },
        "validation": {
            "metric_extent_matches_source": True,
            "elevation_samples_complete": True,
            "placeholder_terrain": False,
        },
    }
    manifest_file = pathlib.Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--center-lat", type=float, required=True)
    parser.add_argument("--center-lon", type=float, required=True)
    parser.add_argument("--width-m", type=float, required=True)
    parser.add_argument("--depth-m", type=float, required=True)
    parser.add_argument("--samples-x", type=int, required=True)
    parser.add_argument("--samples-y", type=int, required=True)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--anchor-name", default="Petal Cantata / Yoshino region")
    parser.add_argument("--elevation-json", help="Use recorded JSON instead of querying the public endpoint")
    parser.add_argument("--output-obj", required=True)
    parser.add_argument("--output-manifest", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    spec = TerrainSourceSpec(
        center_lat=args.center_lat,
        center_lon=args.center_lon,
        width_m=args.width_m,
        depth_m=args.depth_m,
        samples_x=args.samples_x,
        samples_y=args.samples_y,
        dataset=args.dataset,
        anchor_name=args.anchor_name,
    )
    elevations = load_recorded_elevations(args.elevation_json) if args.elevation_json else query_open_topo_data(spec)
    manifest = export_mesh_terrain_source(
        spec,
        elevations,
        obj_path=args.output_obj,
        manifest_path=args.output_manifest,
        source_url=f"{DEFAULT_ENDPOINT}/{args.dataset}",
        source_kind="recorded_dem" if args.elevation_json else "public_dem",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
