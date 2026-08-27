"""Disk-backed CSV matching and checkpoint storage for Google Places runs."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence


CSV_TRANSACTION_SIZE = 10_000


def _integer(value, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _json_row(row: Mapping[str, object]) -> str:
    return json.dumps(
        {str(key): "" if value is None else str(value) for key, value in row.items()},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def atomic_write_json(path: os.PathLike[str] | str, payload: Mapping[str, object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def places_run_signature(
    address_file: os.PathLike[str] | str,
    query: str,
    output_paths: Sequence[os.PathLike[str] | str],
) -> str:
    digest = hashlib.sha256()
    with Path(address_file).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    digest.update(query.encode("utf-8"))
    for output_path in output_paths:
        digest.update(str(Path(output_path).resolve()).encode("utf-8"))
    return digest.hexdigest()[:24]


class PlacesCsvStore:
    """SQLite-backed index that preserves CSV order without loading every row."""

    def __init__(
        self,
        database_path: os.PathLike[str] | str,
        facility_file: os.PathLike[str] | str,
        review_file: os.PathLike[str] | str,
        facility_fields: Sequence[str],
        review_fields: Sequence[str],
        *,
        resume: bool = False,
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        if not resume and self.database_path.exists():
            self.database_path.unlink()
        self.connection = sqlite3.connect(self.database_path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.execute("PRAGMA temp_store=FILE")
        self.facility_fields = list(facility_fields)
        self.review_fields = list(review_fields)
        self._address_transaction = False
        self._create_schema()
        if resume:
            self._load_metadata()
        else:
            self._initialize_from_csv(Path(facility_file), Path(review_file))

    def _create_schema(self) -> None:
        for table in ("facilities", "reviews"):
            self.connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    storage_key TEXT PRIMARY KEY,
                    gid TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    ordinal INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    is_new INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self.connection.execute(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {table}_gid_unique "
                f"ON {table}(gid) WHERE gid <> ''"
            )
            self.connection.execute(
                f"CREATE INDEX IF NOT EXISTS {table}_ordinal_index ON {table}(ordinal)"
            )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.connection.commit()

    @staticmethod
    def _read_header(path: Path) -> list[str]:
        if not path.exists() or path.stat().st_size == 0:
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(next(csv.reader(handle), []))

    def _initialize_from_csv(self, facility_file: Path, review_file: Path) -> None:
        existing_facility_fields = self._read_header(facility_file)
        self.facility_fields = list(dict.fromkeys([*existing_facility_fields, *self.facility_fields]))
        # Review output is intentionally normalized to the canonical shared schema.
        max_facility_id = self._import_csv("facilities", facility_file, "施設GID", "施設ID")
        max_review_id = self._import_csv("reviews", review_file, "レビューGID", "レビューID")
        self._set_metadata("facility_fields", self.facility_fields)
        self._set_metadata("review_fields", self.review_fields)
        # CSV全行の最大値を使う。重複GID行が索引で除外されてもIDを再利用しない。
        self._set_metadata("next_facility_id", max(max_facility_id + 1, 101))
        self._set_metadata("next_review_id", max(max_review_id + 1, 1))
        self.connection.commit()

    def _load_metadata(self) -> None:
        facility_fields = self._get_metadata("facility_fields")
        review_fields = self._get_metadata("review_fields")
        if facility_fields:
            self.facility_fields = list(facility_fields)
        if review_fields:
            self.review_fields = list(review_fields)

    def _import_csv(self, table: str, path: Path, gid_column: str, id_column: str) -> int:
        if not path.exists() or path.stat().st_size == 0:
            return 0
        max_entity_id = 0
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            batch: list[tuple[str, str, int, int, str, int]] = []
            for ordinal, row in enumerate(reader, start=1):
                gid = (row.get(gid_column) or "").strip()
                entity_id = _integer(row.get(id_column))
                max_entity_id = max(max_entity_id, entity_id)
                storage_key = f"gid:{gid}" if gid else f"existing-blank:{ordinal}"
                batch.append((storage_key, gid, entity_id, ordinal, _json_row(row), 0))
                if len(batch) >= CSV_TRANSACTION_SIZE:
                    self._insert_import_batch(table, batch)
                    batch.clear()
            if batch:
                self._insert_import_batch(table, batch)
        return max_entity_id

    def _insert_import_batch(self, table: str, batch: Sequence[tuple]) -> None:
        self.connection.executemany(
            f"INSERT OR IGNORE INTO {table} "
            "(storage_key, gid, entity_id, ordinal, payload, is_new) VALUES (?, ?, ?, ?, ?, ?)",
            batch,
        )
        self.connection.commit()

    def _set_metadata(self, key: str, value: object) -> None:
        self.connection.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value, ensure_ascii=False)),
        )

    def _get_metadata(self, key: str):
        row = self.connection.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def _max_id(self, table: str) -> int:
        value = self.connection.execute(f"SELECT COALESCE(MAX(entity_id), 0) FROM {table}").fetchone()[0]
        return _integer(value)

    def _next_id(self, metadata_key: str) -> int:
        value = _integer(self._get_metadata(metadata_key))
        self._set_metadata(metadata_key, value + 1)
        return value

    def begin_address(self) -> None:
        if self._address_transaction:
            raise RuntimeError("address transaction is already active")
        self.connection.execute("BEGIN IMMEDIATE")
        self._address_transaction = True

    def commit_address(self) -> None:
        if self._address_transaction:
            self.connection.commit()
            self._address_transaction = False

    def rollback_address(self) -> None:
        if self._address_transaction:
            self.connection.rollback()
            self._address_transaction = False

    def get_facility_id(self, gid: str) -> int | None:
        row = self.connection.execute(
            "SELECT entity_id FROM facilities WHERE gid = ?", (gid,)
        ).fetchone()
        return _integer(row[0]) if row else None

    def add_facility(self, row: Mapping[str, object]) -> tuple[int, bool]:
        gid = str(row.get("施設GID") or "").strip()
        if not gid:
            raise ValueError("新規施設の施設GIDが空です")
        existing_id = self.get_facility_id(gid)
        if existing_id is not None:
            return existing_id, False
        entity_id = self._next_id("next_facility_id")
        normalized = {field: row.get(field, "") for field in self.facility_fields}
        normalized["施設ID"] = entity_id
        ordinal = self.connection.execute("SELECT COALESCE(MAX(ordinal), 0) + 1 FROM facilities").fetchone()[0]
        self.connection.execute(
            "INSERT INTO facilities(storage_key, gid, entity_id, ordinal, payload, is_new) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            (f"gid:{gid}", gid, entity_id, ordinal, _json_row(normalized)),
        )
        return entity_id, True

    def add_review(self, row: Mapping[str, object]) -> tuple[int | None, bool]:
        gid = str(row.get("レビューGID") or "").strip()
        if not gid:
            return None, False
        existing = self.connection.execute(
            "SELECT entity_id FROM reviews WHERE gid = ?", (gid,)
        ).fetchone()
        if existing:
            return _integer(existing[0]), False
        entity_id = self._next_id("next_review_id")
        normalized = {field: row.get(field, "") for field in self.review_fields}
        normalized["レビューID"] = entity_id
        ordinal = self.connection.execute("SELECT COALESCE(MAX(ordinal), 0) + 1 FROM reviews").fetchone()[0]
        self.connection.execute(
            "INSERT INTO reviews(storage_key, gid, entity_id, ordinal, payload, is_new) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            (f"gid:{gid}", gid, entity_id, ordinal, _json_row(normalized)),
        )
        return entity_id, True

    def _iter_rows(self, table: str, *, only_new: bool = False) -> Iterator[dict[str, str]]:
        where = "WHERE is_new = 1" if only_new else ""
        cursor = self.connection.execute(
            f"SELECT payload, entity_id FROM {table} {where} ORDER BY ordinal"
        )
        id_column = "施設ID" if table == "facilities" else "レビューID"
        for payload, entity_id in cursor:
            row = json.loads(payload)
            if only_new:
                row[id_column] = str(entity_id)
            yield row

    @staticmethod
    def _atomic_write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                batch: list[Mapping[str, object]] = []
                for row in rows:
                    batch.append(row)
                    if len(batch) >= CSV_TRANSACTION_SIZE:
                        writer.writerows(batch)
                        batch.clear()
                if batch:
                    writer.writerows(batch)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        except BaseException:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise

    def export(
        self,
        facility_file: os.PathLike[str] | str,
        review_file: os.PathLike[str] | str,
        update_facility_file: os.PathLike[str] | str,
        update_review_file: os.PathLike[str] | str,
    ) -> None:
        self.connection.commit()
        self._atomic_write_csv(Path(facility_file), self.facility_fields, self._iter_rows("facilities"))
        self._atomic_write_csv(Path(review_file), self.review_fields, self._iter_rows("reviews"))
        self._atomic_write_csv(
            Path(update_facility_file), self.facility_fields, self._iter_rows("facilities", only_new=True)
        )
        self._atomic_write_csv(
            Path(update_review_file), self.review_fields, self._iter_rows("reviews", only_new=True)
        )

    def counts(self) -> dict[str, int]:
        result = {}
        for table in ("facilities", "reviews"):
            result[table] = self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            result[f"new_{table}"] = self.connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE is_new = 1"
            ).fetchone()[0]
        return result

    def close(self, *, remove_database: bool = False) -> None:
        self.rollback_address()
        self.connection.close()
        if remove_database:
            for suffix in ("", "-wal", "-shm"):
                try:
                    Path(f"{self.database_path}{suffix}").unlink()
                except FileNotFoundError:
                    pass

    def __enter__(self) -> "PlacesCsvStore":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
