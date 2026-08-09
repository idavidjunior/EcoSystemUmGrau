#!/usr/bin/env bash
set -euo pipefail
cd "$1"

APP_ID="com.umgrau.stream"
OLD_ID="com.umgrau.stream_um_grau"

sed -i "s|${OLD_ID}|${APP_ID}|g" android/app/build.gradle.kts

OLD_DIR=$(dirname "$(find android/app/src/main/kotlin -name MainActivity.kt | head -n1)")
NEW_DIR="android/app/src/main/kotlin/${APP_ID//.//}"
mkdir -p "$NEW_DIR"
mv "$OLD_DIR/MainActivity.kt" "$NEW_DIR/MainActivity.kt"

OLD_PKG="${OLD_DIR#android/app/src/main/kotlin/}"
OLD_PKG="${OLD_PKG//\//.}"
sed -i "s|package ${OLD_PKG}|package ${APP_ID}|" "$NEW_DIR/MainActivity.kt"

grep -r "$OLD_ID" android/ || echo "OK: nenhuma referencia restante ao antigo id"
