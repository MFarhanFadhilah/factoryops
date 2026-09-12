from pathlib import Path

from app import (
    EMPTY_CAUSE,
    EMPTY_RETRIEVAL,
    QA_DENY_NEEDS_REASON,
    approval_intro_html,
    approval_lane_html,
    hold_html,
    qa_denial_reason,
    supervisor_copy,
    approval_shell_html,
    audit_html,
    cause_line,
    gate_lane_html,
    header_html,
    load_fixture,
    option,
    decision_label,
    option_card_html,
    options_lane_html,
    options_rows_html,
    options_shell_html,
    qa_block_html,
    resolved_html,
    retrieved_html,
    status_html,
    supervisor_block_html,
    tablets_at_risk,
    dollars_at_risk,
)
from approval import (
    STATE_SUPERVISOR_SIGNED,
    is_on_hold,
    is_resolved,
    new_record,
    resolve,
    sign_qa,
    sign_supervisor,
)
from policy_gate import evaluate


def _signed_record(fixture_n, option_id):
    incident = load_fixture(fixture_n)
    opt = option(incident, option_id)
    gate = evaluate(incident, opt)
    rec = new_record(incident, opt, gate)
    sign_supervisor(rec)
    return incident, gate, rec


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


def _page_for(n):
    incident = load_fixture(n)
    gate = evaluate(incident, option(incident, "C"))
    return incident, gate, (
        header_html(incident)
        + status_html()
        + gate_lane_html(incident, gate)
        + options_lane_html(incident)
        + approval_lane_html(gate)
        + retrieved_html(incident)
    )


def test_review_evidence_shows_tier_source_section_page():
    html = retrieved_html(load_fixture(1)).lower()
    assert "t1" in html
    assert "tablet press troubleshooting guide" in html
    assert "§4.2" in html
    assert "p.&nbsp;18" in html or "p. 18" in html
    page = gate_lane_html(load_fixture(1), evaluate(load_fixture(1), option(load_fixture(1), "C"))).lower()
    assert "review evidence" in page
    assert "retrieved, ranked by relevance" in page


def test_fixture_3_does_not_invent_cause_and_keeps_three_lanes():
    incident, gate, page = _page_for(3)
    text = page.lower()
    assert incident["likely_cause"] is None
    assert incident["retrieved"] == []
    assert cause_line(incident) == EMPTY_CAUSE
    assert EMPTY_CAUSE.lower() in text
    assert "main-drive bearing degradation" not in text
    assert EMPTY_RETRIEVAL.lower() in retrieved_html(incident).lower()
    assert "policy gate" in text
    assert "intervention options" in text
    assert "approval workflow" in text
    assert "approve the intervention" in text
    assert "batch disposition" in text
    assert gate["decision"] == "HUMAN_APPROVAL"
    assert "compliant" not in text
    assert "anomaly" not in text


def test_lanes_are_numbered_and_gate_points_to_options():
    page = _page()
    assert ">1</span> policy gate" in page
    assert ">2</span> intervention options" in page
    assert ">3</span> approval workflow" in page
    assert "next: recommended intervention" in gate_lane_html(
        load_fixture(1), evaluate(load_fixture(1), option(load_fixture(1), "C")), show_next=True
    ).lower()
    assert "next: recommended intervention" not in gate_lane_html(
        load_fixture(1), evaluate(load_fixture(1), option(load_fixture(1), "C")), show_next=False
    ).lower()


def test_options_lane_owned_by_supervisor():
    html = options_lane_html(load_fixture(1)).lower()
    # The pill says "Supervisor", not "Maintenance Supervisor" — the full role
    # name wrapped this column's navy bar onto two lines and left lane 2's
    # title taller than lanes 1 and 3. The full name is still on the screen,
    # in the signature block that does the signing.
    assert "owner-pill" in html
    assert "supervisor" in html
    assert "maintenance supervisor" in approval_lane_html(
        evaluate(load_fixture(1), option(load_fixture(1), "C"))
    ).lower()


def test_every_lane_is_one_card_with_one_padded_body():
    # The bug this guards: lanes 2 and 3 were assembled from loose pieces, so
    # the gap from the navy bar to the first line of text differed per lane.
    # Every lane built as HTML is now title + a single .lane-body.
    incident = load_fixture(1)
    gate = evaluate(incident, option(incident, "C"))
    for html in (
        gate_lane_html(incident, gate),
        options_lane_html(incident),
        approval_lane_html(gate),
        options_shell_html(incident),
        approval_shell_html(),
    ):
        assert html.count('class="lane"') + html.count('class="lane lane-shell"') == 1
        assert html.count('class="lane-body"') == 1
        assert html.count('class="lane-title"') == 1
        assert html.count("<div") == html.count("</div>")
        assert "&lt;/div&gt;" not in html
    # The live lanes carry no hand-built wrapper of their own: the card and the
    # padding come from lane_container(), which shares the CSS declaration.
    src = (Path(__file__).resolve().parents[1] / "src" / "app.py").read_text()
    assert "def lane_container(" in src
    assert ".lane-body, div[class*=\"st-key-lanebody_\"] { padding:" in src


