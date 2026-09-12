import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from approval import (
    AUDIT_FIELDS,
    MEANING_QA,
    MEANING_SUPERVISOR,
    STATE_BOTH_SIGNED,
    STATE_PRESENTED,
    STATE_RESOLVED,
    STATE_SUPERVISOR_SIGNED,
    append_audit,
    is_resolved,
    new_record,
    resolve,
    sign_qa,
    sign_supervisor,
)
from policy_gate import ROLE_QA, ROLE_SUPERVISOR, evaluate

ROOT = Path(__file__).resolve().parents[1]
CLOCK = datetime(2026, 9, 12, 14, 22, tzinfo=timezone.utc)


def fixture_1():
    return json.loads((ROOT / "data" / "fixture_1.json").read_text())


def option_c(incident):
    return next(opt for opt in incident["options"] if opt["id"] == "C")


def record():
    incident = fixture_1()
    option = option_c(incident)
    return new_record(incident, option, evaluate(incident, option))


def test_new_record_starts_presented_with_empty_log():
    rec = record()
    assert rec["state"] == STATE_PRESENTED
    assert rec["signatures"] == []
    assert rec["audit"] == []
    assert rec["data_source"] == "simulated"
    assert rec["required_approvers"] == [ROLE_SUPERVISOR, ROLE_QA]


def test_supervisor_alone_does_not_resolve():
    rec = record()
    sign_supervisor(rec, clock=CLOCK)
    assert rec["state"] == STATE_SUPERVISOR_SIGNED
    assert is_resolved(rec) is False
    assert [sig["role"] for sig in rec["signatures"]] == [ROLE_SUPERVISOR]
    assert rec["signatures"][0]["meaning"] == MEANING_SUPERVISOR
    assert rec["signatures"][0]["name"] == "A. Rivera"
    assert rec["signatures"][0]["timestamp"] == CLOCK.isoformat()


def test_qa_cannot_sign_first():
    rec = record()
    sign_qa(rec, clock=CLOCK)
    assert rec["state"] == STATE_PRESENTED
    assert rec["signatures"] == []
    assert rec["audit"] == []


def test_both_signatures_then_resolve():
    rec = record()
    sign_supervisor(rec, clock=CLOCK)
    sign_qa(rec, clock=CLOCK)
    assert rec["state"] == STATE_BOTH_SIGNED
    assert [sig["role"] for sig in rec["signatures"]] == [ROLE_SUPERVISOR, ROLE_QA]
    assert rec["signatures"][0]["meaning"] == MEANING_SUPERVISOR
    assert rec["signatures"][1]["meaning"] == MEANING_QA
    assert rec["signatures"][0]["meaning"] != rec["signatures"][1]["meaning"]
    resolve(rec, clock=CLOCK)
    assert rec["state"] == STATE_RESOLVED
    assert is_resolved(rec) is True
    assert rec["quality_flag"] is True


def test_resolve_blocked_until_both_sign():
    rec = record()
    sign_supervisor(rec, clock=CLOCK)
    resolve(rec, clock=CLOCK)
    assert rec["state"] == STATE_SUPERVISOR_SIGNED
    assert is_resolved(rec) is False


def test_signature_meanings_are_distinct():
    assert MEANING_SUPERVISOR == "intervention approved"
    assert MEANING_QA == "batch disposition reviewed"
    assert MEANING_SUPERVISOR != MEANING_QA
    rec = record()
    sign_supervisor(rec, clock=CLOCK)
    sign_qa(rec, clock=CLOCK)
    meanings = [sig["meaning"] for sig in rec["signatures"]]
    assert meanings == [MEANING_SUPERVISOR, MEANING_QA]
    for sig in rec["signatures"]:
        assert "name" in sig and sig["name"]
        assert "timestamp" in sig and sig["timestamp"]
        assert "meaning" in sig and sig["meaning"]


def test_audit_has_five_fields_and_simulated_label():
    rec = record()
    sign_supervisor(rec, clock=CLOCK)
    sign_qa(rec, clock=CLOCK)
    resolve(rec, clock=CLOCK)
    assert len(rec["audit"]) == 3
    for entry in rec["audit"]:
        for field in AUDIT_FIELDS:
            assert field in entry
            assert entry[field] not in (None, "")
        assert entry["data_source"] == "simulated"
        assert "compliant" not in json.dumps(entry).lower()
    first = rec["audit"][0]
    assert first["who"] == "A. Rivera"
    assert first["before"]["state"] == STATE_PRESENTED
    assert rec["audit"][1]["before"]["state"] == STATE_SUPERVISOR_SIGNED
    assert rec["audit"][2]["before"]["state"] == STATE_BOTH_SIGNED
    assert rec["audit"][2]["who"] == "system"


def test_audit_is_append_only():
    rec = record()
    sign_supervisor(rec, clock=CLOCK)
    snapshot = copy.deepcopy(rec["audit"])
    sign_qa(rec, clock=CLOCK)
    assert rec["audit"][:1] == snapshot
    assert len(rec["audit"]) == 2


def test_second_supervisor_sign_is_noop():
    rec = record()
    sign_supervisor(rec, clock=CLOCK)
    sign_supervisor(rec, clock=CLOCK)
    assert len(rec["signatures"]) == 1
    assert len(rec["audit"]) == 1


def test_append_audit_timestamp_is_system_generated():
    rec = record()
    entry = append_audit(rec, who="A. Rivera", what="test", why="unit", before={"state": "Presented"}, clock=CLOCK)
    assert entry["when"] == CLOCK.isoformat()
    assert rec["audit"][-1]["when"] == CLOCK.isoformat()
