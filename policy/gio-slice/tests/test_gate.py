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


def test_every_fixture_option_classified_before_rules():
    for n in (1, 2, 3):
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


def test_fixture_1_option_a_deny_continuation(fixture_1):
    result = evaluate(fixture_1, option_by_id(fixture_1, "A"))
    assert result["decision"] == "DENY"
    assert result["change_type"] == "Deviation"
    assert result["required_approvers"] == []
    assert "21 CFR 211.100(b)" in result["regulatory_basis"]


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
    for n in (1, 2, 3):
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


def test_fixture_2_confidence_is_not_high(fixture_2):
    assert fixture_2["confidence"] in ("LOW", "MEDIUM")
    assert fixture_2["confidence"] != "HIGH"
    result = evaluate(fixture_2, option_by_id(fixture_2, "A"))
    assert result["decision"] == "DENY"
