import os
import xarray as xr
import numpy as np
from datetime import datetime
import json
from tqdm import tqdm

# --- 設定 ---
nc_path = 'glo12_rg_6h-i_20250620-00h_3D-uovo_fcst_R20250610.nc'
output_dir = './geojsons_point'

# --- データ読み込み ---
ds = xr.open_dataset(nc_path)
lats = ds['latitude'].values
lons = ds['longitude'].values
depths = ds['depth'].values
times = ds['time'].values

def round_depth(val):
    val_rounded = round(float(val), 2)
    if val_rounded == int(val_rounded):
        return int(val_rounded)
    else:
        return val_rounded

rounded_depths = [round_depth(d) for d in depths]
os.makedirs(output_dir, exist_ok=True)

depth_labels = [str(d) for d in rounded_depths]

def make_time_str(tval):
    try:
        dt = np.datetime64(tval)
        dt = str(dt)
    except:
        dt = str(tval)
    try:
        dt_obj = datetime.fromisoformat(dt.replace('Z','').replace('T', ' '))
        return dt_obj.strftime('%Y%m%dT%H%M%SZ')
    except:
        return dt.replace(':', '').replace('-', '').replace(' ', '').replace('T', 'T') + 'Z'

time_list = []
for tval in times:
    time_label = make_time_str(tval)
    time_list.append(time_label)

with open(os.path.join(output_dir, "depths.json"), "w", encoding="utf-8") as f:
    json.dump(rounded_depths, f, ensure_ascii=False, indent=2)
with open(os.path.join(output_dir, "times.json"), "w", encoding="utf-8") as f:
    json.dump(time_list, f, ensure_ascii=False, indent=2)

# --- time/depth形式で出力 ---
for time_i, time_val in tqdm(list(enumerate(times)), desc="Time loop"):
    time_label = make_time_str(time_val)
    out_dir = os.path.join(output_dir, time_label)
    os.makedirs(out_dir, exist_ok=True)
    for depth_i, depth_label in tqdm(list(enumerate(depth_labels)), desc="Depth loop", leave=False):
        depth_val = rounded_depths[depth_i]
        uo = ds['uo'].isel(time=time_i, depth=depth_i).values
        vo = ds['vo'].isel(time=time_i, depth=depth_i).values
        features = []
        for i in range(uo.shape[0]):
            for j in range(uo.shape[1]):
                lat = float(lats[i])
                lon = float(lons[j])
                u = float(uo[i, j])
                v = float(vo[i, j])
                if np.isnan(u) or np.isnan(v):
                    continue
                speed = np.sqrt(u**2 + v**2)
                direction = (np.degrees(np.arctan2(u, v)) + 360) % 360
                feature = {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "uo": round(u, 4),
                        "vo": round(v, 4),
                        "speed": round(speed, 4),
                        "direction": round(direction, 2),
                        "depth": depth_val,
                        "time": time_label
                    }
                }
                features.append(feature)
        if features:
            out_path = os.path.join(out_dir, f"{depth_label}.geojson")
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
