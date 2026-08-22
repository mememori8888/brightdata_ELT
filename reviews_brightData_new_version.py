#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reviews_brightData_new_version.py
新仕様: PRIVATE_DATA_ROOT のデータを使ってレビュースクレイパーを起動するラッパー

run_reviews_local_interactive.py の自動実行（非対話）バージョン。
データディレクトリを PRIVATE_DATA_ROOT 環境変数で切り替えられる。

使用方法:
  # ローカル（データが /workspaces/googlemap にある場合、自動検出）
  python reviews_brightData_new_version.py

  # データルートを明示指定
  PRIVATE_DATA_ROOT=/path/to/data python reviews_brightData_new_version.py

  # 主要パラメータを env で指定
  INPUT_CSV=results/dental_new.csv \\
  OUTPUT_CSV=results/dental_reviews.csv \\
  DAYS_BACK=10 \\
  python reviews_brightData_new_version.py
"""
import os
import sys
import subprocess
from pathlib import Path


# ─────────────────────────────────────────────
# データルート検出
# 優先順位: PRIVATE_DATA_ROOT env > /workspaces/googlemap > カレントディレクトリ
# ─────────────────────────────────────────────
def detect_data_root() -> Path:
    """データルートを検出する（フェイルセーフ設計）"""

    # 1. 環境変数で明示指定
    env_root = os.environ.get("PRIVATE_DATA_ROOT", "").strip()
    if env_root:
        p = Path(env_root)
        if p.exists() and (p / "results").exists():
            return p
        print(f"⚠️  PRIVATE_DATA_ROOT='{env_root}' に results/ ディレクトリが見つかりません", file=sys.stderr)

    # 2. Codespaces / ローカルの標準パス
    for candidate in [Path("/workspaces/googlemap"), Path.home() / "googlemap"]:
        if candidate.exists() and (candidate / "results").exists():
            return candidate

    # 3. カレントディレクトリにフォールバック
    cwd = Path.cwd()
    if (cwd / "results").exists():
        return cwd

    # 4. スクリプトのディレクトリにフォールバック
    return Path(__file__).parent


# ─────────────────────────────────────────────
# パスの解決ユーティリティ
# ─────────────────────────────────────────────
def resolve_path(raw: str, data_root: Path) -> Path:
    """相対パスは data_root 基準で絶対パスに変換する"""
    p = Path(raw)
    return p if p.is_absolute() else (data_root / p).resolve()


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────
def main() -> None:
    data_root = detect_data_root()
    results_dir = data_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # ─── ファイルパスの解決 ───
    csv_file = resolve_path(
        os.environ.get("INPUT_CSV", "results/dental_new.csv"),
        data_root,
    )
    output_file = resolve_path(
        os.environ.get("OUTPUT_CSV", "results/dental_new_reviews.csv"),
        data_root,
    )

    print(f"📁 データルート : {data_root}")
    print(f"📂 入力CSV      : {csv_file}")
    print(f"📄 出力CSV      : {output_file}")

    # ─── 入力ファイルの存在確認 ───
    if not csv_file.exists():
        print(f"❌ エラー: 入力CSVが見つかりません: {csv_file}", file=sys.stderr)
        print("  INPUT_CSV 環境変数で正しいパスを指定してください", file=sys.stderr)
        sys.exit(1)

    # ─── 呼び出しスクリプトの確認 ───
    script_path = (Path(__file__).parent / "run_reviews_local_interactive.py").resolve()
    if not script_path.exists():
        print(f"❌ エラー: run_reviews_local_interactive.py が見つかりません: {script_path}", file=sys.stderr)
        sys.exit(1)

    # ─── コマンドライン引数の構築 ───
    cmd = [
        sys.executable,
        str(script_path),
        "--non-interactive",
        "--input", str(csv_file),
        "--output", str(output_file),
    ]

    # オプション引数（環境変数から取得）
    optional_args = [
        ("DAYS_BACK",         "--days-back"),
        ("BATCH_SIZE",        "--batch-size"),
        ("MAX_WAIT_MINUTES",  "--max-wait-minutes"),
        ("DATASET_ID",        "--dataset-id"),
        ("SKIP_COLUMN",       "--skip-column"),
        ("START_ROW",         "--start-row"),
        ("END_ROW",           "--end-row"),
        ("ROWS_PER_BATCH",    "--rows-per-batch"),
        ("BATCH_WAIT",        "--batch-wait"),
    ]
    for env_key, flag in optional_args:
        val = os.environ.get(env_key, "").strip()
        if val:
            cmd += [flag, val]

    # バッチモード
    if os.environ.get("BATCH_MODE", "").lower() in ("true", "1", "yes"):
        cmd.append("--batch-mode")

    # 増分ファイル
    update_raw = os.environ.get("UPDATE_FILE", "").strip()
    if update_raw:
        update_file = resolve_path(update_raw, data_root)
        cmd += ["--update", str(update_file)]

    # ─── 環境変数の構築 ───
    env = os.environ.copy()
    env["PRIVATE_DATA_ROOT"] = str(data_root)

    # ─── 実行（CWD をデータルートに設定してパスを自然に解決）───
    result = subprocess.run(
        cmd,
        env=env,
        cwd=str(data_root),
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
