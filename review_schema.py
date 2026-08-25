"""Canonical CSV schema shared by every review acquisition workflow."""

REVIEW_FIELDNAMES = [
    "レビューID",
    "施設ID",
    "施設GID",
    "レビュワー評価",
    "レビュワー名",
    "レビュー日時",
    "レビュー本文",
    "オーナー返信",
    "レビュー表示順位",
    "レビュー取得ソート",
    "関連度ランク",
    "関連度取得ソート",
    "関連度取得日時",
    "レビュー要約",
    "レビューGID",
]

PLACES_REVIEW_SORT_LABEL = "関連度順（Google Places API）"
SERP_REVIEW_SORT_LABEL = "関連度順（SERP API）"
SERP_NEWEST_REVIEW_SORT_LABEL = "新着順（SERP API）"
