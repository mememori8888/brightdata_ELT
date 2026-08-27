"""
カテゴリの副産物の仕分処理の追加
output.jsonを先に取得するデザインの検討の為の出力テスト
"""
import os
import requests
import json
import csv
import datetime
import re
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import random
from pathlib import Path

from address_csv_validator import load_address_queries
from places_csv_store import PlacesCsvStore, atomic_write_json, places_run_signature
from review_schema import PLACES_REVIEW_SORT_LABEL, REVIEW_FIELDNAMES

randomC = random.uniform(1,5)

FACILITY_FIELDNAMES = [
    '施設ID', '施設名', '電話番号', '郵便番号', '都道府県', '市区町村', '住所',
    'web', 'GoogleMap', 'ランク', 'カテゴリ', '緯度', '経度', '施設GID', '営業ステータス'
]
REVIEW_UPDATE_FIELDNAMES = [
    'レビューID', '施設GID_レビュー', *REVIEW_FIELDNAMES[3:]
]
UPDATE_FIELDNAMES = [*FACILITY_FIELDNAMES, *REVIEW_UPDATE_FIELDNAMES]


def normalize_review_dataframe(dataframe):
    """Add missing review columns and return the canonical 15-column order."""
    normalized = dataframe.copy()
    for column in REVIEW_FIELDNAMES:
        if column not in normalized.columns:
            normalized[column] = ''
    return normalized.loc[:, REVIEW_FIELDNAMES]


def build_places_review_row(review, assigned_review_id, facility_id, facility_gid, display_order):
    """Convert one Places API review to the shared review CSV schema.

    Places API (New) does not return owner replies or the separate relevance
    enrichment fields. Those columns remain blank so that downstream CSV
    consumers can use the same schema as the Bright Data Dataset workflow.
    """
    review_name = str(review.get('name') or '')
    review_gid_match = re.search(r"/([^/]+)$", review_name)
    review_gid = review_gid_match.group(1) if review_gid_match else review_name

    text = review.get('text') or review.get('originalText') or {}
    if isinstance(text, dict):
        text = text.get('text', '')

    author = review.get('authorAttribution') or {}
    return {
        'レビューID': assigned_review_id,
        '施設ID': facility_id,
        '施設GID': facility_gid,
        'レビュワー評価': review.get('rating', ''),
        'レビュワー名': author.get('displayName', ''),
        'レビュー日時': review.get('publishTime', ''),
        'レビュー本文': text,
        'オーナー返信': '',
        'レビュー表示順位': display_order,
        'レビュー取得ソート': PLACES_REVIEW_SORT_LABEL,
        '関連度ランク': '',
        '関連度取得ソート': '',
        '関連度取得日時': '',
        'レビュー要約': '',
        'レビューGID': review_gid,
    }

def extract_api_key_from_json(file_path):
    """
    指定されたJSONファイルからAPIキーを抽出します。

    Args:
        file_path (str): JSONファイルのパス

    Returns:
        str: 抽出されたAPIキー
    """

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    api_key = data['api_key']
    return api_key



