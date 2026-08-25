import glob
import json
import os
import re

from address_csv_validator import AddressCsvValidationError, load_address_queries


SEQUENTIAL_EXCLUDED_KEYWORDS = {
    'review',
    'batch',
    'report',
    'fid',
    'heatmap',
    'duplicate',
    'analysis',
    'log',
    'error',
    'summary',
}

FACILITY_EXCLUDED_KEYWORDS = {
    'review',
    'batch',
    'report',
    'fid',
    'heatmap',
    'duplicate',
    'analysis',
    'log',
    'error',
    'summary',
    'add_',
}


def _get_extension(filename):
    return os.path.splitext(filename)[1].lower()


def _address_validation_error(file_path, cache=None):
    if not file_path:
        return "住所CSVの内容を未検証"

    cache = cache if cache is not None else {}
    cache_key = os.path.abspath(file_path)
    if cache_key not in cache:
        try:
            load_address_queries(file_path)
            cache[cache_key] = ""
        except AddressCsvValidationError as exc:
            cache[cache_key] = str(exc)
    return cache[cache_key]


def classify_settings_file(filename, file_path=None, address_validation_cache=None):
    lower_name = filename.lower()
    ext = _get_extension(filename)
    purposes = []
    validation_error = ""

    if ext == '.csv':
        purposes.append('settings_csv')
        if 'address' in lower_name or 'adress' in lower_name:
            validation_error = _address_validation_error(file_path, address_validation_cache)
            if not validation_error:
                purposes.append('address_input')
        if 'exclude' in lower_name:
            purposes.append('exclude_gids')
    elif ext == '.json':
        purposes.append('settings_json')
        if 'settings' in lower_name:
            purposes.append('config')

    entry = {
        'name': filename,
        'path': f'settings/{filename}',
        'extension': ext,
        'purposes': purposes,
    }
    if validation_error:
        # files.jsonは公開されるため、ローカル絶対パスを含む詳細エラーは出さない。
        entry['validation_status'] = 'invalid_address_template'
    return entry


def classify_results_file(filename, size=0, mtime=0):
    lower_name = filename.lower()
    ext = _get_extension(filename)
    purposes = ['results_csv'] if ext == '.csv' else []

    if 'review' in lower_name:
        purposes.append('review_output')
    if 'fid' in lower_name or 'add_data' in lower_name:
        purposes.append('fid_input')
    if 'add_data' in lower_name:
        purposes.append('update_facility_output')
    if 'add_review' in lower_name:
        purposes.append('update_review_output')

    if ext == '.csv' and not any(keyword in lower_name for keyword in SEQUENTIAL_EXCLUDED_KEYWORDS):
        purposes.append('sequential_input')

    if ext == '.csv' and not any(keyword in lower_name for keyword in FACILITY_EXCLUDED_KEYWORDS):
        purposes.append('facility_output')

    return {
        'name': filename,
        'path': f'results/{filename}',
        'extension': ext,
        'purposes': sorted(set(purposes)),
        'size': size,
        'last_modified': mtime,
    }


def _normalize_csv_path(value, root):
    if not value or not isinstance(value, str):
        return ''
    normalized = value.replace('\\', '/').strip()
    if not normalized.startswith(f'{root}/'):
        normalized = f'{root}/{normalized}'
    if not normalized.lower().endswith('.csv'):
        normalized += '.csv'
    return normalized


