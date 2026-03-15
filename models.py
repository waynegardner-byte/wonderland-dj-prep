from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class ClientTrack:
    artist: str = ""
    title: str = ""
    source: str = ""
    genre: str = ""
    notes: str = ""
    alt_artist: str = ""
    alt_title: str = ""
    is_duplicate: bool = False


@dataclass(slots=True)
class LibraryTrack:
    track_id: str
    artist: str
    title: str
    album: str = ""
    genre: str = ""
    path: str = ""

    @property
    def label(self) -> str:
        parts = [self.artist.strip(), self.title.strip()]
        return " — ".join(part for part in parts if part)


@dataclass(slots=True)
class MatchCandidate:
    track: LibraryTrack
    score: int


@dataclass(slots=True)
class MatchRow:
    client: ClientTrack
    match: Optional[LibraryTrack] = None
    score: int = 0
    candidates: list[MatchCandidate] = field(default_factory=list)
    excluded: bool = False
    located_file: str = ""

    @property
    def status_text(self) -> str:
        if self.match is not None:
            return "Matched"
        if self.located_file:
            return "Located"
        if self.client.is_duplicate:
            return "Duplicate"
        return "Imported"


@dataclass(slots=True)
class CSVImportResult:
    rows: list[ClientTrack]
    duplicate_count: int = 0
    skipped_empty_count: int = 0