def test_picking_option_a_shows_signed_deviation_not_a_dead_end():
    # 21 CFR 211.100(b): a deviation is recorded and justified — a signed act.
    # Continuing outside the limit is still the worst option, but it is not
    # something the gate refuses to let a human take responsibility for.
    incident = load_fixture(1)
    gate_a = evaluate(incident, option(incident, "A"))
    assert gate_a["decision"] == "HUMAN_APPROVAL"
    assert gate_a["change_type"] == "Deviation"
    card = option_card_html(incident, "A", gate_a, expanded=True).lower()
    assert "human_approval" in card
    # Both rules that put someone on the signature list are visible.
    assert "211.100(b)" in card
    assert "211.22" in card
    assert "deviation" in card
    # Still never the recommendation.
    assert 'class="recommended"' not in card


def test_picking_option_b_and_c_show_human_approval():
    incident = load_fixture(1)
    for oid in ("B", "C"):
        gate = evaluate(incident, option(incident, oid))
        card = option_card_html(incident, oid, gate, expanded=True).lower()
        assert "human_approval required" in card
    assert 'class="recommended"' in option_card_html(
        incident, "C", evaluate(incident, option(incident, "C")), expanded=True
    )
    assert 'class="recommended"' not in option_card_html(
        incident, "B", evaluate(incident, option(incident, "B")), expanded=True
    )


def test_collapsed_option_b_still_shows_rollback():
    incident = load_fixture(1)
    line = option_card_html(incident, "B", evaluate(incident, option(incident, "B")), expanded=False).lower()
    assert "rollback by 18:00" in line
    assert "temporary change" in line


def test_every_option_is_readable_without_being_selected():
    incident = load_fixture(1)
    rows = options_rows_html(incident, selected="C")
    low = rows.lower()
    # A and B are native disclosures; C never collapses (spec 5.3).
    assert low.count('<details class="option-disclosure"') == 2
    assert "<summary>" in low
    # Collapsed summaries keep the one-line facts.
    assert "rollback by 18:00" in low
    assert "temporary change" in low
    # Each option that is NOT the chosen one carries its own verdict — peek
    # without picking. A's route is a signed deviation, not a dead end.
    # The chosen option's verdict is deliberately absent: the gate evaluates
    # whatever is selected, so it is already the foot of lane 1 and the head
    # of lane 3, and a third copy in the narrowest column says nothing new.
    assert low.count("human_approval required") == 2
    assert "human_approval required" not in option_card_html(
        incident, "C", evaluate(incident, option(incident, "C")), expanded=True, chosen=True
    ).lower()
    assert "211.100(b)" in low
    assert "deny" not in low


def test_chosen_option_starts_open_and_is_marked():
    incident = load_fixture(1)
    with_b = options_rows_html(incident, selected="B")
    assert '<details class="option-disclosure" open>' in with_b
    assert with_b.count("option-disclosure\" open") == 1
    assert "option-line-chosen" in with_b
    # Once in the markup, not once on screen with a hidden twin: a disclosure
    # body no longer repeats the head its summary line already shows.
    assert with_b.count(">Chosen<") == 1
    assert with_b.count("option-card-head") == 1
    with_c = options_rows_html(incident, selected="C")
    # C carries the marker in its always-open card; neither A nor B opens.
    assert "option-disclosure\" open" not in with_c
    assert with_c.count(">Chosen<") == 1
    assert ">Recommended<" in with_c
    # Selecting does not move the Recommended marker off C.
    assert ">Recommended<" in with_b


def test_decision_label_wording():
    incident = load_fixture(1)
    # Every option on this fixture now needs a human; the label says so.
    for oid in ("A", "B", "C"):
        assert decision_label(evaluate(incident, option(incident, oid))) == "HUMAN_APPROVAL required"
    # The DENY label still exists for the paths that genuinely have no
    # signature route (missing rollback date, speed outside qualified range).
    assert decision_label({"decision": "DENY"}) == "DENY — autonomous path"
    assert decision_label({"decision": "ALLOW"}) == "ALLOW"


def test_signature_blocks_highlight_active_role():
    incident = load_fixture(1)
    gate = evaluate(incident, option(incident, "C"))
    rec = new_record(incident, option(incident, "C"), gate)
    # Acting as supervisor: supervisor block owned, QA block waiting.
    sup = supervisor_block_html(rec, "Maintenance Supervisor")
    qa = qa_block_html(rec, "Maintenance Supervisor")
    assert "sig-owned" in sup
    assert "sig-waiting" in qa
    # Acting as QA: the ownership flips.
    sup2 = supervisor_block_html(rec, "Quality Assurance")
    qa2 = qa_block_html(rec, "Quality Assurance")
    assert "sig-waiting" in sup2
    assert "sig-owned" in qa2
    # Meanings and units stay distinct and correct.
    assert "operating unit" in sup.lower()
    assert "quality unit" in qa.lower()