def extract_places_profiles(settings_dir, address_validation_cache=None):
    """Google Places用設定JSONからWebappに公開できる項目だけを抽出する。"""
    profiles = []
    if not os.path.exists(settings_dir):
        return profiles

    for file_path in sorted(glob.glob(os.path.join(settings_dir, '*.json'))):
        try:
            with open(file_path, 'r', encoding='utf-8') as source:
                payload = json.load(source)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"⚠️  設定プロファイルを読み込めません: {file_path}: {exc}")
            continue

        tasks = payload if isinstance(payload, list) else []
        for index, task in enumerate(tasks):
            if not isinstance(task, dict) or not task.get('query'):
                continue

            filename = os.path.basename(file_path)
            task_name = str(task.get('task_name') or f'task-{index + 1}')
            address_csv = _normalize_csv_path(task.get('address_csv_path'), 'settings')
            address_file = os.path.join(settings_dir, address_csv.replace('settings/', '', 1))
            validation_error = _address_validation_error(address_file, address_validation_cache)
            if validation_error:
                print(
                    "[WARN] 住所CSVが不正なためWebAppプリセットから除外します: "
                    f"{address_csv}: {validation_error}"
                )
                continue

            primary_query = str(task['query']).split(' -', 1)[0]
            profile_hint = f"{filename} {task_name} {task.get('address_csv_path', '')}".lower()
            if 'test' in profile_hint:
                mode = 'テスト'
            elif 'small' in profile_hint:
                mode = '小規模'
            else:
                mode = '通常'
            profiles.append({
                'id': f'settings/{filename}::{task_name}',
                'label': f'{primary_query}（{mode}）',
                'config_file': f'settings/{filename}',
                'task_name': task_name,
                'query': task['query'],
                'included_type': task.get('includedType') or '',
                'address_csv': address_csv,
                'facility_file': _normalize_csv_path(task.get('facility_file'), 'results'),
                'review_file': _normalize_csv_path(task.get('review_file'), 'results'),
                'update_facility_file': _normalize_csv_path(task.get('update_facility_path'), 'results'),
                'update_review_file': _normalize_csv_path(task.get('update_review_path'), 'results'),
                'exclude_gids_file': _normalize_csv_path(task.get('exclude_gids_path'), 'settings'),
            })

    return profiles

def _detect_data_root():
    """
    データルートを検出する（フェイルセーフ設計）
    優先順位: PRIVATE_DATA_ROOT env > private-data/ > /workspaces/googlemap > カレントディレクトリ
    """
    import sys
    from pathlib import Path

    env_root = os.environ.get('PRIVATE_DATA_ROOT', '').strip()
    if env_root:
        p = Path(env_root)
        if p.exists() and (p / 'settings').exists():
            return str(p)
        print(f"⚠️  PRIVATE_DATA_ROOT='{env_root}' に settings/ が見つかりません", file=sys.stderr)

    for candidate in ['private-data', '/workspaces/googlemap']:
        p = Path(candidate)
        if p.exists() and (p / 'settings').exists():
            return str(p)

    # カレントディレクトリにフォールバック
    return '.'


