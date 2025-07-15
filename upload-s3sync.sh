#!/usr/bin/env bash
set -ex

# --- NOTE: S3の設定 ---
# aws configure set default.s3.max_concurrent_requests 100 を指定することで、
# S3へのアップロードを並列で行うことができます。必要に応じてデフォルト値を変更してください。 

# 1番目の引数がなければエラー
if [ -z "$1" ]; then
  echo "Usage: $0 <UPLOAD_DIR> <S3_BUCKET_URL>"
  exit 1
fi

# 2番目の引数がなければエラー
if [ -z "$2" ]; then
  echo "Usage: $0 <UPLOAD_DIR> <S3_BUCKET_URL>"
  exit 1
fi

UPLOAD_DIR="$1"
# UPLOAD_DIR は "./" を付けない
if [[ "$UPLOAD_DIR" == "./"* ]]; then
  UPLOAD_DIR="${UPLOAD_DIR:2}"
fi

S3_BUCKET="$2"

# PBFファイル
aws s3 sync "./$UPLOAD_DIR" "$S3_BUCKET/$UPLOAD_DIR" \
  --exclude "*" --include "*.pbf" \
  --content-type "application/vnd.mapbox-vector-tile" \
  --content-encoding gzip \
  --no-progress

# JSONファイル
aws s3 sync "./$UPLOAD_DIR" "$S3_BUCKET/$UPLOAD_DIR" \
  --exclude "*" --include "*.json" \
  --content-type "application/json" \
  --no-progress