def update_mini(base_query,api_key, file_path, facility_file, review_file, update_facility_path, update_review_path, exclude_gids_path, results_dir, included_type=None):
    def split_to_csv(df, file_path, chunksize=10000, mode='a'): #チャンクでcsvに出力
        # 'w'モードの初回書き込みか、'a'モードでファイルが存在しない場合にヘッダーを書き込む
        write_header = (mode == 'w') or (not os.path.exists(file_path) or os.path.getsize(file_path) == 0)

        for i in range(0, len(df), chunksize):
            # 'w'モードの場合、最初のチャンクで上書きし、以降は追記('a')モードに切り替える
            current_mode = 'w' if i == 0 and mode == 'w' else 'a'
            # ヘッダーを書き込むのは、ループの初回かつ、書き込みが必要と判断された場合のみ
            is_first_chunk_and_header_needed = (i == 0 and write_header)
            df.iloc[i:i+chunksize].to_csv(f"{file_path}", mode=current_mode, index=False, header=is_first_chunk_and_header_needed, encoding='utf-8')

    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def bs_address(text):
            # HTMLを解析
        soup = BeautifulSoup(text, 'html.parser')

        # class="region"を持つ要素を検索
        region_element = soup.find('span', class_='region')
        region_element_street = soup.find('span', class_='street-address')
        # 要素のテキストを取得
        if region_element:
            region = region_element.text
            region_street = region_element_street.text
           
        else:
            region = 'not found'
            region_street = 'not found'
        return region,region_street

    def split_address(address_text):
        """
        住所文字列を郵便番号と住所に分割する関数

        Args:
            address_text: 分割したい住所文字列

        Returns:
            tuple: (郵便番号, 住所)
        """

        # 郵便番号の正規表現 (数字5桁または7桁)
        postal_code_pattern = r'〒\d{3}-\d{4}|〒\d{7}'

        # 郵便番号部分を抽出
        match = re.search(postal_code_pattern, address_text)
        if match:
            postal_code = match.group()
            address = address_text.replace(postal_code, "").strip()
            return postal_code, address
        else:
            return None, address_text



    def convert_date_format(date_str):
        """
        日付文字列のフォーマットを変換する関数

        Args:
            date_str: 変換する日付文字列 (例: "2013-12-13")

        Returns:
            変換後の日付文字列 (例: "2013年12月13日")
        """

        # 文字列をdatetimeオブジェクトに変換
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')

        # datetimeオブジェクトを新しいフォーマットの文字列に変換
        new_format = date_obj.strftime('%Y年%m月%d日')
        return new_format

    def search_places(api_key, query,fields,page_token=None,**kwargs):
        """
        Google Places API (新版) の searchText API を呼び出す関数

        Args:
            api_key: Google Places API の API キー
            query: 検索クエリ
            page_token: 次のページのトークン (初回は None)

        Returns:
            辞書形式の検索結果
        """

        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": fields
        }
        data = {
            "textQuery": query
        }
        data.update(kwargs)
        if page_token:
            data["pageToken"] = page_token

        # 指数バックオフ
        max_retries = 5
        base = 2
        jitter=True

        for attempt in range(1, max_retries + 1):
          response = None
          try:
              response = requests.post(url, headers=headers, json=data, timeout=15)
              response.raise_for_status()  # ステータスコードが異常な場合、例外を発生させる
              return response.json()

          except requests.exceptions.RequestException as e:
              error_message = f"APIリクエスト失敗 (試行 {attempt}/{max_retries}): {e}"
              if response is not None:
                  try:
                      error_details = response.json()
                      error_message += f" - 詳細: {error_details}"
                  except (requests.exceptions.JSONDecodeError, AttributeError, ValueError):
                      error_message += f" - レスポンスボディ: {response.text}"
              logging.warning(error_message)
              delay = base ** attempt
              if jitter:
                  delay += random.uniform(0, delay)
              time.sleep(delay)

        raise Exception("Max retries exceeded.")

    # ログ設定
    log_file_path = os.path.join(results_dir, 'app.log')
    
    # 既存のハンドラーをクリア（複数回実行時の重複を防止）
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()
    
    # ログファイルを初期化（上書きモード）
    logging.basicConfig(filename=log_file_path, filemode='w', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s')

    # APIキーを抽出
    # api_key = extract_api_key_from_json(api_file_path)

    # API キーを置き換えてください
    # 使用例
    # query = "東京都 港区 斎場||葬儀場||告別式"
    fields = ','.join(["places.displayName",
              "places.formattedAddress",
              "places.attributions",
              "places.id",
              "places.name",
              "nextPageToken",
              "places.addressComponents",
              "places.adrFormatAddress",
              "places.displayName",
              "places.nationalPhoneNumber",
              "places.location",
              "places.rating",
              "places.primaryTypeDisplayName",
              "places.websiteUri",
              "places.googleMapsUri",
              "places.reviews",
              "places.userRatingCount",
              "places.regularOpeningHours",
              "places.regularSecondaryOpeningHours"
             ])

    # 他のパラメータを追加
    params = {
        "languageCode":"ja",
        "includePureServiceAreaBusinesses":True
    }
    if included_type:
        params["includedType"] = included_type

    # 除外GIDリストの読み込み
    exclude_gids = set()
    if exclude_gids_path and os.path.exists(exclude_gids_path):
        try:
            with open(exclude_gids_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                exclude_gids = {row[0] for row in reader if row}
            print(f"除外GIDリスト '{exclude_gids_path}' を読み込みました。{len(exclude_gids)}件のGIDを除外します。")
        except Exception as e:
            logging.error(f"除外GIDリスト '{exclude_gids_path}' の読み込みに失敗しました: {e}")

    address_list = load_address_queries(file_path)
    request_count = 0
    request_log = []
    output_paths = [facility_file, review_file, update_facility_path, update_review_path]
    signature_conditions = json.dumps(
        {"query": base_query, "included_type": included_type or ""},
        ensure_ascii=False,
        sort_keys=True,
    )
    signature = places_run_signature(file_path, signature_conditions, output_paths)
    progress_dir = Path(results_dir) / "progress"
    progress_path = progress_dir / f"places_{signature}.json"
    database_path = progress_dir / f"places_{signature}.sqlite3"
    run_status_path = Path(results_dir) / "places_run_status.json"
    progress = {}
    if progress_path.exists():
        try:
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logging.warning("住所処理の進捗JSONを読み込めないため、最初から実行します。")
    can_resume = (
        progress.get("signature") == signature
        and progress.get("status") in {"running", "partial", "failed"}
        and database_path.exists()
    )
    start_address_index = int(progress.get("next_address_index", 0)) if can_resume else 0
    soft_limit_minutes = max(float(os.environ.get("PLACES_SOFT_LIMIT_MINUTES", "240")), 1.0)
    started_at = time.monotonic()

    store = PlacesCsvStore(
        database_path,
        facility_file,
        review_file,
        FACILITY_FIELDNAMES,
        REVIEW_FIELDNAMES,
        resume=can_resume,
    )

    def write_progress(status, next_address_index, error_type=""):
        payload = {
            "signature": signature,
            "status": status,
            "address_csv": str(file_path),
            "search_query": base_query,
            "included_type": included_type or "",
            "output_files": [str(path) for path in output_paths],
            "completed_address_rows": next_address_index,
            "next_address_index": next_address_index,
            "total_address_rows": len(address_list),
            "request_count": request_count,
            "error_type": error_type,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        atomic_write_json(progress_path, payload)
        atomic_write_json(run_status_path, payload)

    def export_checkpoint():
        store.export(facility_file, review_file, update_facility_path, update_review_path)
        counts = store.counts()
        print(
            "SQLite照合結果: "
            f"施設{counts['facilities']}件（新規{counts['new_facilities']}件）、"
            f"レビュー{counts['reviews']}件（新規{counts['new_reviews']}件）"
        )

    try:
        if can_resume:
            print(f"住所処理を{start_address_index + 1}行目から再開します。")

        for address_index in range(start_address_index, len(address_list)):
            if (time.monotonic() - started_at) / 60 >= soft_limit_minutes:
                export_checkpoint()
                write_progress("partial", address_index, "soft_deadline")
                print(
                    f"{soft_limit_minutes:g}分のソフト上限に到達したため、"
                    f"住所{address_index + 1}行目から次回再開します。"
                )
                return request_count

            query = address_list[address_index]
            search_query = f'{query} {base_query}'
            print(f'現在の検索キーワード　{query} {base_query} ')
            page_token = None
            query_request_count = 0
            store.begin_address()
            try:
                while True:
                    time.sleep(2)
                    request_count += 1
                    query_request_count += 1
                    results = search_places(api_key, search_query, fields, page_token, **params)
                    places = results.get('places') or []
                    if not places:
                        print("responseがありませんでした。")
                        break
                    print(f"responseがありました。施設数: {len(places)}")

                    for result in places:
                        facility_gid = str(result.get('id') or '').strip()
                        if not facility_gid:
                            logging.warning("Place IDが空の施設は重複照合できないためスキップします。")
                            continue
                        if facility_gid in exclude_gids:
                            print(f"GID '{facility_gid}' は除外リストに含まれているためスキップします。")
                            continue

                        facility_name = result.get('displayName', {}).get('text', '#N/A')
                        prefecture = '?'
                        city = '?'
                        try:
                            formatted_address = result.get('formattedAddress', '')
                            postal_code, address = split_address(formatted_address)
                            address = address.replace('日本、', '')
                            for component in result.get("addressComponents", []):
                                if "administrative_area_level_1" in component.get("types", []):
                                    prefecture = component.get("longText", "?")
                                elif "locality" in component.get("types", []):
                                    city = component.get("longText", "?")
                                elif "administrative_area_level_2" in component.get("types", []):
                                    city = component.get("longText", "?")
                        except Exception:
                            address = '#N/A '
                            postal_code = '#N/A '
                            prefecture = '#N/A '
                            city = '#N/A '

                        facility_tell = result.get('nationalPhoneNumber', '#N/A ')
                        facility_location = result.get('location') or {}
                        facility_lati = facility_location.get('latitude', '#N/A ')
                        facility_long = facility_location.get('longitude', '#N/A ')
                        facility_rank = result.get('rating', '#N/A ')
                        facility_cat = (result.get('primaryTypeDisplayName') or {}).get('text', '#N/A')
                        facility_web = result.get('websiteUri', '#N/A ')
                        facility_gmap = result.get('googleMapsUri', '#N/A ')

                        if postal_code and prefecture and city:
                            address = address.replace(str(postal_code), '').replace(str(prefecture), '').replace(str(city), '')
                        else:
                            address = '#N/A'

                        facility_row = {
                            '施設ID': '',
                            '施設名': facility_name,
                            '電話番号': facility_tell,
                            '郵便番号': postal_code or '',
                            '都道府県': prefecture,
                            '市区町村': city,
                            '住所': address,
                            'web': facility_web,
                            'GoogleMap': facility_gmap,
                            'ランク': facility_rank,
                            'カテゴリ': facility_cat,
                            '緯度': facility_lati,
                            '経度': facility_long,
                            '施設GID': facility_gid,
                            '営業ステータス': '',
                        }
                        assigned_facility_id, is_new_facility = store.add_facility(facility_row)
                        if is_new_facility:
                            print('新しい施設です。')

                        for display_order, review in enumerate(result.get('reviews') or [], start=1):
                            review_row = build_places_review_row(
                                review,
                                assigned_review_id='',
                                facility_id=assigned_facility_id,
                                facility_gid=facility_gid,
                                display_order=display_order,
                            )
                            if not str(review_row.get('レビューGID') or '').strip():
                                logging.warning("レビューGIDが空のためレビューをスキップします。")
                                continue
                            _, is_new_review = store.add_review(review_row)
                            if is_new_review:
                                print("新しいreviewがありました。")

                    page_token = results.get('nextPageToken')
                    print(f'リクエスト {request_count}回目 (クエリ内 {query_request_count}回目)')
                    if not page_token:
                        break

                store.commit_address()
                request_log.append({'query': query, 'request_count': query_request_count})
                write_progress("running", address_index + 1)
            except BaseException:
                store.rollback_address()
                export_checkpoint()
                write_progress("failed", address_index, "api_or_processing_error")
                raise

        export_checkpoint()
        write_progress("success", len(address_list))
        store.close(remove_database=True)
        store = None
        print("施設情報.csvとレビュー情報.csvを更新しました")
        return request_count
    finally:
        if store is not None:
            store.close()
        # Windowsでも一時・出力ディレクトリを直ちに扱えるよう、今回のログを閉じる。
        for handler in logging.root.handlers[:]:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == os.path.abspath(log_file_path):
                logging.root.removeHandler(handler)
                handler.close()

def run_from_config(config_file, file_overrides=None):
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except FileNotFoundError:
        print(f"エラー: 設定ファイル '{config_file}' が見つかりません。")
        return
    except json.JSONDecodeError:
        print(f"エラー: 設定ファイル '{config_file}' の形式が不正です。JSON形式を確認してください。")
        return

    # 環境変数からAPIキーを取得（GitHub Secrets: GOOGLE_MAPS_API_KEY を想定）
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("エラー: 環境変数 'GOOGLE_MAPS_API_KEY' が設定されていません。")
        print("  GitHub Actionsの場合はSecretsに、ローカル実行の場合は環境変数として設定してください。")
        return

    def _safe_join(base_dir, raw_path):
        """base_dir が既に含まれている場合は二重に連結しない（例: settings/settings/... を防ぐ）"""
        if raw_path is None:
            return None
        normalized = raw_path.replace('\\', '/')
        if normalized == base_dir or normalized.startswith(f"{base_dir}/"):
            return raw_path
        return os.path.join(base_dir, raw_path)

    file_overrides = {
        key: value for key, value in (file_overrides or {}).items() if value
    }
    override_roots = {
        'address_csv_path': 'settings',
        'facility_file': 'results',
        'review_file': 'results',
        'update_facility_path': 'results',
        'update_review_path': 'results',
        'exclude_gids_path': 'settings',
    }
    for key, value in file_overrides.items():
        if key in {'query', 'includedType'}:
            continue
        normalized = value.replace('\\', '/')
        parts = normalized.split('/')
        expected_root = override_roots.get(key)
        if (
            not expected_root
            or os.path.isabs(value)
            or '..' in parts
            or not normalized.startswith(f'{expected_root}/')
            or not normalized.lower().endswith('.csv')
        ):
            raise ValueError(
                f"Invalid {key}: '{value}'. Expected {expected_root}/*.csv"
            )

    for task in tasks:
        # Webapp / GitHub Actions から指定されたファイルだけを設定値へ上書きする。
        # 未指定時は従来どおり settings.json の値を使うため、既存実行との互換性を保つ。
        task = {**task, **file_overrides}
        task_name = task.get('task_name', '未定義タスク')
        base_query = task.get('query')
        included_type = task.get('includedType')
        # 結果を保存するディレクトリを作成
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)

        # ファイルパスを解決（settings.json側に既にフォルダ名を含む場合と含まない場合の両方に対応）
        file_path = _safe_join('settings', task.get('address_csv_path')) # address.csvはsettingsフォルダにある想定
        facility_file = _safe_join(results_dir, task.get('facility_file'))
        review_file = _safe_join(results_dir, task.get('review_file'))
        update_facility_path = _safe_join(results_dir, task.get('update_facility_path'))
        update_review_path = _safe_join(results_dir, task.get('update_review_path'))
        exclude_gids_path = _safe_join('settings', task.get('exclude_gids_path')) if task.get('exclude_gids_path') else None # 設定ファイルから読み込む

        print(f'設定された検索クエリの業種は　{base_query}')
        print(f'設定された検索クエリの住所は　{file_path}')
        if included_type:
            print(f'設定されたカテゴリは　{included_type}')
        print(f'設定された施設情報ファイルは　{facility_file}')
        print(f'設定されたレビュー情報ファイルは　{review_file}')
        print(f'設定された増分施設情報ファイルは　{update_facility_path}')
        print(f'設定された増分レビューファイルは　{update_review_path}')
        print(f'設定された除外GIDファイルは　{exclude_gids_path}')
        # address_csv_pathは必須だが、他は生成されるのでチェック対象から外す
        if not all([base_query, task.get('address_csv_path'), task.get('facility_file'), task.get('review_file'), task.get('update_facility_path'), task.get('update_review_path')]):
            print(f"エラー: タスク '{task_name}' に必要な設定情報が不足しています。スキップします。")
            continue
        time.sleep(10)
        # try:
        print(f"\n--- タスク '{task_name}' の処理を開始 ---")
        total_requests = update_mini(
            base_query = base_query,
            api_key=api_key, # api_key.jsonから取得したAPIキーを渡す
            file_path=file_path,
            facility_file=facility_file,
            review_file=review_file,
            update_facility_path=update_facility_path,
            update_review_path=update_review_path,
            exclude_gids_path=exclude_gids_path,
            results_dir=results_dir,
            included_type=included_type
        )
        print(f"--- タスク '{task_name}' の処理が完了しました ---")
        print(f"合計リクエスト数: {total_requests}")
        # except Exception as e:
        #     print(f"エラー: タスク '{task_name}' の実行中に予期せぬエラーが発生しました: {e}")
        #     logging.error(f"タスク '{task_name}' の実行中にエラーが発生: {e}")


if __name__ == "__main__":
    CONFIG_FILE = os.environ.get('CONFIG_FILE', 'settings/settings.json')
    FILE_OVERRIDES = {
        'query': os.environ.get('SEARCH_QUERY'),
        'includedType': os.environ.get('INCLUDED_TYPE'),
        'address_csv_path': os.environ.get('ADDRESS_CSV_FILE'),
        'facility_file': os.environ.get('FACILITY_FILE'),
        'review_file': os.environ.get('REVIEW_FILE'),
        'update_facility_path': os.environ.get('UPDATE_FACILITY_FILE'),
        'update_review_path': os.environ.get('UPDATE_REVIEW_FILE'),
        'exclude_gids_path': os.environ.get('EXCLUDE_GIDS_FILE'),
    }
    print(f"🚀 Starting with CONFIG_FILE: {CONFIG_FILE}")
    run_from_config(CONFIG_FILE, FILE_OVERRIDES)
