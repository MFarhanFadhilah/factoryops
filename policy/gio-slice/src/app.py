import json
from pathlib import Path

import streamlit as st

from approval import (
    STATE_PRESENTED,
    STATE_SUPERVISOR_SIGNED,
    is_resolved,
    new_record,
    resolve,
    sign_qa,
    sign_supervisor,
)
from policy_gate import evaluate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

NAV = [
    ("Plant Floor", ["Overview"]),
    ("Line 1 — Encapsulation", ["CF-01", "CF-02", "CF-03", "CF-04"]),
    ("Line 2 — Coating", ["CT-01", "CT-02", "CT-03"]),
    ("Line 3 — Tablet Compression", ["TP-01", "TP-02", "TP-04", "TP-05", "TP-06", "TP-07", "TP-08"]),
]
LIVE_MACHINE = "TP-04"

CSS = """
<style>
.stApp { background: #f3f4f6; }
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e5e7eb; }
section[data-testid="stSidebar"] .stButton > button {
  background: none; border: none; border-left: 3px solid transparent;
  color: #374151; text-align: left; font-weight: 400; border-radius: 0;
  padding: 7px 16px 7px 13px; width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover { background: #f3f4f6; color: #374151; }
.sidenav-brand { font-size: 14px; font-weight: 700; letter-spacing: 0.05em;
  text-transform: uppercase; color: #00447C; padding: 4px 4px 12px; }
.sidenav-group { font-size: 12px; font-weight: 700; letter-spacing: 0.05em;
  text-transform: uppercase; color: #9ca3af; padding: 12px 4px 4px; }
.sidenav-active { font-size: 14px; font-weight: 700; color: #00447C;
  border-left: 3px solid #0076CE; background: #f3f4f6;
  padding: 7px 16px 7px 13px; margin: 0 -1rem; }
div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"] {
  background: #0076CE; color: #ffffff; border: none; font-weight: 600; border-radius: 4px;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"] {
  background: #f3f4f6; color: #9ca3af; border: 1px solid #e5e7eb; font-weight: 600; border-radius: 4px;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) {
  background: #ffffff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.incident-id { font-size: 16px; font-weight: 700; color: #00447C;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.sim-tag { font-size: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  color: #374151; background: #e5e7eb; border-radius: 4px; padding: 4px 8px; margin-left: 8px; }
.subline { font-size: 12px; color: #9ca3af; margin-top: 4px; margin-bottom: 12px; }
.status-banner { padding: 12px 20px; font-size: 16px; font-weight: 700; color: #d97706;
  background: rgba(217,119,6,0.12); border-radius: 4px; margin-bottom: 16px; }
.status-resolved { color: #059669; background: rgba(5,150,105,0.12); }
.lane { background: #ffffff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.lane-title { font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  color: #ffffff; background: #00447C; padding: 10px 18px; border-radius: 4px 4px 0 0; }
.lane-body { padding: 8px 18px 16px; }
.eyebrow { font-size: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  color: #374151; margin-top: 12px; }
.cause-headline { font-size: 18px; font-weight: 600; color: #00447C; }
.muted { color: #9ca3af; font-size: 13px; }
.evidence-row { display: flex; justify-content: space-between; padding: 7px 0; font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; border-top: 1px solid #f3f4f6; }
.delta-bad { color: #dc2626; font-weight: 700; }
.tile-wrap { display: flex; gap: 12px; }
.tile { flex: 1; background: #f3f4f6; border-radius: 4px; padding: 10px 14px; }
.tile-number { font-size: 24px; font-weight: 700; color: #00447C;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.tile-caption { font-size: 11px; color: #9ca3af; }
.assumption { font-size: 11px; color: #9ca3af; margin-top: 8px; }
.quality-flag { display: inline-block; background: #f3f4f6; border-radius: 4px; padding: 8px 12px;
  font-size: 12.5px; font-weight: 600; color: #374151; margin-top: 8px; }
.gate-decision { background: #f3f4f6; border-radius: 4px; padding: 12px 14px; }
.gate-decision-value { font-size: 14px; font-weight: 700; color: #00447C; }
.gate-decision-basis { font-size: 11.5px; color: #9ca3af;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.option-line { display: flex; justify-content: space-between; gap: 8px; background: #f3f4f6;
  border-radius: 4px; padding: 10px 12px; font-size: 13px; font-weight: 600; color: #00447C;
  margin-bottom: 8px; }
.option-card { border-left: 3px solid #0076CE; background: #eef6fb; border-radius: 4px; padding: 14px; }
.option-title { font-size: 14px; font-weight: 600; color: #00447C; }
.class-tag { font-size: 11px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
  border-radius: 4px; padding: 3px 7px; white-space: nowrap; }
.class-deviation { background: rgba(220,38,38,0.12); color: #dc2626; }
.class-temporary { background: rgba(217,119,6,0.12); color: #d97706; }
.class-repair { background: rgba(5,150,105,0.12); color: #059669; }
.rollback-inline { font-size: 11.5px; font-weight: 600; color: #d97706; margin-right: 6px; }
.recommended { font-size: 11.5px; font-weight: 700; color: #0076CE; }
.sig-block { background: #f3f4f6; border-radius: 4px; padding: 12px 14px; margin-top: 10px; }
.sig-role { font-size: 13.5px; font-weight: 700; color: #00447C; }
.sig-meaning { font-size: 11.5px; color: #9ca3af; }
.sig-confirmed { display: flex; align-items: center; gap: 6px; background: rgba(5,150,105,0.12);
  border-radius: 4px; padding: 7px 10px; font-size: 12px; font-weight: 600; color: #059669;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; margin-top: 8px; }
.basis-row { font-size: 13px; font-weight: 600; color: #00447C; }
.cfr { font-size: 11.5px; color: #9ca3af; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.resolved-detail { background: #f3f4f6; border-radius: 4px; padding: 14px; margin-top: 10px; }
.arrow-from { color: #9ca3af; }
.arrow-to { color: #059669; font-weight: 700; }
.audit-block { background: #f3f4f6; border-radius: 4px; padding: 12px 14px; margin-top: 10px; }
.audit-row { font-size: 11.5px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  padding: 8px 0; border-top: 1px solid #e5e7eb; color: #374151; }
.audit-row:first-of-type { border-top: none; }
.audit-label { color: #9ca3af; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  font-size: 10px; }
</style>
"""


