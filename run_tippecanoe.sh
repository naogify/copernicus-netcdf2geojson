#!/bin/bash

# スクリプトの堅牢性を高める設定 (エラー発生時に停止)
set -e

#---スクリプトの説明---
# このスクリプトは、指定されたGeoJSONファイルを使用して、Tippecanoeを実行し、タイルを生成します。
# GeoJSONファイルは、`geojsons_point`ディレクトリから取得し、生成されたタイルは、`tiles`ディレクトリに保存されます。  
# run_tippecanoe_opt.sh との違いは、ズームレベル毎の軽量化をしません

# --- 設定 ---
# GeoJSONファイルが格納されているルートディレクトリ
GEOJSONS_ROOT="./geojsons_point"

# 生成したタイルを格納するルートディレクトリ
TILES_ROOT="./tiles"


# --- メイン処理 ---
echo "タイル生成を開始します..."

# time/depth 構造のGeoJSONファイルを全探索
# 例: ./geojsons_center_polygon/2025-06-11T00:00:00Z/0.49.geojson
find "$GEOJSONS_ROOT" -type f -name "0.49.geojson" | while read -r geojson_path; do
  
  ### 変更点: パスから time と depth を抽出するロジック ###
  
  # ルートディレクトリ部分を除いた相対パスを取得
  # 例: 2025-06-11T00:00:00Z/0.49.geojson
  rel_path="${geojson_path#$GEOJSONS_ROOT/}"

  # 最初のスラッシュまでを「time」として抽出
  # 例: 2025-06-11T00:00:00Z
  time="${rel_path%%/*}"

  # 最初のスラッシュ以降（ファイル名）を取得
  # 例: 0.49.geojson
  depth_ext="${rel_path#*/}"

  # 拡張子 .geojson を取り除き「depth」を取得
  # 例: 0.49
  depth="${depth_ext%.geojson}"

  ### 変更点: タイルの出力先ディレクトリ構造 ###
  # time/depth の階層で出力ディレクトリを作成
  OUT_DIR="${TILES_ROOT}/${time}/${depth}"
  mkdir -p "$OUT_DIR"

  echo "処理中: $geojson_path  ->  $OUT_DIR"

  # tippecanoeでタイルを生成し、指定したディレクトリに出力 (-e)
  tippecanoe \
    -e "$OUT_DIR" \
    -l current \
    -Z0 -z8 \
    "$geojson_path" \
    --no-tile-size-limit \
    --no-feature-limit \
    -r1 \
    --no-tile-compression
done

# --- 後処理 ---
echo "メタデータファイルをコピーしています..."

# depths.json と times.json をタイルのルートディレクトリにコピー
cp "$GEOJSONS_ROOT/depths.json" "$TILES_ROOT/depths.json"
cp "$GEOJSONS_ROOT/times.json" "$TILES_ROOT/times.json"

echo "すべてのタイル生成が完了しました！ ✨"