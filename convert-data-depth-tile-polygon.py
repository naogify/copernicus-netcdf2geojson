import os
import xarray as xr
import numpy as np
from datetime import datetime
import json
from tqdm import tqdm

# --- 設定 ---
nc_path = 'glo12_rg_6h-i_20250620-00h_3D-uovo_fcst_R20250610.nc'
output_dir = './geojsons_center_polygon'
WEB_MERCATOR_LAT_LIMIT = 85.0511  # Webメルカトルの緯度上限（必要な場合のみ有効）
# 指定の空間範囲（Copernicus product spec）
EXT_LAT_MIN, EXT_LAT_MAX = -80.0, 90.0
EXT_LON_MIN, EXT_LON_MAX = -180.0, 179.92

# --- データ読み込み ---
ds = xr.open_dataset(nc_path)
lats = ds['latitude'].values
lons = ds['longitude'].values
depths = ds['depth'].values
times = ds['time'].values

def round_depth(val):
    val_rounded = round(float(val), 2)
    return int(val_rounded) if val_rounded == int(val_rounded) else val_rounded

rounded_depths = [round_depth(d) for d in depths]
os.makedirs(output_dir, exist_ok=True)

# depthの値をファイル名として使えるように文字列に変換
depth_labels = [str(d) for d in rounded_depths]

def make_time_str(tval):
    """ISO 8601形式に変換"""
    try:
        dt_obj = datetime.utcfromtimestamp(np.datetime64(tval, 's').astype(int))
        return dt_obj.strftime('%Y-%m-%dT%H:%M:%SZ')
    except Exception:
        dt_str = str(tval).replace(' ', 'T')
        return dt_str if dt_str.endswith('Z') else dt_str + 'Z'

time_list = [make_time_str(tval) for tval in times]

# depths.jsonとtimes.jsonを生成（depthは0.49のみ対象）
with open(os.path.join(output_dir, "depths.json"), "w", encoding="utf-8") as f:
    json.dump([0.49], f, ensure_ascii=False, indent=2)
with open(os.path.join(output_dir, "times.json"), "w", encoding="utf-8") as f:
    json.dump(time_list, f, ensure_ascii=False, indent=2)

# --- セルサイズ（度） ---
# 緯度：等間隔だが自己交差回避のため符号を吸収
dlat = abs(float(np.mean(np.diff(lats))))
# 経度：等間隔。そのまま度単位で使用（cosを掛けない）
dlon = abs(float(np.mean(np.diff(lons))))

# ---- メインループ ----
for time_i, time_label in tqdm(list(enumerate(time_list)), desc="Time loop"):
    for depth_i, depth_label in tqdm(list(enumerate(depth_labels)), desc="Depth loop", leave=False):
        depth_val = float(rounded_depths[depth_i])
        if depth_val != 0.49:
            continue

        uo = ds['uo'].isel(time=time_i, depth=depth_i).values
        vo = ds['vo'].isel(time=time_i, depth=depth_i).values

        features = []
        for i in range(uo.shape[0]):
            lat_c = float(lats[i])
            lat_bottom = lat_c - dlat/2
            lat_top    = lat_c + dlat/2

            # まず product の緯度範囲を厳密チェック（セル四隅で判定）
            if not (EXT_LAT_MIN <= lat_bottom and lat_top <= EXT_LAT_MAX):
                continue

            # Webメルカトルで描く場合の安全域（必要な人だけ有効）
            if (lat_top > WEB_MERCATOR_LAT_LIMIT) or (lat_bottom < -WEB_MERCATOR_LAT_LIMIT):
                continue

            for j in range(uo.shape[1]):
                lon_c = float(lons[j])
                lon_left  = lon_c - dlon/2
                lon_right = lon_c + dlon/2

                # Product の経度範囲を厳密チェック（セル四隅で判定）
                if not (EXT_LON_MIN <= lon_left and lon_right <= EXT_LON_MAX):
                    continue

                u = float(uo[i, j])
                v = float(vo[i, j])
                if np.isnan(u) or np.isnan(v):
                    continue

                # ポリゴン（度単位の等間隔グリッド）
                polygon = [[
                    [lon_left,  lat_bottom],
                    [lon_right, lat_bottom],
                    [lon_right, lat_top],
                    [lon_left,  lat_top],
                    [lon_left,  lat_bottom]
                ]]

                speed = float(np.sqrt(u**2 + v**2))
                direction = float((np.degrees(np.arctan2(u, v)) + 360) % 360)

                feature = {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": polygon},
                    "properties": {
                        "uo": float(round(u, 4)),
                        "vo": float(round(v, 4)),
                        "speed": float(round(speed, 4)),
                        "direction": float(round(direction, 2)),
                        "depth": float(depth_val),
                        "time": str(time_label)
                    }
                }
                features.append(feature)

        if features:
            out_dir = os.path.join(output_dir, time_label)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{depth_label}.geojson")
            geojson = {"type": "FeatureCollection", "features": features}
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(geojson, f, ensure_ascii=False)

print("処理が完了しました。")
print(f"出力先: {os.path.abspath(output_dir)}")