def test_beat_one_shells_keep_the_map():
    incident = load_fixture(1)
    options = options_shell_html(incident).lower()
    approval = approval_shell_html().lower()
    assert "c recommended" in options
    assert "repair" in options
    assert "2 signatures required" in approval
    assert "supervisor approved" in approval
    assert "qa reviewed" in approval
    assert "approve intervention" not in approval
    assert "lane-shell" in options
    assert "lane-shell" in approval
    assert ">2</span> intervention options" in options
    assert ">3</span> approval workflow" in approval
    full_options = options_lane_html(incident).lower()
    assert "controlled shutdown" in full_options
    assert "lane-shell" not in full_options


def test_qa_denial_needs_a_reason_before_anything_is_recorded():
    incident, gate, rec = _signed_record(1, "C")
    assert rec["state"] == STATE_SUPERVISOR_SIGNED
    # Blank and whitespace-only reasons record nothing at all.
    for empty in ("", "   "):
        sign_qa(rec, decision="deny", reason=empty)
        assert rec["state"] == STATE_SUPERVISOR_SIGNED
        assert not is_on_hold(rec)
        assert qa_denial_reason(rec) == ""
        assert qa_block_html(rec).lower().count("k. chen") == 0
    # The screen's warning names the problem AND the fix, not just the problem.
    warning = QA_DENY_NEEDS_REASON.lower()
    assert "reason" in warning
    assert "deny" in warning
    # A real reason lands on the hold state, and only there.
    sign_qa(rec, decision="deny", reason="Weight RSD trend not explained by the bearing.")
    assert is_on_hold(rec)
    assert not is_resolved(rec)
    assert qa_denial_reason(rec) == "Weight RSD trend not explained by the bearing."


def test_hold_renders_distinctly_from_resolved_and_invents_no_telemetry():
    incident, gate, rec = _signed_record(1, "C")
    sign_qa(rec, decision="deny", reason="Weight RSD trend not explained by the bearing.")
    hold = hold_html(incident, rec).lower()
    resolved = resolved_html(incident).lower()
    # The reason QA typed is the point of the block.
    assert "weight rsd trend not explained by the bearing." in hold
    assert "hold-detail" in hold
    # Not the resolved block, and none of its post-intervention numbers.
    assert "resolved-detail" not in hold
    assert "post-intervention verification" in resolved
    assert "post-intervention verification" not in hold
    assert "4.3" not in hold
    assert "arrow-to" not in hold
    # Its own banner state, not the green one and not the amber opening one.
    banner = status_html(rec).lower()
    assert "status-hold" in banner
    assert "incident resolved" not in banner
    assert "compliant" not in hold
    # No stray tag text from a dropped conditional fragment.
    assert "&lt;/div&gt;" not in hold
    assert hold.count("<div") == hold.count("</div>")


def test_deviation_supervisor_copy_is_not_intervention_copy():
    incident, gate_a, dev = _signed_record(1, "A")
    _, gate_c, rep = _signed_record(1, "C")
    assert dev["change_type"] == "Deviation"
    dev_copy, rep_copy = supervisor_copy(dev), supervisor_copy(rep)
    # Different act, different words — in the block, on the button, everywhere.
    for field in ("meaning", "confirmed", "button", "waiting_for"):
        assert dev_copy[field] != rep_copy[field]
    assert "deviation" in dev_copy["button"].lower()
    assert "approve" not in dev_copy["button"].lower()
    dev_block = supervisor_block_html(dev).lower()
    assert "intervention approved" not in dev_block
    assert "deviation acknowledged" in dev_block
    assert "intervention approved" in supervisor_block_html(rep).lower()
    # The deviation's approval lane cites both rules that put someone on the list.
    intro = approval_intro_html(gate_a)
    assert "211.100(b)" in intro
    assert "211.22" in intro


def test_qa_signature_never_says_approved():
    _, _, unsigned = _signed_record(1, "C")
    blocks = [qa_block_html(unsigned)]
    _, _, approved = _signed_record(1, "C")
    sign_qa(approved, decision="approve")
    resolve(approved)
    blocks.append(qa_block_html(approved))
    _, _, denied = _signed_record(1, "C")
    sign_qa(denied, decision="deny", reason="Investigation still open.")
    blocks.append(qa_block_html(denied))
    for html in blocks:
        low = html.lower()
        assert "approve" not in low
        assert "authorized" not in low
        assert "compliant" not in low
    assert "reviewed" in blocks[1].lower()
    assert "denied" in blocks[2].lower()


def test_fixture_3_shells_still_named():
    incident, gate, page = _page_for(3)
    shells = (options_shell_html(incident) + approval_shell_html()).lower()
    assert EMPTY_CAUSE.lower() in page.lower()
    assert "intervention options" in shells
    assert "approval workflow" in shells
    assert "c recommended" in shells
    assert "2 signatures required" in shells
