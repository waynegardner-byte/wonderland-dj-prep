from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from models import LibraryTrack


class RekordboxReaderError(RuntimeError):
    pass


class RekordboxLibraryReader:
    DEFAULT_RB_PATHS = [
        Path.home() / "Library/Pioneer/rekordbox/master.db",
        Path.home() / "Library/Pioneer/rekordbox6/master.db",
        Path.home() / "Library/Pioneer/rekordbox7/master.db",
        Path.home() / "Library/Containers/com.pioneerdj.rekordbox/Data/Library/Pioneer/rekordbox/master.db",
        Path.home() / "Library/Containers/com.pioneerdj.rekordbox/Data/Library/Pioneer/rekordbox6/master.db",
        Path.home() / "Library/Containers/com.pioneerdj.rekordbox/Data/Library/Pioneer/rekordbox7/master.db",
    ]

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path

    def locate_database(self) -> str:
        if self.db_path:
            if os.path.exists(self.db_path):
                return self.db_path
            raise RekordboxReaderError(f"Configured Rekordbox database not found:\n\n{self.db_path}")

        for path in self.DEFAULT_RB_PATHS:
            if path.exists():
                return str(path)

        raise RekordboxReaderError("Could not find the Rekordbox master.db file.")

    def read_tracks(self) -> list[LibraryTrack]:
        db_path = self.locate_database()

        try:
            connection = sqlite3.connect(db_path)
        except sqlite3.Error as exc:
            raise RekordboxReaderError(f"Could not open the Rekordbox database.\n\n{exc}") from exc

        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT ID, ArtistName, Title, AlbumName, Genre, FolderPath
                FROM djmdContent
                """
            )

            tracks: list[LibraryTrack] = []
            for row in cursor.fetchall():
                tracks.append(
                    LibraryTrack(
                        track_id=str(row[0] or ""),
                        artist=(row[1] or "").strip(),
                        title=(row[2] or "").strip(),
                        album=(row[3] or "").strip(),
                        genre=(row[4] or "").strip(),
                        path=(row[5] or "").replace("file://localhost", ""),
                    )
                )
            return tracks
        except sqlite3.Error as exc:
            raise RekordboxReaderError(f"Could not query the Rekordbox database.\n\n{exc}") from exc
        finally:
            connection.close()
