from __future__ import annotations

from unidiff import PatchSet


class DiffParser:
    _HEADER = "--- a/_\n+++ b/_\n"

    def anchorable_lines(self, patch: str | None) -> set[int]:
        if not patch:
            return set()
        patch_set = PatchSet.from_string(self._HEADER + patch)
        if not patch_set:
            return set()
        return {
            line.target_line_no
            for hunk in patch_set[0]
            for line in hunk
            if line.is_added and line.target_line_no is not None
        }
