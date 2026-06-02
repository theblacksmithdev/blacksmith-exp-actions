from __future__ import annotations

import pytest

from blacksmith.actions.reviewer.findings import Finding, FindingsResponse
from blacksmith.actions.reviewer.severity import Severity


class TestSeverity:
    def test_ordering(self) -> None:
        assert Severity.LOW < Severity.MEDIUM < Severity.HIGH < Severity.CRITICAL

    def test_parse_normalizes_case(self) -> None:
        assert Severity.parse("critical") is Severity.CRITICAL
        assert Severity.parse(" High ") is Severity.HIGH

    def test_parse_rejects_unknown(self) -> None:
        with pytest.raises(ValueError):
            Severity.parse("bogus")


class TestFindingModel:
    def test_accepts_string_severity(self) -> None:
        finding = Finding(file="a.py", line=1, severity="high", title="t", body="b")
        assert finding.severity is Severity.HIGH

    def test_accepts_int_severity(self) -> None:
        finding = Finding(file="a.py", line=1, severity=3, title="t", body="b")
        assert finding.severity is Severity.CRITICAL

    def test_rejects_invalid_severity_string(self) -> None:
        with pytest.raises(ValueError):
            Finding(file="a.py", line=1, severity="bogus", title="t", body="b")


class TestFindingsResponse:
    def test_round_trip(self) -> None:
        response = FindingsResponse.model_validate({
            "findings": [
                {"file": "a.py", "line": 1, "severity": "low", "title": "t", "body": "b"},
                {"file": "b.py", "line": 2, "severity": "critical", "title": "t", "body": "b"},
            ]
        })
        assert len(response.findings) == 2
        assert response.findings[1].severity is Severity.CRITICAL