def load_fixture(n=1):
    return json.loads((DATA / f"fixture_{n}.json").read_text())


def option(incident, option_id):
    return next(opt for opt in incident["options"] if opt["id"] == option_id)


def tablets_at_risk(incident):
    return int(incident["tablets_per_hour"] * incident["mean_hours_to_forced_shutdown"])


def dollars_at_risk(incident):
    return int(tablets_at_risk(incident) / 1000 * incident["contribution_margin_per_1000"])


def render_sidebar():
    st.sidebar.markdown('<div class="sidenav-brand">FactoryOps Pharma</div>', unsafe_allow_html=True)
    for group, items in NAV:
        st.sidebar.markdown(f'<div class="sidenav-group">{group}</div>', unsafe_allow_html=True)
        for item in items:
            if item == LIVE_MACHINE:
                st.sidebar.markdown(f'<div class="sidenav-active">{item}</div>', unsafe_allow_html=True)
            else:
                st.sidebar.button(item, key=f"nav_{item}", use_container_width=True)


def gate_lane_html(incident, gate):
    vibration_delta = (incident["vibration_mm_s"] - incident["max_vibration_mm_s"]) / incident["max_vibration_mm_s"]
    temp_delta = incident["motor_temperature_c"] - incident["max_motor_temperature_c"]
    cause = incident["likely_cause"] or "Insufficient data to determine root cause"
    basis = ", ".join(incident["confidence_basis"][:2])
    pct = int(round(vibration_delta * 100))
    return f"""
<div class="lane">
  <div class="lane-title">Policy Gate</div>
  <div class="lane-body">
    <div class="eyebrow">Likely Cause</div>
    <div class="cause-headline">{cause}</div>
    <p style="font-weight:600;color:#374151;margin:6px 0 0;">Confidence: {incident["confidence"].title()}</p>
    <p class="muted">{basis}</p>
    <div class="eyebrow">Evidence</div>
    <div class="evidence-row"><span>Vibration</span><span>{incident["vibration_mm_s"]}&nbsp;mm/s · limit {incident["max_vibration_mm_s"]}&nbsp;mm/s · <span class="delta-bad">+{pct}%</span></span></div>
    <div class="evidence-row"><span>Motor temperature</span><span>{incident["motor_temperature_c"]}&nbsp;°C · limit {incident["max_motor_temperature_c"]}&nbsp;°C · <span class="delta-bad">+{int(temp_delta)}&nbsp;°C</span></span></div>
    <div class="evidence-row"><span>Tablet weight RSD</span><span>{incident["tablet_weight_rsd_pct"]}% · trending up</span></div>
    <div class="eyebrow">Impact</div>
    <div class="tile-wrap">
      <div class="tile"><div class="tile-number">{tablets_at_risk(incident):,}</div><div class="tile-caption">tablets at risk</div></div>
      <div class="tile"><div class="tile-number">${dollars_at_risk(incident):,}</div><div class="tile-caption">production contribution at risk</div></div>
    </div>
    <div class="assumption">Assumes ${incident["contribution_margin_per_1000"]} contribution margin per 1,000 tablets · {incident["tablets_per_hour"]:,} tablets/hr · {incident["mean_hours_to_forced_shutdown"]} hr estimated downtime</div>
    <div class="quality-flag">Batch {incident["batch_id"]} flagged for QA disposition</div>
    <div class="eyebrow">Gate Decision</div>
    <div class="gate-decision">
      <div class="gate-decision-value">{gate["decision"]} required</div>
      <div class="gate-decision-basis">{" · ".join(gate["regulatory_basis"])}</div>
    </div>
  </div>
</div>
"""


