"""Validate and load address CSV files used by facility search workflows."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path


PREFECTURES = {
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
}

HEADER_ALIASES = (
    {"都道府県", "prefecture"},
    {"市区町村", "city", "municipality", "city_town"},
    {"町域", "区", "町名", "住所", "town", "ward", "district", "address"},
    {"丁目", "大字", "街区", "street", "area"},
    {"補足", "小字", "番地", "detail", "address_detail"},
)


class AddressCsvValidationError(ValueError):
    """Raised when an address CSV cannot be used safely."""


def _normalized_header(row: list[str]) -> list[str]:
    return [cell.strip().lower() for cell in row]


def _is_supported_header(row: list[str]) -> bool:
    header = _normalized_header(row)
    if not 2 <= len(header) <= len(HEADER_ALIASES):
        return False

    legacy_header = [chr(ord("a") + index) for index in range(len(header))]
    if header == legacy_header:
        return True

    return all(value in HEADER_ALIASES[index] for index, value in enumerate(header))


def load_address_queries(csv_path: os.PathLike[str] | str) -> list[str]:
    """Return normalized address queries after validating the CSV template.

    The first row must be either the legacy ``a,b,...`` header or a descriptive
    header beginning with ``都道府県,市区町村`` (English aliases are also
    accepted). Blank lines are ignored and the legacy ``end,end`` marker ends
    the input.
    """

    path = Path(csv_path)
    if not path.is_file():
        raise AddressCsvValidationError(f"住所CSVが見つかりません: {path}")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))
    except UnicodeDecodeError as exc:
        raise AddressCsvValidationError(
            f"住所CSVはUTF-8で保存してください（Shift_JIS/文字化けは使用不可）: {path}"
        ) from exc
    except (OSError, csv.Error) as exc:
        raise AddressCsvValidationError(f"住所CSVを読み込めません: {path}: {exc}") from exc

    if not rows or not any(cell.strip() for cell in rows[0]):
        raise AddressCsvValidationError(f"住所CSVの1行目にヘッダーがありません: {path}")

    header = [cell.strip() for cell in rows[0]]
    if not _is_supported_header(header):
        raise AddressCsvValidationError(
            "住所CSVのヘッダーが不正です。"
            "1行目を『都道府県,市区町村,町域』または既存互換の『a,b,c』形式にしてください: "
            f"{path}"
        )

    expected_columns = len(header)
    addresses: list[str] = []
    for line_number, raw_row in enumerate(rows[1:], start=2):
        row = [cell.strip() for cell in raw_row]
        while row and not row[-1]:
            row.pop()
        if not row:
            continue

        if len(row) >= 2 and row[0].lower() == "end" and row[1].lower() == "end":
            break

        if len(row) > expected_columns:
            raise AddressCsvValidationError(
                f"住所CSVの{line_number}行目はヘッダーより列数が多いです"
                f"（ヘッダー{expected_columns}列、データ{len(row)}列）: {path}"
            )
        if len(row) < 2 or not row[0] or not row[1]:
            raise AddressCsvValidationError(
                f"住所CSVの{line_number}行目は都道府県と市区町村が必須です: {path}"
            )
        if any(cell.lstrip().startswith(("=", "+", "@")) for cell in row if cell):
            raise AddressCsvValidationError(
                f"住所CSVの{line_number}行目に数式または不正なセル値があります: {path}"
            )
        if row[0] not in PREFECTURES:
            raise AddressCsvValidationError(
                f"住所CSVの{line_number}行目の都道府県が不正です: {row[0]}: {path}"
            )

        addresses.append(" ".join(cell for cell in row if cell))

    if not addresses:
        raise AddressCsvValidationError(
            f"住所CSVにはヘッダー以外に1行以上の住所データが必要です: {path}"
        )

    return addresses


def _safe_address_path(raw_path: str, config_path: Path | None = None) -> Path:
    normalized = raw_path.replace("\\", "/").strip()
    candidate = Path(normalized)
    if (
        not normalized
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.suffix.lower() != ".csv"
    ):
        raise AddressCsvValidationError(
            f"住所CSVは settings/*.csv の形式で指定してください: {raw_path}"
        )

    if candidate.parts and candidate.parts[0] == "settings":
        if config_path and config_path.is_absolute() and config_path.parent.name == "settings":
            return config_path.parent.parent / candidate
        return candidate

    if config_path:
        return config_path.parent / candidate
    return Path("settings") / candidate


def validate_config_addresses(
    config_file: os.PathLike[str] | str,
    address_override: str | None = None,
) -> list[tuple[Path, int]]:
    """Validate an override address CSV or every address CSV in a config file."""

    config_path = Path(config_file)
    if address_override:
        paths = [_safe_address_path(address_override, config_path)]
    else:
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AddressCsvValidationError(
                f"設定ファイルから住所CSVを確認できません: {config_path}: {exc}"
            ) from exc
        if not isinstance(payload, list):
            raise AddressCsvValidationError(f"設定ファイルはタスクの配列である必要があります: {config_path}")

        paths = []
        for index, task in enumerate(payload, start=1):
            if not isinstance(task, dict) or not task.get("address_csv_path"):
                raise AddressCsvValidationError(
                    f"設定ファイルのタスク{index}に address_csv_path がありません: {config_path}"
                )
            paths.append(_safe_address_path(str(task["address_csv_path"]), config_path))

    validated = []
    seen = set()
    for path in paths:
        normalized_path = str(path.resolve())
        if normalized_path in seen:
            continue
        seen.add(normalized_path)
        validated.append((path, len(load_address_queries(path))))
    return validated


def main() -> int:
    parser = argparse.ArgumentParser(description="住所CSVテンプレートを検証します")
    parser.add_argument("--config-file", required=True, help="settings/*.json")
    parser.add_argument("--address-csv", help="指定時は設定ファイルの住所CSVを上書き")
    args = parser.parse_args()

    try:
        results = validate_config_addresses(args.config_file, args.address_csv)
    except AddressCsvValidationError as exc:
        print(f"[ERROR] 住所CSV検証エラー: {exc}", file=sys.stderr)
        return 1

    for path, count in results:
        print(f"[OK] 住所CSV: {path}（検索対象{count}行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
