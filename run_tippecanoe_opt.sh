#!/bin/bash
set -ex

#---スクリプトの説明---
# このスクリプトは、指定されたGeoJSONファイルを使用して、Tippecanoeを実行し、タイルを生成します。
# Z0-3用のタイルは、`geojsons_point`ディレクトリから取得し、Z4-8用のタイルは、`geojsons_center_polygon`ディレクトリから取得します。
# 生成されたタイルは、`tiles/2025-06-20T00:00:00Z/0.49`ディレクトリに保存されます。
# また、`depths.json`と`times.json`ファイルも同じディレクトリにコピーされます。 
#
# run_tippecanoe.sh との違いは、ズームレベル毎の軽量化をします。

# 必要なパスを設定
GEOJSONS_POINT="./geojsons_point/20250620T000000Z/0.49.geojson"
GEOJSONS_CENTER_POLYGON_ROOT="./geojsons_center_polygon/"
GEOJSONS_CENTER_POLYGON="./geojsons_center_polygon/2025-06-20T00:00:00Z/0.49.geojson"


TILES_ROOT="./tiles"
TARGET_DIR="./tiles/2025-06-20T00:00:00Z/0.49"
DIR_Z0="$TARGET_DIR/z0"
DIR_Z1_12="$TARGET_DIR/z1-12"

# # TILES_ROOT　が存在したら削除
# if [ -d "$TILES_ROOT" ]; then
#   echo "既存の $TILES_ROOT ディレクトリを削除します..."
#   rm -rf "$TILES_ROOT"
# fi

mkdir -p "$DIR_Z0" "$DIR_Z1_12"

echo "処理中: $GEOJSONS_POINT, $GEOJSONS_CENTER_POLYGON"
echo "  - Z0用: $DIR_Z0"
echo "  - Z1-12用: $DIR_Z1_12"

# Z0-3: geojsons_point
simplified_geojson='./simplified_point.geojson'
jq '{
  type: .type,
  features: [.features[] | {
    type: .type,
    geometry: .geometry,
    properties: { uo: .properties.uo, vo: .properties.vo, speed: .properties.speed, direction: .properties.direction }
  }]
}' "$GEOJSONS_POINT" > "$simplified_geojson"

# --maximum-tile-features=63058 で約1MBのタイルサイズになる
tippecanoe \
  -e "$DIR_Z0" \
  -l current \
  -Z0 -z0 \
  "$simplified_geojson" \
  --no-tile-compression \
  -maximum-tile-bytes=1000000 \
  --drop-densest-as-needed

pid_z03=$!


# # Z4-8: geojsons_polygon
# simplified_polygon_geojson='./simplified_polygon.geojson'
# echo $simplified_polygon_geojson
# jq '{
#   type: .type,
#   features: [.features[] | {
#     type: .type,
#     geometry: .geometry,
#     properties: { uo: .properties.uo, vo: .properties.vo, speed: .properties.speed, direction: .properties.direction }
#   }]
# }' "$GEOJSONS_CENTER_POLYGON" > "$simplified_polygon_geojson"

# # --- Z4-8: geojsons_center_polygon
# # Z4-8用のタイルを生成
# # --no-simplification-of-shared-nodes で共有している線を結合
# # --grid-low-zooms で斜めの線を許可しない（グリッドのみ）
# # --low-detail=8 で 2^12=4096x4096の解像度のタイルを、2^8=256（256×256グリッド）に減らす
# # ----------------------
# tippecanoe \
#   -e "$DIR_Z1_12" \
#   -l current \
#   -Z1 -z12 \
#   "$simplified_polygon_geojson" \
#   --no-tile-compression \
#   --no-simplification-of-shared-nodes \
#   --grid-low-zooms \
#   --no-tile-size-limit \
#   --no-feature-limit \
#   --low-detail=7 \
#   -r1 &

# pid_z48=$!

# # 両方終わるまで待つ
# # wait $pid_z03
# wait $pid_z48

# rm "$simplified_geojson"
# rm "$simplified_polygon_geojson"

# マージ
cp -r "$DIR_Z0/"* "$TARGET_DIR/" 2>/dev/null || true
# cp -r "$DIR_Z1_12/"* "$TARGET_DIR/" 2>/dev/null || true

# 不要なディレクトリ削除
rm -rf "$DIR_Z0" "$DIR_Z1_12"

# cp "$GEOJSONS_CENTER_POLYGON_ROOT/depths.json" "$TILES_ROOT/depths.json"
# cp "$GEOJSONS_CENTER_POLYGON_ROOT/times.json" "$TILES_ROOT/times.json"

echo "完了！"
