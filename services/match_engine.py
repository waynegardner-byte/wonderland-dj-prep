from __future__ import annotations

import re

from models import ClientTrack, LibraryTrack, MatchCandidate, MatchRow


class MatchEngine:
    def __init__(self, library_tracks: list[LibraryTrack], threshold: int = 78) -> None:
        self.threshold = threshold
        self.index: list[tuple[LibraryTrack, str]] = []

        for track in library_tracks:
            combo = self._normalize(
                f"{self._main_artist(track.artist)} {self._strip_version(track.title)}"
            )
            self.index.append((track, combo))

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.lower()
        value = re.sub(r"\(feat\..*?\)", "", value)
        value = re.sub(r"\[.*?\]", "", value)
        value = re.sub(r"[^\w\s]", " ", value)
        return " ".join(value.split())

    @staticmethod
    def _main_artist(artist: str) -> str:
        parts = re.split(r"\s+(?:feat(?:uring)?\.?|ft\.?|with|x)\s+", artist, maxsplit=1, flags=re.I)
        return parts[0].strip()

    @staticmethod
    def _strip_version(title: str) -> str:
        return re.sub(
            r"\s*[\(\[][^\(\]]*\b(remix|edit|mix|version|remaster|live|acoustic)\b[^\)\]]*[\)\]]",
            "",
            title,
            flags=re.I,
        ).strip()

    @staticmethod
    def _token_set_ratio(lhs: str, rhs: str) -> int:
        lhs_tokens = set(lhs.split())
        rhs_tokens = set(rhs.split())

        if not lhs_tokens or not rhs_tokens:
            return 0

        intersection = len(lhs_tokens & rhs_tokens)
        union = len(lhs_tokens | rhs_tokens)

        if union == 0:
            return 0

        return int((intersection / union) * 100)

    def top_matches(self, client: ClientTrack, limit: int = 5) -> list[MatchCandidate]:
        query = self._normalize(
            f"{self._main_artist(client.artist)} {self._strip_version(client.title)}"
        )

        if not query:
            return []

        scored: list[MatchCandidate] = []
        for track, combo in self.index:
            score = self._token_set_ratio(query, combo)
            if score > 0:
                scored.append(MatchCandidate(track=track, score=score))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def match(self, client: ClientTrack) -> MatchRow:
        candidates = self.top_matches(client)
        if candidates and candidates[0].score >= self.threshold:
            return MatchRow(
                client=client,
                match=candidates[0].track,
                score=candidates[0].score,
                candidates=candidates,
            )

        return MatchRow(
            client=client,
            match=None,
            score=candidates[0].score if candidates else 0,
            candidates=candidates,
        )
