from __future__ import annotations

import pytest

from blacksmith.actions.reviewer.findings import Finding, FindingsResponse, Reference
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


class TestReferences:
    def test_finding_defaults_to_no_references(self) -> None:
        finding = Finding(file="a.py", line=1, severity="low", title="t", body="b")
        assert finding.references == []

    def test_accepts_well_formed_reference(self) -> None:
        finding = Finding(
            file="a.py",
            line=1,
            severity="high",
            title="t",
            body="b",
            references=[
                {"url": "https://owasp.org/cheatsheet", "why": "OWASP on input validation"},
            ],
        )
        assert len(finding.references) == 1
        assert isinstance(finding.references[0], Reference)
        assert finding.references[0].why == "OWASP on input validation"

    def test_reference_rejects_non_http_url_directly(self) -> None:
        with pytest.raises(ValueError):
            Reference(url="not-a-url", why="x")

    def test_finding_silently_drops_invalid_references(self) -> None:
        finding = Finding(
            file="a.py",
            line=1,
            severity="high",
            title="t",
            body="b",
            references=[
                {"url": "https://owasp.org/x", "why": "good"},
                {"url": "javascript:alert(1)", "why": "bad scheme"},
                {"url": "garbage", "why": "no host"},
            ],
        )
        assert len(finding.references) == 1
        assert finding.references[0].why == "good"

    def test_schema_does_not_use_uri_format(self) -> None:
        """GitHub Models' structured-output schema rejects format: 'uri'.
        pydantic's HttpUrl emits that, plain str does not."""
        from blacksmith.actions.reviewer.findings import FindingsResponse

        schema_text = str(FindingsResponse.model_json_schema())
        assert "'uri'" not in schema_text
        assert '"uri"' not in schema_text


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
