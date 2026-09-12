import copy
import json
from pathlib import Path

import pytest

from policy_gate import (
    CHANGE_TYPES,
    ROLE_QA,
    ROLE_SUPERVISOR,
    classify,
    evaluate,
    limit_violations,
    signatures_satisfy,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_fixture(n):
    return json.loads((DATA / f"fixture_{n}.json").read_text())


def option_by_id(incident, option_id):
    return next(opt for opt in incident["options"] if opt["id"] == option_id)


def dump_strings(result):
    return json.dumps(result).lower()


@pytest.fixture
def fixture_1():
    return load_fixture(1)


@pytest.fixture
def fixture_2():
    return load_fixture(2)


@pytest.fixture
def fixture_3():
    return load_fixture(3)


@pytest.fixture
def fixture_4():
    return load_fixture(4)


@pytest.fixture
def fixture_5():
    return load_fixture(5)


def test_every_fixture_option_classified_before_rules():
    for n in (1, 2, 3, 4, 5):
        incident = load_fixture(n)
        for option in incident["options"]:
            change_type = classify(option)
            assert change_type in CHANGE_TYPES
            result = evaluate(incident, option)
            assert result["change_type"] == change_type
            assert "likely_cause" not in result


def test_fixture_1_option_c_human_approval_both_roles(fixture_1):
    result = evaluate(fixture_1, option_by_id(fixture_1, "C"))
    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["change_type"] == "Repair"
    assert result["required_approvers"] == [ROLE_SUPERVISOR, ROLE_QA]
    assert result["quality_flag"] is True
    assert "GAMP 5 App O6 p.307" in result["regulatory_basis"]
    assert "21 CFR 211.22" in result["regulatory_basis"]


def test_fixture_1_option_a_requires_signed_deviation(fixture_1):
    # Continuing outside the limit is never autonomous (rule 1), but a human
    # choosing it is a deviation that must be "recorded and justified"
    # (211.100(b)) — a signed act, not a dead end. Quality unit signs too
    # since a CQA-linked parameter has moved (rule 5), same as Repair.
    result = evaluate(fixture_1, option_by_id(fixture_1, "A"))
    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["change_type"] == "Deviation"
    assert result["required_approvers"] == [ROLE_SUPERVISOR, ROLE_QA]
    assert result["quality_flag"] is True
    assert "21 CFR 211.100(b)" in result["regulatory_basis"]
    assert "21 CFR 211.22" in result["regulatory_basis"]


def test_fixture_1_option_b_human_approval_with_rollback(fixture_1):
    result = evaluate(fixture_1, option_by_id(fixture_1, "B"))
    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["change_type"] == "Temporary Change"
    assert result["required_approvers"] == [ROLE_SUPERVISOR, ROLE_QA]
    assert "21 CFR 211.100(a)" in result["regulatory_basis"]


def test_temporary_change_missing_rollback_is_deny(fixture_1):
    option = copy.deepcopy(option_by_id(fixture_1, "B"))
    del option["rollback_review_by"]
    result = evaluate(fixture_1, option)
    assert result["decision"] == "DENY"
    assert result["change_type"] == "Temporary Change"
    assert result["required_approvers"] == []


def test_temporary_change_empty_rollback_is_deny(fixture_1):
    option = copy.deepcopy(option_by_id(fixture_1, "B"))
    option["rollback_review_by"] = ""
    result = evaluate(fixture_1, option)
    assert result["decision"] == "DENY"


def test_proposed_rpm_outside_qualified_range_is_deny(fixture_1):
    option = copy.deepcopy(option_by_id(fixture_1, "B"))
    option["proposed_turret_speed_rpm"] = 20
    result = evaluate(fixture_1, option)
    assert result["decision"] == "DENY"
    assert "EU Annex 11 ¶10" in result["regulatory_basis"]
    assert "21 CFR 211.68(b)" in result["regulatory_basis"]


def test_one_signature_does_not_satisfy_and_join(fixture_1):
    result = evaluate(fixture_1, option_by_id(fixture_1, "C"))
    only_supervisor = [{"role": ROLE_SUPERVISOR, "name": "A. Rivera", "meaning": "intervention approved"}]
    only_qa = [{"role": ROLE_QA, "name": "K. Chen", "meaning": "batch disposition reviewed"}]
    both = only_supervisor + only_qa
    assert signatures_satisfy(result["required_approvers"], only_supervisor) is False
    assert signatures_satisfy(result["required_approvers"], only_qa) is False
    assert signatures_satisfy(result["required_approvers"], both) is True


def test_fixture_3_does_not_invent_likely_cause(fixture_3):
    assert fixture_3["likely_cause"] is None
    assert fixture_3["retrieved"] == []
    original = copy.deepcopy(fixture_3)
    for option in fixture_3["options"]:
        result = evaluate(fixture_3, option)
        assert "likely_cause" not in result
        assert result.get("likely_cause") in (None, "")
    assert fixture_3 == original


def test_return_strings_never_say_compliant():
    for n in (1, 2, 3, 4, 5):
        incident = load_fixture(n)
        for option in incident["options"]:
            result = evaluate(incident, option)
            assert "compliant" not in dump_strings(result)


def test_unknown_change_type_is_deny(fixture_1):
    result = evaluate(fixture_1, {"id": "X", "gamp_change_type": "Emergency Change"})
    assert result["decision"] == "DENY"
    assert result["change_type"] is None


def test_diagnostic_standard_routine_is_allow(fixture_1):
    option = {
        "id": "D",
        "description": "Read vibration trend",
        "gamp_change_type": "Standard/Routine",
    }
    result = evaluate(fixture_1, option)
    assert result["decision"] == "ALLOW"
    assert result["change_type"] == "Standard/Routine"
    assert result["required_approvers"] == []


def test_ejection_force_outside_limit_is_a_violation():
    # sticking/picking's real signal (INC-003) — the gate had no idea this
    # parameter existed until fixture_5 needed it. A CQA parameter with no
    # violation check is a parameter the gate silently can't see.
    incident = {"ejection_force_kn": 1.95, "max_ejection_force_kn": 0.85}
    assert "ejection_force_kn" in limit_violations(incident)
    incident_ok = {"ejection_force_kn": 0.7, "max_ejection_force_kn": 0.85}
    assert "ejection_force_kn" not in limit_violations(incident_ok)


def test_tablet_thickness_deviation_is_a_violation():
    incident = {"tablet_thickness_mm": 4.6, "target_tablet_thickness_mm": 4.5, "tablet_thickness_tolerance_mm": 0.05}
    assert "tablet_thickness_mm" in limit_violations(incident)
    incident_ok = {"tablet_thickness_mm": 4.52, "target_tablet_thickness_mm": 4.5, "tablet_thickness_tolerance_mm": 0.05}
    assert "tablet_thickness_mm" not in limit_violations(incident_ok)


def test_fixture_4_real_feed_vibration_bearing_is_high_confidence(fixture_4):
    # Real telemetry/RAG pulled from the team's tools (Farhan/Ferdi), not a
    # hand-invented fixture — see docs/gio-gameday.md build order step 4.
    assert fixture_4["data_source"].startswith("real_feed:")
    assert fixture_4["confidence"] == "HIGH"
    result = evaluate(fixture_4, option_by_id(fixture_4, "C"))
    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["change_type"] == "Repair"
    assert result["required_approvers"] == [ROLE_SUPERVISOR, ROLE_QA]


def test_fixture_5_real_feed_sticking_picking_is_medium_confidence(fixture_5):
    # The scenario's own SOP says telemetry alone can't confirm sticking or
    # picking — confidence must reflect that, not just the raw signal count.
    assert fixture_5["data_source"].startswith("real_feed:")
    assert fixture_5["confidence"] == "MEDIUM"
    assert fixture_5["prior_similar_incidents"] == 0
    result = evaluate(fixture_5, option_by_id(fixture_5, "C"))
    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["required_approvers"] == [ROLE_SUPERVISOR, ROLE_QA]
    assert result["quality_flag"] is True


def test_fixture_2_confidence_is_not_high(fixture_2):
    assert fixture_2["confidence"] in ("LOW", "MEDIUM")
    assert fixture_2["confidence"] != "HIGH"
    # fixture_2's weight drift is itself a limit violation, so option A is
    # still a signed deviation here too — see test_fixture_1_option_a_*.
    result = evaluate(fixture_2, option_by_id(fixture_2, "A"))
    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["required_approvers"] == [ROLE_SUPERVISOR, ROLE_QA]
