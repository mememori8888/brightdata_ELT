#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_places_api_review_fields.py

Google Places API (New) の searchText レスポンスから、
reviews配列に実際に含まれるキー名だけを確認する診断スクリプト。
レビュー本文・投稿者名などの中身は表示しない（キー名のみ表示）。

使い方:
  GOOGLE_MAPS_API_KEY=xxxx python scripts/diagnose_places_api_review_fields.py "東京都 港区 歯科医院"
"""
import os
import sys
import json
import requests


def main():
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("❌ 環境変数 GOOGLE_MAPS_API_KEY が設定されていません。", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1] if len(sys.argv) > 1 else "東京都 港区 歯科医院"

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # フィールドマスクは reviews を含む最小限に絞る（課金・レスポンス量削減のため）
        "X-Goog-FieldMask": "places.displayName,places.id,places.reviews",
    }
    data = {"textQuery": query, "languageCode": "ja"}

    print(f"🔍 クエリ: {query}")
    resp = requests.post(url, headers=headers, json=data, timeout=15)
    resp.raise_for_status()
    result = resp.json()

    places = result.get("places", [])
    print(f"📍 取得件数: {len(places)}")

    if not places:
        print("⚠️ 施設が見つかりませんでした。クエリを変えて再実行してください。")
        return

    for place in places:
        reviews = place.get("reviews", [])
        if not reviews:
            continue
        print(f"\n施設: {place.get('displayName', {}).get('text', '?')}")
        print(f"  レビュー件数: {len(reviews)}")
        print(f"  1件目のレビューのキー一覧:")
        print(f"    {sorted(reviews[0].keys())}")
        # 生JSON構造も、値をマスクした状態で1件だけ出力（キーの階層構造を確認するため）
        masked = _mask_values(reviews[0])
        print(f"  キー階層（値はマスク済み）:")
        print(json.dumps(masked, ensure_ascii=False, indent=2))
        return  # 1件確認できれば十分なので終了

    print("⚠️ どの施設にもレビューが含まれていませんでした。")


def _mask_values(obj):
    """値を型情報だけに置き換え、キー構造だけを残す（個人情報を表示しないため）"""
    if isinstance(obj, dict):
        return {k: _mask_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_mask_values(v) for v in obj[:1]]
    return f"<{type(obj).__name__}>"


if __name__ == "__main__":
    main()