def options_lane_html(incident):
    a = option(incident, "A")
    b = option(incident, "B")
    c = option(incident, "C")
    rollback = b.get("rollback_review_by", "")
    return f"""
<div class="lane">
  <div class="lane-title">Intervention Options</div>
  <div class="lane-body">
    <div class="option-line"><span>A · {a["description"]}</span><span class="class-tag class-deviation">{a["gamp_change_type"]}</span></div>
    <div class="option-line"><span>B · {b["description"]}</span><span><span class="rollback-inline">rollback by {rollback}</span><span class="class-tag class-temporary">{b["gamp_change_type"]}</span></span></div>
    <div class="option-card">
      <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;">
        <span class="option-title">C · {c["description"]}</span>
        <span><span class="class-tag class-repair">{c["gamp_change_type"]}</span> <span class="recommended">Recommended</span></span>
      </div>
      <p style="font-size:13px;color:#374151;margin:8px 0 0;">Like-for-like repair, pre-approved. Specification does not change. Estimated intervention: 3.5&nbsp;hr.</p>
    </div>
  </div>
</div>
"""


def approval_intro_html(gate):
    basis = gate["regulatory_basis"][0] if gate["regulatory_basis"] else "21 CFR 211.100(a)"
    return f"""
<div class="lane-title">Approval Workflow</div>
<div class="lane-body" style="padding-bottom:0;">
  <div class="basis-row">Human approval required</div>
  <div class="cfr">{basis}</div>
</div>
"""


def supervisor_block_html(record):
    signed = next((sig for sig in record["signatures"] if sig["role"] == "Maintenance Supervisor"), None)
    if signed:
        clock = signed["timestamp"][11:16] if "T" in signed["timestamp"] else signed["timestamp"]
        return f"""
    <div class="sig-block">
      <div class="sig-role">Maintenance Supervisor</div>
      <div class="sig-meaning">signs to approve the intervention</div>
      <div class="sig-confirmed">Intervention approved · {clock} · {signed["name"]}</div>
    </div>
"""
    return """
    <div class="sig-block">
      <div class="sig-role">Maintenance Supervisor</div>
      <div class="sig-meaning">signs to approve the intervention</div>
    </div>
"""


def qa_block_html(record):
    signed = next((sig for sig in record["signatures"] if sig["role"] == "Quality Assurance"), None)
    if signed:
        clock = signed["timestamp"][11:16] if "T" in signed["timestamp"] else signed["timestamp"]
        return f"""
    <div class="sig-block">
      <div class="sig-role">Quality Assurance</div>
      <div class="sig-meaning">signs to review batch disposition</div>
      <div class="sig-confirmed">Batch disposition reviewed · {clock} · {signed["name"]}</div>
    </div>
"""
    return """
    <div class="sig-block">
      <div class="sig-role">Quality Assurance</div>
      <div class="sig-meaning">signs to review batch disposition</div>
    </div>
"""


def resolved_html(incident):
    return f"""
    <div class="resolved-detail">
      <div class="eyebrow" style="margin-top:0;">Post-Intervention Verification</div>
      <div class="muted" style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;">
        <div>Vibration&nbsp; <span class="arrow-from">{incident["vibration_mm_s"]}</span> → <span class="arrow-to">4.3</span>&nbsp;mm/s</div>
        <div>Motor temp&nbsp; <span class="arrow-from">{incident["motor_temperature_c"]}</span> → <span class="arrow-to">66</span>&nbsp;°C</div>
        <div>Weight RSD&nbsp; <span class="arrow-from">{incident["tablet_weight_rsd_pct"]}%</span> → <span class="arrow-to">1.1%</span></div>
      </div>
      <p class="muted" style="margin:8px 0 0;">Maintenance recommendation: inspect bearing at next scheduled service.</p>
      <div class="quality-flag">Batch {incident["batch_id"]} remains flagged for QA disposition</div>
    </div>
"""


