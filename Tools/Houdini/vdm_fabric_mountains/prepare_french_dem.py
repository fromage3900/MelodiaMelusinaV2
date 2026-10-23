#!/usr/bin/env python3
"""Non-destructive French DEM intake for Faraway Mother Houdini research.

Input: local IGN GeoTIFF/ASC, public Copernicus GLO-30 COG, or synthetic smoke-test.
Outputs: normalized 16-bit PNG, metric float32 GeoTIFF, slope/hillshade and manifest.
Never edits FarawayDrape.hip, existing UE levels or authored heightfields.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform_bounds
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / 'recipes/houdini_faraway/terrain_fabric_atlas.v1.json'

def source_url(lat: int, lon: int) -> str:
    latpart = ('N' if lat >= 0 else 'S') + f'{abs(lat):02d}_00'
    lonpart = ('E' if lon >= 0 else 'W') + f'{abs(lon):03d}_00'
    name = f'Copernicus_DSM_COG_10_{latpart}_{lonpart}_DEM'
    return f'https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif'

def read_into_grid(paths: list[str], dst_transform, shape: tuple[int, int]):
    result = np.full(shape, np.nan, dtype=np.float32)
    metadata = []
    for path in paths:
        with rasterio.open(path) as ds:
            if ds.crs is None:
                raise RuntimeError(f'Source has no CRS: {path}')
            arr = np.full(shape, np.nan, dtype=np.float32)
            reproject(
                source=rasterio.band(ds, 1), destination=arr,
                src_transform=ds.transform, src_crs=ds.crs, src_nodata=ds.nodata,
                dst_transform=dst_transform, dst_crs='EPSG:2154',
                dst_nodata=np.nan, resampling=Resampling.bilinear,
                init_dest_nodata=True)
            valid = np.isfinite(arr)
            result[valid] = arr[valid]
            metadata.append({'source': path, 'source_crs': str(ds.crs),
                             'source_nodata': ds.nodata})
    if not np.isfinite(result).any():
        raise RuntimeError('No valid elevation values overlap crop; check CRS and source coverage')
    return result, metadata

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preset', required=True, help='Region ID from the JSON atlas')
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument('--source', nargs='+', type=Path,
                        help='Local georeferenced source(s), preferably IGN bare-earth DTM')
    source.add_argument('--fetch-copernicus', action='store_true',
                        help='Stream public GLO-30 COG(s); DSM includes vegetation/buildings')
    source.add_argument('--fixture', action='store_true',
                        help='Synthetic offline QA only, NOT real French topography')
    ap.add_argument('--size-m', type=float, default=4000)
    ap.add_argument('--res', type=int, default=513)
    ap.add_argument('--out-dir', type=Path, default=None)
    args = ap.parse_args()
    if not (33 <= args.res <= 4097 and 100 <= args.size_m <= 20000):
        ap.error('Use 33 <= --res <= 4097 and 100 <= --size-m <= 20000')
    atlas = json.loads(CATALOG.read_text(encoding='utf-8'))
    presets = {p['id']: p for p in atlas['regions']}
    if args.preset not in presets:
        ap.error(f'Unknown preset {args.preset}; choose from {", ".join(presets)}')
    region = presets[args.preset]
    c = region['center_wgs84']
    x, y = Transformer.from_crs('EPSG:4326', 'EPSG:2154', always_xy=True).transform(c['lon'], c['lat'])
    half = args.size_m / 2.0
    size = args.res
    pixel_metres = args.size_m / size
    transform = from_origin(x-half, y+half, pixel_metres, pixel_metres)
    paths: list[str] = []
    if args.source:
        paths = [str(p.resolve()) for p in args.source]
        for p in paths:
            if not Path(p).is_file():
                ap.error(f'Local DEM missing: {p}')
        source_kind = 'local_georeferenced_DEM_or_DSM_verify_product'
    elif args.fetch_copernicus:
        west,south,east,north = transform_bounds(
            'EPSG:2154','EPSG:4326',x-half,y-half,x+half,y+half,densify_pts=21)
        for la in range(math.floor(south), math.floor(north)+1):
            for lo in range(math.floor(west), math.floor(east)+1):
                paths.append(source_url(la,lo))
        source_kind = 'Copernicus_GLO30_2021_public_DSM'
    else:
        source_kind = 'SYNTHETIC_FIXTURE_NOT_REAL_ELEVATION'
    if args.fixture:
        u,v = np.meshgrid(np.linspace(-1,1,size),np.linspace(-1,1,size))
        z = (700+180*np.exp(-3*(u*u+v*v))+70*np.sin(u*8+v*2)+35*v).astype('float32')
        meta = [{'source':'analytic_fixture','source_crs':'EPSG:2154'}]
    else:
        z,meta = read_into_grid(paths,transform,(size,size))
    valid = np.isfinite(z)
    zmin,zmax = float(np.nanmin(z)),float(np.nanmax(z))
    span = max(zmax-zmin,1e-9)
    normalized = np.where(valid,(z-zmin)/span,0)
    height_u16 = np.rint(np.clip(normalized,0,1)*65535).astype(np.uint16)
    out = args.out_dir or (ROOT/'Saved/Audit/houdini_faraway_mother/dem_atlas'/args.preset)
    out.mkdir(parents=True,exist_ok=True)
    height_path=out/'height_normalized_16bit.png'
    Image.fromarray(height_u16).save(height_path)
    absolute_path=out/'height_absolute_m_epsg2154.tif'
    with rasterio.open(absolute_path,'w',driver='GTiff',height=size,width=size,
        count=1,dtype='float32',crs='EPSG:2154',transform=transform,
        nodata=np.nan,compress='deflate') as dst:
        dst.write(z.astype(np.float32),1)
    rowgrad,colgrad = np.gradient(np.nan_to_num(z,nan=zmin),pixel_metres)
    east_grad,north_grad = colgrad,-rowgrad
    slope = np.arctan(np.hypot(east_grad,north_grad))
    slope_path=out/'slope_preview_8bit.png'
    Image.fromarray(np.rint(np.degrees(slope)/90*255).clip(0,255).astype('uint8')).save(slope_path)
    nx,ny,nz = -east_grad,-north_grad,np.ones_like(z)
    length=np.sqrt(nx*nx+ny*ny+nz*nz)
    az,elev=np.deg2rad(315),np.deg2rad(40)
    shade=(nx*np.sin(az)*np.cos(elev)+ny*np.cos(az)*np.cos(elev)+nz*np.sin(elev))/length
    preview=out/'hillshade_preview.png'
    Image.fromarray(np.where(valid,np.clip(shade,0,1)*225+25,0).astype('uint8')).save(preview)
    def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'schema':'melodia.faraway_dem_intake.v1',
        'generated_utc':datetime.now(timezone.utc).isoformat(),
        'preset':args.preset,'region':region['name'],'source_kind':source_kind,
        'source_metadata':meta,'license_requires_independent_review':True,
        'center_wgs84':c,'extent_m':args.size_m,'resolution_px':size,
        'raster_crs':'EPSG:2154','vertical_units':'metres as delivered; verify source vertical datum',
        'z_min_m':zmin,'z_max_m':zmax,'z_span_m':zmax-zmin,
        'valid_fraction':round(float(valid.mean()),6),
        'png16_decode':'height_m = z_min_m + png_u16 / 65535 * z_span_m',
        'outputs':{p.name:sha(p) for p in [height_path,absolute_path,slope_path,preview]}}
    (out/'source_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','source_kind':source_kind,'out_dir':str(out),
        'z_min_m':zmin,'z_max_m':zmax,'valid_fraction':manifest['valid_fraction']},indent=2))
    return 0
if __name__=='__main__':
    raise SystemExit(main())
