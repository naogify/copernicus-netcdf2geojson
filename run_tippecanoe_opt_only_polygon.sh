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
GEOJSONS_CENTER_POLYGON_ROOT="./geojsons_center_polygon/"
GEOJSONS_CENTER_POLYGON="./geojsons_center_polygon/2025-06-20T00:00:00Z/0.49.geojson"


TILES_ROOT="./tiles"
TARGET_DIR="./tiles/2025-06-20T00:00:00Z/0.49"

# TILES_ROOT　が存在したら削除
if [ -d "$TILES_ROOT" ]; then
  echo "既存の $TILES_ROOT ディレクトリを削除します..."

  TEMP_DIR="./temp_tiles_$(date +%s)"
  mv "$TILES_ROOT" "$TEMP_DIR"
  rm -rf "$TEMP_DIR" &
fi

#TARGET_DIRのディレクトリを作成
mkdir -p "$TARGET_DIR"

echo "処理中: $GEOJSONS_CENTER_POLYGON"

simplified_polygon_geojson='./simplified_polygon.geojson'

if [ -f $simplified_polygon_geojson ]; then
  echo "$simplified_polygon_geojson が既に存在するためスキップします。"
else
  # Z4-8: geojsons_polygon
  echo $simplified_polygon_geojson
  jq '{
    type: .type,
    features: [.features[] | {
      type: .type,
      geometry: .geometry,
      properties: { uo: .properties.uo, vo: .properties.vo, speed: .properties.speed, direction: .properties.direction }
    }]
  }' "$GEOJSONS_CENTER_POLYGON" > "$simplified_polygon_geojson"
fi

tippecanoe \
  -e "$TARGET_DIR" \
  -l current \
  -Z1 -z12 \
  "$simplified_polygon_geojson" \
  --no-tile-compression \
  --no-simplification-of-shared-nodes \
  --grid-low-zooms \
  --no-tile-size-limit \
  --no-feature-limit \
  --low-detail=7

rm "$simplified_polygon_geojson"

cp "$GEOJSONS_CENTER_POLYGON_ROOT/depths.json" "$TILES_ROOT/depths.json"
cp "$GEOJSONS_CENTER_POLYGON_ROOT/times.json" "$TILES_ROOT/times.json"

echo "完了！"
