from __future__ import annotations

import csv
import os
import re
from typing import Optional

from models import CSVImportResult, ClientTrack


class CSVImportError(RuntimeError):
    pass


class CSVImportService:
    TITLE_HEADERS = {"title", "track", "song", "song title", "track title", "name"}
    ARTIST_HEADERS = {"artist", "artist name", "performer", "artists", "by"}
    GENRE_HEADERS = {"genre", "music genre"}

    @staticmethod
    def _normalize_header(value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip().lower())

    def _find_header(self, headers: list[str], candidates: set[str]) -> Optional[str]:
        for header in headers:
            if self._normalize_header(header) in candidates:
                return header
        return None

    @staticmethod
    def _dedupe_key(artist: str, title: str) -> tuple[str, str]:
        norm_artist = re.sub(r"\s+", " ", (artist or "").strip().lower())
        norm_title = re.sub(r"\s+", " ", (title or "").strip().lower())
        return norm_artist, norm_title

    def import_file(self, path: str) -> CSVImportResult:
        if not path:
            raise CSVImportError("Please select a CSV file first.")

        if not os.path.exists(path):
            raise CSVImportError(f"CSV file not found:\n\n{path}")

        try:
            with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as handle:
                sample = handle.read(4096)
                handle.seek(0)

                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(handle, dialect=dialect)

                if not reader.fieldnames:
                    raise CSVImportError("The CSV appears to be empty or missing a header row.")

                headers = [header or "" for header in reader.fieldnames]
                title_key = self._find_header(headers, self.TITLE_HEADERS)
                artist_key = self._find_header(headers, self.ARTIST_HEADERS)
                genre_key = self._find_header(headers, self.GENRE_HEADERS)

                if not title_key:
                    raise CSVImportError(
                        "Could not find a track title column.\n\n"
                        "Supported headers include: Title, Track, Song."
                    )

                rows: list[ClientTrack] = []
                seen: set[tuple[str, str]] = set()
                duplicate_count = 0
                skipped_empty_count = 0
                malformed_rows: list[int] = []

                for line_number, row in enumerate(reader, start=2):
                    try:
                        title = (row.get(title_key) or "").strip()
                        artist = (row.get(artist_key) or "").strip() if artist_key else ""
                        genre = (row.get(genre_key) or "").strip() if genre_key else ""
                    except Exception:
                        malformed_rows.append(line_number)
                        continue

                    if not title and not artist:
                        skipped_empty_count += 1
                        continue

                    if not title:
                        malformed_rows.append(line_number)
                        continue

                    key = self._dedupe_key(artist, title)
                    is_duplicate = key in seen
                    if is_duplicate:
                        duplicate_count += 1
                    else:
                        seen.add(key)

                    rows.append(
                        ClientTrack(
                            artist=artist,
                            title=title,
                            source="csv",
                            genre=genre,
                            notes="Duplicate row" if is_duplicate else "",
                            is_duplicate=is_duplicate,
                        )
                    )

                if malformed_rows:
                    preview = ", ".join(str(item) for item in malformed_rows[:10])
                    suffix = "" if len(malformed_rows) <= 10 else f" and {len(malformed_rows) - 10} more"
                    raise CSVImportError(
                        "The CSV contains malformed rows.\n\n"
                        f"Problem rows: {preview}{suffix}\n"
                        "Please make sure each row includes a valid title value."
                    )

                if not rows:
                    raise CSVImportError("No importable tracks were found in the CSV.")

                return CSVImportResult(
                    rows=rows,
                    duplicate_count=duplicate_count,
                    skipped_empty_count=skipped_empty_count,
                )

        except OSError as exc:
            raise CSVImportError(f"Could not read CSV file.\n\n{exc}") from exc
