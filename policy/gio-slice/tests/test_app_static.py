from app import (
    approval_lane_html,
    audit_html,
    gate_lane_html,
    header_html,
    load_fixture,
    option,
    options_lane_html,
    resolved_html,
    status_html,
    tablets_at_risk,
    dollars_at_risk,
)
from approval import new_record, resolve, sign_qa, sign_supervisor
from policy_gate import evaluate


def _page():
    incident = load_fixture(1)
    gate = evaluate(incident, option(incident, "C"))
    return (
        header_html(incident)
        + status_html()
        + gate_lane_html(incident, gate)
        + options_lane_html(incident)
        + approval_lane_html(gate)
    ).lower()


def test_fixture_1_impact_math():
    incident = load_fixture(1)
    assert tablets_at_risk(incident) == 720000
    assert dollars_at_risk(incident) == 25200


def test_static_page_carries_trunk_strings():
    page = _page()
    assert "tp-04-0912" in page
    assert "simulated plant data" in page
    assert "main-drive bearing degradation" in page
    assert "720,000" in page
    assert "$25,200" in page
    assert "tablets at risk" in page
    assert "rollback by 18:00" in page
    assert "human_approval" in page
    assert "intervention approved" in page or "approve the intervention" in page
    assert "batch disposition" in page
    assert "incident" in page


def test_static_page_forbidden_words():
    page = _page()
    assert "compliant" not in page
    assert "anomaly" not in page
    assert "authorized" not in page
    assert "classification" not in page


def test_audit_html_shows_five_fields_after_both_signatures():
    incident = load_fixture(1)
    gate = evaluate(incident, option(incident, "C"))
    rec = new_record(incident, option(incident, "C"), gate)
    sign_supervisor(rec)
    sign_qa(rec)
    resolve(rec)
    html = audit_html(rec).lower()
    for field in ("who", "what", "when", "why", "before"):
        assert f">{field}<" in html or f" {field}</span>" in html or f">{field}</span>" in html
    assert "simulated" in html
    assert "a. rivera" in html
    assert "k. chen" in html
    assert "compliant" not in html
    resolved = resolved_html(incident).lower()
    assert "remains flagged for qa disposition" in resolved
    assert "incident resolved" in status_html(rec).lower()
