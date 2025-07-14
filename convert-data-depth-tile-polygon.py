import os
import xarray as xr
import numpy as np
from datetime import datetime
import json
from tqdm import tqdm

# --- 設定 ---
nc_path = 'glo12_rg_6h-i_20250620-00h_3D-uovo_fcst_R20250610.nc'
output_dir = './geojsons_center_polygon'

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

# depthの値をファイル名として使えるように文字列に変換
depth_labels = [str(d) for d in rounded_depths]

def make_time_str(tval):
    """
    xarrayのtimeオブジェクトをファイル名やディレクトリ名として安全に使える
    ISO 8601形式の文字列（UTC）に変換します。
    例: '2024-01-01T00:00:00Z'
    """
    try:
        # np.datetime64からPythonのdatetimeオブジェクトに変換
        dt_obj = datetime.utcfromtimestamp(np.datetime64(tval, 's').astype(int))
        # ISO 8601形式の文字列（'Z'でUTCを示す）にフォーマット
        return dt_obj.strftime('%Y-%m-%dT%H:%M:%SZ')
    except Exception:
        # フォールバック処理
        dt_str = str(tval).replace(' ', 'T')
        if not dt_str.endswith('Z'):
            dt_str += 'Z'
        return dt_str

time_list = [make_time_str(tval) for tval in times]

# depths.jsonとtimes.jsonを生成
with open(os.path.join(output_dir, "depths.json"), "w", encoding="utf-8") as f:
    json.dump([float(d) for d in rounded_depths], f, ensure_ascii=False, indent=2)
with open(os.path.join(output_dir, "times.json"), "w", encoding="utf-8") as f:
    json.dump(time_list, f, ensure_ascii=False, indent=2)

# Δlat, Δlon（全体平均。等間隔グリッド想定）
dlat = float(np.mean(np.diff(lats)))
dlon = float(np.mean(np.diff(lons)))

# ---- メインループ ----
### 変更点 ###: ループの順序を time -> depth に変更
for time_i, time_label in tqdm(list(enumerate(time_list)), desc="Time loop"):
    for depth_i, depth_label in tqdm(list(enumerate(depth_labels)), desc="Depth loop", leave=False):
        depth_val = float(rounded_depths[depth_i])
        
        # データスライスを取得
        uo = ds['uo'].isel(time=time_i, depth=depth_i).values
        vo = ds['vo'].isel(time=time_i, depth=depth_i).values
        
        features = []
        for i in range(uo.shape[0]):
            for j in range(uo.shape[1]):
                lat_c = float(lats[i])
                lon_c = float(lons[j])
                u = float(uo[i, j])
                v = float(vo[i, j])
                
                if np.isnan(u) or np.isnan(v):
                    continue
                    
                # CF規約で「格子点は中心」なので±Δ/2でグリッドセル生成
                polygon = [[
                    [lon_c - dlon/2, lat_c - dlat/2],  # 左下
                    [lon_c + dlon/2, lat_c - dlat/2],  # 右下
                    [lon_c + dlon/2, lat_c + dlat/2],  # 右上
                    [lon_c - dlon/2, lat_c + dlat/2],  # 左上
                    [lon_c - dlon/2, lat_c - dlat/2]   # 左下（close）
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
            ### 変更点 ###: time/depth 構造でディレクトリとパスを作成
            # 出力先ディレクトリ (例: ./geojsons_center_polygon/2024-01-01T00:00:00Z/)
            out_dir = os.path.join(output_dir, time_label)
            os.makedirs(out_dir, exist_ok=True)
            
            # 出力ファイルパス (例: .../0.49.geojson)
            out_path = os.path.join(out_dir, f"{depth_label}.geojson")
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(geojson, f, ensure_ascii=False) # indentを削除してファイルサイズを削減

print("処理が完了しました。")
print(f"出力先: {os.path.abspath(output_dir)}")