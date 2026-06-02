from __future__ import annotations

from blacksmith.actions.reviewer.findings import Finding, FindingsParser
from blacksmith.actions.reviewer.severity import Severity


class TestFindingsParser:
    def setup_method(self) -> None:
        self.parser = FindingsParser()

    def test_parses_plain_json_array(self) -> None:
        raw = '[{"file":"a.py","line":3,"severity":"high","title":"t","body":"b"}]'
        findings = self.parser.parse(raw)
        assert len(findings) == 1
        assert findings[0].file == "a.py"
        assert findings[0].line == 3
        assert findings[0].severity is Severity.HIGH

    def test_strips_json_code_fence(self) -> None:
        raw = '```json\n[{"file":"a.py","line":1,"severity":"low","title":"t","body":"b"}]\n```'
        findings = self.parser.parse(raw)
        assert len(findings) == 1
        assert findings[0].severity is Severity.LOW

    def test_returns_empty_on_garbage(self) -> None:
        assert self.parser.parse("not json") == []
        assert self.parser.parse("") == []

    def test_skips_invalid_items_keeps_valid(self) -> None:
        raw = (
            '[{"file":"a.py","line":1,"severity":"bogus","title":"t","body":"b"},'
            '{"file":"b.py","line":2,"severity":"medium","title":"t","body":"b"}]'
        )
        findings = self.parser.parse(raw)
        assert len(findings) == 1
        assert findings[0].file == "b.py"


class TestSeverity:
    def test_ordering(self) -> None:
        assert Severity.LOW < Severity.MEDIUM < Severity.HIGH < Severity.CRITICAL

    def test_parse_normalizes_case(self) -> None:
        assert Severity.parse("critical") is Severity.CRITICAL
        assert Severity.parse(" High ") is Severity.HIGH

    def test_parse_rejects_unknown(self) -> None:
        import pytest
        with pytest.raises(ValueError):
            Severity.parse("bogus")


class TestFindingModel:
    def test_accepts_string_severity(self) -> None:
        finding = Finding(file="a.py", line=1, severity="high", title="t", body="b")
        assert finding.severity is Severity.HIGH

    def test_accepts_int_severity(self) -> None:
        finding = Finding(file="a.py", line=1, severity=3, title="t", body="b")
        assert finding.severity is Severity.CRITICAL
