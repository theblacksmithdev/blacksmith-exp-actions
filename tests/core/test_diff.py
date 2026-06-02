from __future__ import annotations

from blacksmith.core.diff import DiffParser

FIXTURE_PATCH = """@@ -1,3 +1,5 @@
 line1
-line2_old
+line2_new
+line3_new
 line4
@@ -10,2 +12,3 @@
 line10
+line11_new
 line12
"""


class TestDiffParser:
    def setup_method(self) -> None:
        self.parser = DiffParser()

    def test_extracts_added_line_numbers_across_hunks(self) -> None:
        assert self.parser.anchorable_lines(FIXTURE_PATCH) == {2, 3, 13}

    def test_empty_patch(self) -> None:
        assert self.parser.anchorable_lines("") == set()
        assert self.parser.anchorable_lines(None) == set()

    def test_ignores_no_newline_marker(self) -> None:
        patch = (
            "@@ -1,1 +1,2 @@\n"
            " keep\n"
            "+added\n"
            "\\ No newline at end of file\n"
        )
        assert self.parser.anchorable_lines(patch) == {2}

    def test_only_added_lines_in_anchor_set(self) -> None:
        patch = "@@ -1,2 +1,2 @@\n-removed\n+added\n context\n"
        assert self.parser.anchorable_lines(patch) == {1}