def audit_html(record):
    if not record["audit"]:
        return ""
    rows = []
    for entry in record["audit"]:
        clock = entry["when"][11:19] if "T" in entry["when"] else entry["when"]
        before = entry["before"]
        if isinstance(before, dict):
            before_text = before.get("state", str(before))
        else:
            before_text = str(before)
        rows.append(
            f'<div class="audit-row">'
            f'<div><span class="audit-label">who</span> {entry["who"]}</div>'
            f'<div><span class="audit-label">what</span> {entry["what"]}</div>'
            f'<div><span class="audit-label">when</span> {clock}</div>'
            f'<div><span class="audit-label">why</span> {entry["why"]}</div>'
            f'<div><span class="audit-label">before</span> {before_text}</div>'
            f'<div><span class="audit-label">source</span> {entry["data_source"]}</div>'
            f"</div>"
        )
    return (
        '<div class="audit-block"><div class="eyebrow" style="margin-top:0;">Audit</div>'
        + "".join(rows)
        + "</div>"
    )


def approval_lane_html(gate):
    basis = gate["regulatory_basis"][0] if gate["regulatory_basis"] else "21 CFR 211.100(a)"
    return f"""
<div class="lane">
  <div class="lane-title">Approval Workflow</div>
  <div class="lane-body">
    <div class="basis-row">Human approval required</div>
    <div class="cfr">{basis}</div>
    <div class="sig-block">
      <div class="sig-role">Maintenance Supervisor</div>
      <div class="sig-meaning">signs to approve the intervention</div>
    </div>
    <div class="sig-block">
      <div class="sig-role">Quality Assurance</div>
      <div class="sig-meaning">signs to review batch disposition</div>
    </div>
  </div>
</div>
"""


def header_html(incident):
    return (
        f'<span class="incident-id">{incident["incident_id"]}</span>'
        f'<span class="sim-tag">Simulated Plant Data</span>'
        f'<div class="subline">Rotary Tablet Press · Machine {incident["machine_id"]} · '
        f'Batch {incident["batch_id"]} · {incident["product"]}</div>'
    )


def status_html(record=None):
    if record and is_resolved(record):
        return '<div class="status-banner status-resolved">Incident Resolved — Equipment Returned to Normal Range</div>'
    return '<div class="status-banner">Critical Equipment Incident — Human Approval Required</div>'


def init_record(incident, gate):
    if "record" not in st.session_state:
        st.session_state.record = new_record(incident, option(incident, "C"), gate)
    return st.session_state.record


def render_approval_lane(incident, gate, record):
    st.markdown(approval_intro_html(gate), unsafe_allow_html=True)
    st.markdown(supervisor_block_html(record), unsafe_allow_html=True)
    if record["state"] == STATE_PRESENTED:
        if st.button("Approve Intervention", key="btn_supervisor", type="primary", use_container_width=True):
            sign_supervisor(st.session_state.record)
            st.rerun()
    st.markdown(qa_block_html(record), unsafe_allow_html=True)
    qa_ready = record["state"] == STATE_SUPERVISOR_SIGNED
    if record["state"] in (STATE_PRESENTED, STATE_SUPERVISOR_SIGNED):
        if st.button(
            "Review Batch Disposition",
            key="btn_qa",
            type="primary" if qa_ready else "secondary",
            disabled=not qa_ready,
            use_container_width=True,
        ):
            sign_qa(st.session_state.record)
            resolve(st.session_state.record)
            st.rerun()
    if is_resolved(record):
        st.markdown(resolved_html(incident), unsafe_allow_html=True)
    st.markdown(audit_html(record), unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="FactoryOps Pharma — Incident Approval", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    render_sidebar()
    incident = load_fixture(1)
    gate = evaluate(incident, option(incident, "C"))
    record = init_record(incident, gate)
    st.markdown(header_html(incident), unsafe_allow_html=True)
    st.markdown(status_html(record), unsafe_allow_html=True)
    col_gate, col_options, col_approval = st.columns([2, 1.3, 1.3])
    with col_gate:
        st.markdown(gate_lane_html(incident, gate), unsafe_allow_html=True)
    with col_options:
        st.markdown(options_lane_html(incident), unsafe_allow_html=True)
    with col_approval:
        render_approval_lane(incident, gate, record)


if __name__ == "__main__":
    main()
