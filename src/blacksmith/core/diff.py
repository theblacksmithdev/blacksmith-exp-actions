from __future__ import annotations

import re


class DiffParser:
    _HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    def anchorable_lines(self, patch: str | None) -> set[int]:
        if not patch:
            return set()
        anchored: set[int] = set()
        new_line = 0
        for line in patch.splitlines():
            if line.startswith("@@"):
                match = self._HUNK_RE.match(line)
                if match:
                    new_line = int(match.group(1))
                continue
            if line.startswith(("+++", "---")):
                continue
            if not line:
                new_line += 1
                continue
            head = line[0]
            if head == "+":
                anchored.add(new_line)
                new_line += 1
            elif head in ("-", "\\"):
                continue
            else:
                new_line += 1
        return anchored