def update_file_list():
    """
    resultsディレクトリ内のファイル一覧を更新し、webapp/files.jsonに保存する
    さらに、GitHub Actionsワークフローファイルの選択肢も自動更新する
    データはプライベートリポジトリ (PRIVATE_DATA_ROOT) から読み込む
    """
    data_root = _detect_data_root()
    results_dir = os.path.join(data_root, 'results')
    settings_dir = os.path.join(data_root, 'settings')
    output_file = 'docs/webapp/files.json'
    print(f"📁 データルート: {data_root}")
    workflow_file = '.github/workflows/brightdata_facility.yml'
    
    print(f"Updating file list from {results_dir} and {settings_dir} to {output_file}")
    
    # settingsディレクトリのCSVファイルを取得
    settings_csv_files = []
    valid_address_csv_files = []
    settings_entries = []
    address_validation_cache = {}
    if os.path.exists(settings_dir):
        for file_path in glob.glob(os.path.join(settings_dir, '*.csv')):
            filename = os.path.basename(file_path)
            settings_csv_files.append(filename)
            entry = classify_settings_file(filename, file_path, address_validation_cache)
            settings_entries.append(entry)
            if 'address_input' in entry['purposes']:
                valid_address_csv_files.append(filename)
    settings_csv_files.sort()
    valid_address_csv_files.sort()
    
    # settingsディレクトリのJSONファイルを取得
    settings_json_files = []
    if os.path.exists(settings_dir):
        for file_path in glob.glob(os.path.join(settings_dir, '*.json')):
            filename = os.path.basename(file_path)
            settings_json_files.append(filename)
            settings_entries.append(classify_settings_file(filename))
    settings_json_files.sort()
    settings_entries.sort(key=lambda entry: entry['name'])
    places_profiles = extract_places_profiles(settings_dir, address_validation_cache)
    
    # resultsディレクトリのCSVファイルを取得
    results_files = []
    if os.path.exists(results_dir):
        for file_path in glob.glob(os.path.join(results_dir, '*.csv')):
            filename = os.path.basename(file_path)
            size = os.path.getsize(file_path)
            mtime = os.path.getmtime(file_path)
            
            results_files.append(classify_results_file(filename, size=size, mtime=mtime))
    
    # 更新日時順にソート
    results_files.sort(key=lambda x: x['last_modified'], reverse=True)
    results_filenames = [f['name'] for f in results_files]
    
    # ディレクトリ作成
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # files.jsonを保存
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'settings': settings_entries,
                'results': results_files,
                'places_profiles': places_profiles,
                'generated_by': 'update_file_list.py',
            }, f, indent=2, ensure_ascii=False)
        print(f"✅ File list saved to {output_file}")
        print(f"   - Settings CSV files: {len(settings_csv_files)}")
        print(f"   - Valid address CSV files: {len(valid_address_csv_files)}")
        print(f"   - Settings JSON files: {len(settings_json_files)}")
        print(f"   - Google Places profiles: {len(places_profiles)}")
        print(f"   - Results files: {len(results_filenames)}")
    except Exception as e:
        print(f"❌ Error saving file list: {e}")
        return False
    
    # ワークフローファイルを更新
    should_update_workflow = os.getenv('UPDATE_WORKFLOW_CHOICES', '').lower() in {'1', 'true', 'yes'}

    if should_update_workflow and os.path.exists(workflow_file):
        print(f"\n📝 Updating workflow file: {workflow_file}")
        update_workflow_choices(workflow_file, valid_address_csv_files, settings_json_files, results_filenames)
    elif should_update_workflow:
        print(f"⚠️  Workflow file not found: {workflow_file}")
    else:
        print("ℹ️  Workflow choice update skipped")
    
    return True

def update_workflow_choices(workflow_file, settings_csv_files, settings_json_files, results_files):
    """
    ワークフローファイルの選択肢を自動更新する
    """
    try:
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # config_file の選択肢を更新
        config_options = "          - 'settings/settings.json'"
        for filename in settings_json_files:
            if filename != 'settings.json':  # デフォルトは最初に追加済み
                config_options += f"\n          - 'settings/{filename}'"
        config_options += "\n"
        
        # config_file セクションを置換
        config_pattern = r"(      config_file:[\s\S]*?options:\n)([\s\S]*?)(        default: 'settings/)"
        config_replacement = r"\1" + config_options + r"\3"
        content = re.sub(config_pattern, config_replacement, content)
        
        # address_csv の選択肢を更新
        address_options = "          - 'default'\n"
        for filename in settings_csv_files:
            address_options += f"          - 'settings/{filename}'\n"
        
        # address_csv セクションを置換
        address_pattern = r"(      address_csv:[\s\S]*?options:\n)([\s\S]*?)(        default: 'default')"
        address_replacement = r"\1" + address_options + r"\3"
        content = re.sub(address_pattern, address_replacement, content)
        
        # output_file の説明文を更新（既存ファイルリストを表示）
        output_description = "'出力ファイル名（既存ファイル選択または新規ファイル名入力）"
        if results_files:
            output_description += "\n\n          既存ファイル: " + ", ".join(results_files[:10])
            if len(results_files) > 10:
                output_description += f" ...他{len(results_files)-10}件"
        output_description += "'"
        
        # output_file の description を置換
        output_desc_pattern = r"(      output_file:\n        description: )['\"].*?['\"]"
        output_desc_replacement = r"\1" + output_description
        content = re.sub(output_desc_pattern, output_desc_replacement, content, flags=re.DOTALL)
        
        # ファイルに書き込み
        with open(workflow_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Workflow file updated successfully")
        print(f"   - Config file options: {len(settings_json_files)}")
        print(f"   - Address CSV options: {len(settings_csv_files)}")
        print(f"   - Output file description updated with {len(results_files)} files")
        
    except Exception as e:
        print(f"❌ Error updating workflow file: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = update_file_list()
    exit(0 if success else 1)
