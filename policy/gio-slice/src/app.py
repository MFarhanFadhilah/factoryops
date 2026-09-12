import json
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

import streamlit as st

from approval import (
    MEANING_SUPERVISOR_DEVIATION,
    STATE_PRESENTED,
    STATE_SUPERVISOR_SIGNED,
    can_sign,
    is_on_hold,
    is_resolved,
    new_record,
    resolve,
    sign_qa,
    sign_supervisor,
    supervisor_meaning,
)
from policy_gate import ROLE_QA, ROLE_SUPERVISOR, evaluate, limit_violations

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
/* Streamlit relocates the "re-expand the sidebar" button into the header
   once the sidebar is collapsed — hiding the whole header (above, for the
   default deploy/hamburger chrome) silently hid this too, so collapsing
   the sidebar was a one-way trip with no way back. Force just this one
   control visible again; the rest of the header stays hidden. */
header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] { visibility: visible !important; }
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
div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"],
div[data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button {
  background: #0076CE; color: #ffffff; border: none; font-weight: 600; border-radius: 4px;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"] {
  background: #f3f4f6; color: #9ca3af; border: 1px solid #e5e7eb; font-weight: 600; border-radius: 4px;
}
.incident-id { font-size: 16px; font-weight: 700; color: #00447C;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.sim-tag { font-size: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  color: #374151; background: #e5e7eb; border-radius: 4px; padding: 4px 8px; margin-left: 8px; }
.subline { font-size: 12px; color: #9ca3af; margin-top: 4px; margin-bottom: 12px; }
.status-banner { padding: 12px 20px; font-size: 16px; font-weight: 700; color: #d97706;
  background: rgba(217,119,6,0.12); border-radius: 4px; margin-bottom: 16px; }
.status-resolved { color: #059669; background: rgba(5,150,105,0.12); }
/* Third status state. Red is already this screen's word for "outside the
   approved limit" (.delta-bad, .class-deviation) — a quality hold is the same
   vocabulary, not a new one. §7: palette is reserved for status. */
.status-hold { color: #dc2626; background: rgba(220,38,38,0.12); }
/* One lane, two ways to build it — same card, same padding.
   Lane 1 is a single st.markdown string, so its card is the .lane div.
   Lanes 2 and 3 contain native widgets (radio, buttons, text_area) that
   cannot live inside one HTML string, so their card is a keyed
   st.container (Streamlit stamps it .st-key-<key>). Both selectors share
   one declaration so the border-to-first-text gap is one number, declared
   once, for all three lanes. */
.lane, div[class*="st-key-lanecard_"] {
  background: #ffffff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.lane-title { font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  color: #ffffff; background: #00447C; padding: 10px 18px; border-radius: 4px 4px 0 0;
  display: flex; align-items: center; gap: 10px; min-height: 40px; }
.lane-num { display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.7);
  font-size: 11px; letter-spacing: 0; flex-shrink: 0; }
.lane-body, div[class*="st-key-lanebody_"] { padding: 20px 18px 16px; }
/* Streamlit hangs margin-bottom:-1rem on every markdown block to cancel the
   trailing <p>'s own 1rem margin. These lanes are raw HTML divs with no such
   margin, so the compensation left each block 16px shorter than its content
   and the next block overlapped it. Inside a lane the container gap is the
   only thing that spaces blocks. */
div[class*="st-key-lanecard_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0; }
/* The gap above the first line of text is the padding, nothing else — so a
   fragment's own top margin (.eyebrow is 12px) can't make lane 1 sit lower
   than the lanes whose first element is a widget. */
.lane-body > *:first-child { margin-top: 0; }
/* Inside a Streamlit-built lane body the container gap owns the vertical
   rhythm, because widgets carry no margins of their own. These fragments
   would otherwise add their margin on top of it. */
div[class*="st-key-lanebody_"] .sig-block,
div[class*="st-key-lanebody_"] .audit-block,
div[class*="st-key-lanebody_"] .resolved-detail,
div[class*="st-key-lanebody_"] .hold-detail,
div[class*="st-key-lanebody_"] .handoff-hint { margin-top: 0; }
div[class*="st-key-lanebody_"] .option-line:last-child,
div[class*="st-key-lanebody_"] details.option-disclosure:last-child > .option-card,
div[class*="st-key-lanebody_"] .option-card:last-child { margin-bottom: 0; }
/* Same trap the .option-detail rule below documents, and it was biting every
   other paragraph in every lane: Streamlit's own
   [data-testid="stMarkdownContainer"] p { font-size: inherit } outranks a
   bare class, so supporting lines rendered at 16px — level with the cause
   headline they support — instead of the 13px the mockup specifies. One
   extra qualifier each is all it takes to win. */
.lane p.muted, div[class*="st-key-lanecard_"] p.muted { font-size: 13px; line-height: 1.55; }
.lane p.shell-line { font-size: 13px; }
.lane p.shell-hint { font-size: 12px; }
.evidence-detail p.empty-retrieval { font-size: 13px; }
.eyebrow { font-size: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  color: #374151; margin-top: 12px; }
.cause-headline { font-size: 18px; font-weight: 600; color: #00447C; }
.muted { color: #9ca3af; font-size: 13px; }
.evidence-row { display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; border-top: 1px solid #f3f4f6; }
/* The parameter's name is the column you read down; it never wraps. Only the
   reading may, and "Tablet thickness" — the longest label and the longest
   reading on the panel — was breaking both. */
.evidence-row > span:first-child { white-space: nowrap; }
.evidence-row > span:last-child { text-align: right; }
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
.next-step { font-size: 11.5px; font-weight: 600; color: #0076CE; margin-top: 8px; }
/* The beat-1 call to action sits under lane 1's card. Streamlit's own
   markdown margin cancels the column gap exactly, so without this the
   button is glued to the card's bottom edge. */
.st-key-btn_next { margin-top: 12px; }
.lane-shell { opacity: 0.5; }
.shell-line { font-size: 13px; font-weight: 600; color: #00447C; margin: 8px 0 0; }
.shell-hint { font-size: 12px; color: #9ca3af; margin: 4px 0 0; }
.option-line { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap;
  background: #f3f4f6; border-radius: 4px; padding: 13px 14px; font-size: 13px; font-weight: 600;
  line-height: 1.5; color: #00447C; margin-bottom: 12px; }
.option-card { border-left: 3px solid #0076CE; background: #eef6fb; border-radius: 4px;
  padding: 16px 16px 18px; margin-bottom: 12px; }
.option-card-head { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.option-title { font-size: 14px; font-weight: 600; line-height: 1.45; color: #00447C; }
/* Scoped through .option-card on purpose: Streamlit's own
   [data-testid="stMarkdownContainer"] p rule outranks a bare class and would
   silently push this paragraph back to 16px. */
.option-card p.option-detail { font-size: 13px; line-height: 1.55; color: #374151; margin: 10px 0 0; }
.option-card .gate-decision { margin-top: 12px; }
.option-card .gate-decision-basis { line-height: 1.5; }
.class-tag { font-size: 11px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
  border-radius: 4px; padding: 4px 8px; white-space: nowrap; }
.class-deviation { background: rgba(220,38,38,0.12); color: #dc2626; }
.class-temporary { background: rgba(217,119,6,0.12); color: #d97706; }
.class-repair { background: rgba(5,150,105,0.12); color: #059669; }
.rollback-inline { font-size: 11.5px; font-weight: 600; color: #d97706; margin-right: 6px;
  white-space: nowrap; }
.recommended { font-size: 11.5px; font-weight: 700; color: #0076CE; }
.sig-block { background: #f3f4f6; border-radius: 4px; padding: 12px 14px; margin-top: 10px; }
.sig-role { font-size: 13.5px; font-weight: 700; color: #00447C; }
.sig-meaning { font-size: 11.5px; color: #9ca3af; }
.sig-confirmed { display: flex; align-items: center; gap: 6px; background: rgba(5,150,105,0.12);
  border-radius: 4px; padding: 7px 10px; font-size: 12px; font-weight: 600; color: #059669;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; margin-top: 8px; }
.sig-confirmed.sig-denied { background: rgba(220,38,38,0.12); color: #dc2626; }
.basis-row { font-size: 13px; font-weight: 600; color: #00447C; }
.cfr { font-size: 11.5px; color: #9ca3af; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.resolved-detail { background: #f3f4f6; border-radius: 4px; padding: 14px; margin-top: 10px; }
/* Deliberately NOT .resolved-detail: nothing was verified, so this block
   carries no post-intervention telemetry. Only what QA actually wrote. */
.hold-detail { background: #f3f4f6; border-left: 3px solid #dc2626; border-radius: 4px;
  padding: 14px; margin-top: 10px; }
.hold-detail p.hold-reason { font-size: 13px; line-height: 1.55; color: #374151; margin: 8px 0 0; }
.deny-label { font-size: 11.5px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  color: #6b7280; margin: 0 0 2px; }
div[data-testid="stHorizontalBlock"] .st-key-btn_qa_deny .stButton > button[kind="secondary"],
div[data-testid="stHorizontalBlock"] .st-key-btn_qa_deny button[kind="secondary"],
div[data-testid="stHorizontalBlock"] .st-key-btn_qa_deny button {
  background: #ffffff; color: #dc2626; border: 1px solid #dc2626; font-weight: 600;
  border-radius: 4px;
}
.arrow-from { color: #9ca3af; }
.arrow-to { color: #059669; font-weight: 700; }
.audit-block { background: #f3f4f6; border-radius: 4px; padding: 12px 14px; margin-top: 10px; }
.audit-row { font-size: 11.5px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  padding: 8px 0; border-top: 1px solid #e5e7eb; color: #374151; }
.audit-row:first-of-type { border-top: none; }
.audit-label { color: #9ca3af; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  font-size: 10px; }
.evidence-header { display: flex; align-items: center; justify-content: space-between; }
details.evidence-disclosure > summary {
  list-style: none; cursor: pointer; font-size: 13px; font-weight: 600; color: #0076CE;
  border: 1px solid #0076CE; border-radius: 4px; padding: 6px 10px; display: inline-flex;
  align-items: center; gap: 6px;
}
details.evidence-disclosure > summary::-webkit-details-marker { display: none; }
details.option-disclosure > summary { list-style: none; cursor: pointer; display: block; }
details.option-disclosure > summary::-webkit-details-marker { display: none; }
details.option-disclosure > summary .option-line { border-left: 3px solid transparent; }
details.option-disclosure > summary .option-line.option-line-chosen { border-left-color: #0076CE; }
details.option-disclosure > summary:hover .option-line { background: #e5e7eb; }
details.option-disclosure[open] > summary .option-line { border-radius: 4px 4px 0 0; margin-bottom: 0; }
details.option-disclosure[open] > .option-card { border-radius: 0 0 4px 4px; margin-bottom: 12px; }
.evidence-detail { margin-top: 8px; background: #f3f4f6; border-radius: 4px; padding: 14px; }
.retrieved-item { display: flex; gap: 8px; padding: 8px 0; }
.retrieved-item + .retrieved-item { border-top: 1px solid #e5e7eb; }
.tier-tag { font-size: 11px; font-weight: 700; border-radius: 4px; padding: 2px 6px;
  flex-shrink: 0; align-self: flex-start;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.tier-t1 { background: rgba(0,118,206,0.12); color: #0076CE; }
.tier-t2 { background: rgba(55,65,81,0.12); color: #374151; }
.tier-t3 { background: rgba(156,163,175,0.18); color: #6b7280; }
.retrieved-title { font-size: 13px; font-weight: 600; color: #00447C; }
.retrieved-meta { font-size: 12px; color: #9ca3af; }
.empty-retrieval { font-size: 13px; color: #374151; }
.fixture-label { font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  color: #9ca3af; padding: 16px 4px 4px; }
.role-label { font-size: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  color: #374151; margin-bottom: 2px; }
.owner-pill { font-size: 10.5px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
  color: #00447C; background: rgba(0,68,124,0.10); border-radius: 4px; padding: 2px 7px;
  white-space: nowrap; }
/* line-height pinned so the pill cannot make lane 2's bar taller than the
   bars either side of it — all three navy bars are exactly 40px. */
.lane-title .owner-pill { color: #ffffff; background: rgba(255,255,255,0.18); line-height: 1.35; }
.sig-block.sig-owned { border-left: 3px solid #0076CE; }
.sig-block.sig-waiting { opacity: 0.5; }
.owner-tag { font-size: 10.5px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
  color: #6b7280; }
.handoff-hint { font-size: 12.5px; font-weight: 600; color: #d97706;
  background: rgba(217,119,6,0.10); border-radius: 4px; padding: 8px 12px; margin-top: 8px; }
</style>
"""

EMPTY_CAUSE = "Insufficient data to determine root cause"
EMPTY_RETRIEVAL = "No matching documents returned. The agent does not invent a cause."


def load_fixture(n=1):
    return json.loads((DATA / f"fixture_{n}.json").read_text())


def lane_title_html(num, label, owner=""):
    """The navy bar at the top of a lane. One function, so all three match.

    The owner pill goes through _join_fragments: an empty owner cannot leave
    a stray element or a whitespace-only line inside the raw HTML block.
    """
    pill = f'<span style="flex:1;"></span><span class="owner-pill">{owner}</span>' if owner else ""
    return _join_fragments(
        f'<div class="lane-title"><span class="lane-num">{num}</span> {label}',
        pill,
        "</div>",
    )


def lane_html(title, body, shell=False):
    """A whole lane as one HTML card — title bar, then one padded body.

    Lane 1 and the beat-1 shells are built this way. Lanes 2 and 3 hold
    native widgets, so their live path builds the same card with
    lane_container() instead; the CSS gives both the same padding.
    """
    shell_class = " lane-shell" if shell else ""
    return f'<div class="lane{shell_class}">{title}<div class="lane-body">{body}</div></div>'


@contextmanager
def lane_container(key, title_html):
    """The widget-bearing twin of lane_html().

    st.radio / st.button / st.text_area cannot be nested inside an
    st.markdown string, so lanes 2 and 3 are many separate Streamlit calls.
    A keyed st.container draws the card from the outside and a second keyed
    container supplies .lane-body's padding, so the gap from the navy bar to
    the first line of text is the same number in every lane no matter how
    many calls build the rest. gap=None joins the bar to the body; gap=10
    gives the body the same rhythm the HTML fragments carry in lane 1.
    """
    with st.container(key=f"lanecard_{key}", gap=None):
        st.markdown(title_html, unsafe_allow_html=True)
        with st.container(key=f"lanebody_{key}", gap=10):
            yield


def option(incident, option_id):
    return next(opt for opt in incident["options"] if opt["id"] == option_id)


def tablets_at_risk(incident):
    return int(incident["tablets_per_hour"] * incident["mean_hours_to_forced_shutdown"])


def dollars_at_risk(incident):
    return int(tablets_at_risk(incident) / 1000 * incident["contribution_margin_per_1000"])


# The dev switcher's fixtures, in demo order. 2 (ambiguous) is deliberately
# not here — it exists to prove confidence varies and is exercised by the
# tests, not by the demo. 4 and 5 are built from the team's real tool output,
# so the label says so: they are the answer to "is this only a mockup?".
FIXTURE_LABELS = {
    1: "1 — clean (demo)",
    3: "3 — empty retrieval",
    4: "4 — vibration bearing (real feed)",
    5: "5 — sticking/picking (real feed)",
}


def render_sidebar():
    st.sidebar.markdown('<div class="sidenav-brand">Pill FactoryOps</div>', unsafe_allow_html=True)
    for group, items in NAV:
        st.sidebar.markdown(f'<div class="sidenav-group">{group}</div>', unsafe_allow_html=True)
        for item in items:
            if item == LIVE_MACHINE:
                st.sidebar.markdown(f'<div class="sidenav-active">{item}</div>', unsafe_allow_html=True)
            else:
                st.sidebar.button(item, key=f"nav_{item}", use_container_width=True)
    st.sidebar.markdown('<div class="fixture-label">Demo fixture (dev)</div>', unsafe_allow_html=True)
    st.sidebar.radio(
        "Demo fixture (dev)",
        list(FIXTURE_LABELS),
        format_func=lambda n: FIXTURE_LABELS[n],
        key="fixture_n",
        label_visibility="collapsed",
    )


def cause_line(incident):
    return incident.get("likely_cause") or EMPTY_CAUSE


OUTCOME_LABELS = {
    "bearing": "bearing replacement",
    "align": "alignment correction",
}


def alternate_cause_line(incident):
    outcomes = incident.get("prior_outcomes") or []
    if not outcomes or not incident.get("likely_cause"):
        return ""
    counts = Counter(outcomes)
    majority_outcome, _ = counts.most_common(1)[0]
    minority = [(o, n) for o, n in counts.items() if o != majority_outcome]
    if not minority:
        return ""
    minority_outcome, minority_n = minority[0]

    def label(key):
        return OUTCOME_LABELS.get(key, key.capitalize())

    total = len(outcomes)
    return (
        f"Considered and set aside: {minority_n} of {total} similar past incidents on this "
        f"machine were resolved by {label(minority_outcome)} rather than {label(majority_outcome)} "
        f"— the minority outcome, so {label(majority_outcome)} remains the likely cause here."
    )


def retrieved_html(incident):
    chunks = incident.get("retrieved") or []
    if not chunks:
        return (
            '<div class="evidence-detail">'
            f'<p class="empty-retrieval">{EMPTY_RETRIEVAL}</p>'
            "</div>"
        )
    items = []
    for chunk in chunks:
        tier = chunk.get("tier", "")
        tier_class = f"tier-{tier.lower()}" if tier else "tier-t2"
        source = chunk.get("source", "")
        section = chunk.get("section", "")
        page = chunk.get("page", "")
        text = chunk.get("text", "")
        meta = f"{section} · p.&nbsp;{page}"
        items.append(
            f'<div class="retrieved-item">'
            f'<span class="tier-tag {tier_class}">{tier}</span>'
            f'<div><div class="retrieved-title">{source}</div>'
            f'<div class="retrieved-meta">{meta}</div>'
            f'<div class="retrieved-meta">{text}</div></div></div>'
        )
    return (
        '<div class="evidence-detail">'
        '<div class="eyebrow" style="margin-top:0;">Retrieved, Ranked by Relevance</div>'
        + "".join(items)
        + "</div>"
    )


def _join_fragments(*fragments):
    """Join HTML fragments, dropping empty ones.

    Joined with no separator so a dropped fragment never leaves a
    whitespace-only line inside a raw HTML block — Streamlit's markdown
    step reads that as a block break and splits the surrounding div.
    """
    return "".join(f for f in fragments if f)


def _muted_line(text, margin="6px 0 0"):
    return f'<p class="muted" style="margin:{margin};">{text}</p>' if text else ""


def _trim(value):
    """3 dp, no trailing zeros — 4.573 − 4.5 is 0.07299999999999951 in binary
    floating point and the panel must not print that at a QA reviewer."""
    return f"{round(value, 3):g}"


def _pct_delta(value, limit):
    return f"+{int(round((value - limit) / limit * 100))}%"


def _degree_delta(value, limit):
    return f"+{int(value - limit)}&nbsp;°C"


def _limit_reading(incident, value_field, limit_field, unit, violated, delta):
    """The reading, then its approved limit, then the over-limit delta — and
    the delta only when the gate actually counted this field as a violation.

    Red is this screen's word for "outside the approved limit" (§7), so a
    reading that is inside its limit — fixture 5's vibration and motor
    temperature are both real and both normal — shows the number and the
    limit and nothing else. Assuming the violation instead is what made the
    panel print "+-20%" in red on a healthy reading.
    """
    reading = f'{incident[value_field]}&nbsp;{unit} · limit {incident[limit_field]}&nbsp;{unit}'
    if not violated:
        return reading
    return f'{reading} · <span class="delta-bad">{delta(incident[value_field], incident[limit_field])}</span>'


def _vibration_reading(incident, violated):
    return _limit_reading(incident, "vibration_mm_s", "max_vibration_mm_s", "mm/s", violated, _pct_delta)


def _temperature_reading(incident, violated):
    return _limit_reading(incident, "motor_temperature_c", "max_motor_temperature_c", "°C", violated, _degree_delta)


def _ejection_reading(incident, violated):
    return _limit_reading(incident, "ejection_force_kn", "max_ejection_force_kn", "kN", violated, _pct_delta)


def _weight_rsd_reading(incident, violated):
    # Value only, deliberately: RSD is a spread, not a reading against an
    # approved ceiling, so it has never carried a limit or a violation flag.
    return f'{incident["tablet_weight_rsd_pct"]}%'


def _thickness_reading(incident, violated):
    reading = (
        f'{incident["tablet_thickness_mm"]}&nbsp;mm · '
        f'target {incident["target_tablet_thickness_mm"]}&nbsp;mm ± '
        f'{incident["tablet_thickness_tolerance_mm"]}&nbsp;mm'
    )
    if not violated:
        return reading
    deviation = _trim(abs(incident["tablet_thickness_mm"] - incident["target_tablet_thickness_mm"]))
    return f'{reading} · <span class="delta-bad">±{deviation}&nbsp;mm</span>'


# (label, fields the row needs, policy_gate violation key, reading builder).
# Ordered: the three readings every press incident carries, then the ones a
# specific failure mode brings with it. A row appears only if the incident
# actually holds its fields, and its red badge comes from
# policy_gate.limit_violations() — so the panel shows what this incident's
# decision rests on rather than the same three parameters every time. Sticking
# or picking (fixture 5) is diagnosed by ejection force and tablet thickness;
# showing vibration and motor temperature alone would have been two irrelevant
# numbers where the evidence should be.
EVIDENCE_ROWS = (
    ("Vibration", ("vibration_mm_s", "max_vibration_mm_s"), "vibration_mm_s", _vibration_reading),
    ("Motor temperature", ("motor_temperature_c", "max_motor_temperature_c"), "motor_temperature_c", _temperature_reading),
    ("Tablet weight RSD", ("tablet_weight_rsd_pct",), None, _weight_rsd_reading),
    ("Ejection force", ("ejection_force_kn", "max_ejection_force_kn"), "ejection_force_kn", _ejection_reading),
    (
        "Tablet thickness",
        ("tablet_thickness_mm", "target_tablet_thickness_mm", "tablet_thickness_tolerance_mm"),
        "tablet_thickness_mm",
        _thickness_reading,
    ),
)


def evidence_rows_html(incident):
    """The Evidence rows for whatever CQA parameters this incident carries.

    Through _join_fragments, and the caller keeps the result inline on the
    line above <details>: a row that does not apply must not leave a
    whitespace-only line inside the raw HTML block — that is exactly what put
    a literal </div> on screen on an earlier pass.
    """
    violations = limit_violations(incident)
    return _join_fragments(
        *(
            f'<div class="evidence-row"><span>{label}</span>'
            f'<span>{reading(incident, key in violations)}</span></div>'
            for label, fields, key, reading in EVIDENCE_ROWS
            if all(incident.get(field) is not None for field in fields)
        )
    )


def gate_lane_html(incident, gate, show_next=True):
    cause = cause_line(incident)
    basis = ", ".join(incident["confidence_basis"])
    confidence_block = _join_fragments(
        f'<p class="muted">{basis}</p>',
        _muted_line(alternate_cause_line(incident), margin="6px 0 12px"),
    )
    decision_block = _join_fragments(
        f'<div class="gate-decision-value">{decision_label(gate)}</div>',
        f'<div class="gate-decision-basis">{" · ".join(gate["regulatory_basis"])}</div>',
        _muted_line(decision_gloss(gate)),
        '<div class="next-step">Next: recommended intervention →</div>' if show_next else "",
    )
    body = f"""
    <div class="eyebrow">Likely Cause</div>
    <div class="cause-headline">{cause}</div>
    <p style="font-weight:600;color:#374151;margin:6px 0 0;">Confidence: {incident["confidence"].title()}</p>
    {confidence_block}
    <div class="evidence-header">
      <div class="eyebrow" style="margin-top:0;">Evidence</div>
    </div>{evidence_rows_html(incident)}
    <details class="evidence-disclosure">
      <summary>Review Evidence</summary>
      {retrieved_html(incident)}
    </details>
    <div class="eyebrow">Impact</div>
    <div class="tile-wrap">
      <div class="tile"><div class="tile-number">{tablets_at_risk(incident):,}</div><div class="tile-caption">tablets at risk</div></div>
      <div class="tile"><div class="tile-number">${dollars_at_risk(incident):,}</div><div class="tile-caption">production contribution at risk</div></div>
    </div>
    <div class="assumption">Assumes ${incident["contribution_margin_per_1000"]} contribution margin per 1,000 tablets · {incident["tablets_per_hour"]:,} tablets/hr · {incident["mean_hours_to_forced_shutdown"]} hr estimated downtime</div>
    <div class="quality-flag">Batch {incident["batch_id"]} flagged for QA disposition</div>
    <div class="eyebrow">Gate Decision</div>
    <div class="gate-decision">{decision_block}</div>
"""
    return lane_html(lane_title_html(1, "Policy Gate"), body)


def options_shell_html(incident):
    c = option(incident, "C")
    return lane_html(
        options_title_html(shell=True),
        f'<p class="shell-line">C recommended · {c["gamp_change_type"]}</p>'
        '<p class="shell-hint">Opens with approval. One step.</p>',
        shell=True,
    )


def approval_shell_html():
    return lane_html(
        approval_title_html(),
        '<p class="shell-line">2 signatures required</p>'
        '<p class="shell-hint">Supervisor approved, then QA reviewed.</p>',
        shell=True,
    )


CHANGE_TAG_CLASS = {
    "Deviation": "class-deviation",
    "Temporary Change": "class-temporary",
    "Repair": "class-repair",
    "Standard/Routine": "class-repair",
}

OPTION_DETAIL = {
    # Deliberately parameter-agnostic — this incident's evidence panel is
    # what says which reading is over limit; naming just one here would be
    # wrong on any incident with more than one (fixture_4) or a different
    # one entirely (fixture_5's ejection force / thickness, not vibration).
    "A": "Continuing to run outside the approved limit is a deviation: it can proceed only once it's recorded, justified and signed for. Not recommended — the underlying cause goes unaddressed.",
    "B": "Slows the turret to reduce mechanical stress until the planned repair, at an estimated {loss}% output loss. It only qualifies as a Temporary Change if rollback is reviewed by {rollback} — without that, the gate denies this option.",
    # {description} is this option's own incident-specific text (e.g.
    # "Controlled shutdown + bearing inspection" or "Pause production +
    # inspect tooling") and {downtime} is the incident's own estimated
    # downtime figure — the same number the impact tile's assumption line
    # already states, so this can't quote a different figure than the rest
    # of the screen.
    "C": "{description} — the specification doesn't change, so GAMP classifies it as pre-approved. Estimated intervention: {downtime}&nbsp;hr of downtime before the line resumes.",
}


def decision_label(gate):
    d = gate["decision"]
    if d == "HUMAN_APPROVAL":
        return "HUMAN_APPROVAL required"
    if d == "DENY":
        return "DENY — autonomous path"
    return "ALLOW"


def decision_gloss(gate):
    if gate["decision"] != "HUMAN_APPROVAL":
        return ""
    if gate.get("change_type") == "Deviation":
        # 21 CFR 211.100(b): a deviation is "recorded and justified" by a
        # signature, not waved through and not silently refused.
        return "Running outside the approved limit has to be signed for and justified before the line continues."
    return "Needs sign-off from both the operating unit and the quality unit before this intervention proceeds."


def options_title_html(shell=False):
    # "Supervisor", not "Maintenance Supervisor": the full role name is two
    # lines wide in this column and wrapped the navy bar, leaving lane 2's
    # bar 19px taller than lanes 1 and 3. The full name is still on screen
    # in the signature block and in the locked note under this title.
    # The beat-1 shell carries no pill — nothing is owned until the lane opens.
    return lane_title_html(2, "Intervention Options", owner="" if shell else "Supervisor")


def approval_title_html():
    return lane_title_html(3, "Approval Workflow")


def option_card_html(incident, option_id, gate, expanded, chosen=False, show_head=True):
    opt = option(incident, option_id)
    tag_class = CHANGE_TAG_CLASS.get(opt["gamp_change_type"], "class-repair")
    tag = f'<span class="class-tag {tag_class}">{opt["gamp_change_type"]}</span>'
    recommended = ' <span class="recommended">Recommended</span>' if option_id == "C" else ""
    # Conditional fragments stay inline (never alone on a line) and go through
    # _join_fragments so an empty one cannot split the surrounding div.
    chosen_mark = ' <span class="recommended">Chosen</span>' if chosen else ""
    if not expanded:
        rollback = opt.get("rollback_review_by")
        extra = f'<span class="rollback-inline">rollback by {rollback}</span>' if rollback else ""
        line_class = " option-line-chosen" if chosen else ""
        marks = _join_fragments(extra, tag, chosen_mark)
        return (
            f'<div class="option-line{line_class}"><span>{option_id} · {opt["description"]}</span>'
            f'<span>{marks}</span></div>'
        )
    detail = OPTION_DETAIL.get(option_id, "").format(
        loss=opt.get("output_loss_pct", ""),
        rollback=opt.get("rollback_review_by", ""),
        description=opt.get("description", ""),
        downtime=incident.get("mean_hours_to_forced_shutdown", ""),
    )
    # The chosen option's verdict is the screen's verdict: the gate evaluates
    # whatever is selected, so this box would repeat word for word what the
    # foot of lane 1 and the head of lane 3 already say, in the narrowest
    # column. The other options keep theirs, where it answers a question this
    # screen does not otherwise answer — what happens if I pick that instead.
    verdict = "" if chosen else (
        f'<div class="gate-decision">'
        f'<div class="gate-decision-value">{decision_label(gate)}</div>'
        f'<div class="gate-decision-basis">{" · ".join(gate["regulatory_basis"])}</div></div>'
    )
    marks = _join_fragments(tag, recommended, chosen_mark)
    # Inside a disclosure the summary line already carries the title and the
    # marks, so the card's own head is not rendered at all. It used to be
    # emitted and hidden in CSS, which put a second "Chosen" in the markup.
    head = (
        '<div class="option-card-head">'
        f'<span class="option-title">{option_id} · {opt["description"]}</span>'
        f'<span>{marks}</span></div>'
    ) if show_head else ""
    return _join_fragments(
        '<div class="option-card">',
        head,
        f'<p class="option-detail">{detail}</p>',
        verdict,
        "</div>",
    )


def option_row_html(incident, option_id, gate, chosen=False):
    """One row of the options lane.

    C is always fully expanded (spec 5.3: "C never collapses"). A and B are
    native <details> disclosures — reading one is not choosing one, so clicking
    them never reruns the script or touches selected_option. The chosen option
    starts open; that is an initial hint, not a lock.
    """
    if option_id == "C":
        return option_card_html(incident, option_id, gate, expanded=True, chosen=chosen)
    summary = option_card_html(incident, option_id, gate, expanded=False, chosen=chosen)
    body = option_card_html(incident, option_id, gate, expanded=True, chosen=chosen, show_head=False)
    return _join_fragments(
        f'<details class="option-disclosure"{" open" if chosen else ""}>',
        f"<summary>{summary}</summary>",
        body,
        "</details>",
    )


def options_rows_html(incident, selected="C"):
    return "".join(
        option_row_html(incident, oid, evaluate(incident, option(incident, oid)), chosen=(oid == selected))
        for oid in ("A", "B", "C")
    )


def options_heading_html(locked=False, note=""):
    """The lane's first line: what this lane is for, and why it may be locked.

    First in the body, so it carries no top margin of its own — the lane's
    padding is the whole gap, the same one lane 1 shows.
    """
    return _join_fragments(
        f'<div class="eyebrow" style="margin-top:0;">{"Chosen" if locked else "Choose"} Intervention</div>',
        _muted_line(note, margin="4px 0 0"),
    )


def options_lane_html(incident, selected="C"):
    """Lane 2 as one HTML string — the same title, heading and rows the live
    path renders, minus the radio, which cannot exist inside a markdown
    string. Kept in step with render_options_lane() deliberately: the two
    had drifted into different structures, and the static one is what the
    tests see."""
    return lane_html(
        options_title_html(),
        options_heading_html() + options_rows_html(incident, selected),
    )


def render_options_lane(incident, record, active_role):
    locked = bool(record["signatures"]) or active_role != ROLE_SUPERVISOR
    selected = st.session_state.get("selected_option", "C")
    note = ""
    if locked:
        note = (
            "Locked — the intervention cannot change once it has been signed for."
            if record["signatures"]
            else "Only the Maintenance Supervisor chooses the intervention."
        )
    with lane_container("options", options_title_html()):
        st.markdown(options_heading_html(locked, note), unsafe_allow_html=True)
        # Letters only. The rows below already name every option, its change
        # type and its rollback time; a full label here printed all three a
        # second time, so lane 2 listed six things where it has three.
        st.radio(
            "Choose intervention",
            ["A", "B", "C"],
            # Explicit index: this radio is first instantiated on a rerun (two-beat
            # screen), and Streamlit then paints the marker on index 0 even though
            # session_state already holds C — the dot would contradict the lane.
            index=["A", "B", "C"].index(selected),
            key="selected_option",
            disabled=locked,
            horizontal=True,
            label_visibility="collapsed",
        )
        # Every option's full detail is readable regardless of which one is selected
        # or who is acting — peek without picking. Only the radio above is lockable.
        st.markdown(options_rows_html(incident, selected), unsafe_allow_html=True)


def approval_intro_html(gate):
    """Lane 3's first line: the verdict, then the rule it rests on.

    The title bar and the body's padding belong to the lane wrapper now —
    this returns the content only, so the same fragment can sit inside the
    HTML lane (tests, static view) and inside the live st.container lane.

    Every citation, not just the first: a deviation on a flagged batch is
    carried by two rules (211.100(b) and 211.22) and showing one hides why
    the quality unit is on the signature list at all.
    """
    basis = " · ".join(gate["regulatory_basis"]) or "21 CFR 211.100(a)"
    headline = (
        "Deviation must be recorded and justified"
        if gate.get("change_type") == "Deviation"
        else "Human approval required"
    )
    return f'<div class="basis-row">{headline}</div><div class="cfr">{basis}</div>'


def _block_class(active_role, block_role):
    if active_role == block_role:
        return " sig-owned"
    if active_role is not None:
        return " sig-waiting"
    return ""


SUPERVISOR_COPY_DEVIATION = {
    "meaning": "signs to acknowledge the deviation and take responsibility for continuing outside the approved limit",
    "confirmed": "Deviation acknowledged",
    "button": "Acknowledge Deviation",
    "waiting_for": "acknowledge the deviation",
}
SUPERVISOR_COPY_INTERVENTION = {
    "meaning": "signs to approve the intervention, clearing the operating unit to carry it out",
    "confirmed": "Intervention approved",
    "button": "Approve Intervention",
    "waiting_for": "approve the intervention",
}


def supervisor_copy(record):
    """What the Supervisor is actually signing, in words.

    A Deviation is not an intervention — nothing is repaired and nothing is
    changed — so this block cannot say "approve". Source of truth is
    approval.supervisor_meaning(), so the screen and the signature on the
    record can never disagree about what was signed.
    """
    if supervisor_meaning(record) == MEANING_SUPERVISOR_DEVIATION:
        return SUPERVISOR_COPY_DEVIATION
    return SUPERVISOR_COPY_INTERVENTION


def supervisor_block_html(record, active_role=None):
    signed = next((sig for sig in record["signatures"] if sig["role"] == ROLE_SUPERVISOR), None)
    cls = _block_class(active_role, ROLE_SUPERVISOR)
    copy = supervisor_copy(record)
    if signed:
        clock = signed["timestamp"][11:16] if "T" in signed["timestamp"] else signed["timestamp"]
        return f"""
    <div class="sig-block{cls}">
      <div class="sig-role">Maintenance Supervisor <span class="owner-tag">· operating unit</span></div>
      <div class="sig-meaning">{copy["meaning"]}</div>
      <div class="sig-confirmed">{copy["confirmed"]} · {clock} · {signed["name"]}</div>
    </div>
"""
    return f"""
    <div class="sig-block{cls}">
      <div class="sig-role">Maintenance Supervisor <span class="owner-tag">· operating unit</span></div>
      <div class="sig-meaning">{copy["meaning"]}</div>
    </div>
"""


def qa_signature(record):
    return next((sig for sig in record["signatures"] if sig["role"] == ROLE_QA), None)


def qa_denial_reason(record):
    sig = qa_signature(record)
    if sig and sig.get("decision") == "deny":
        return (sig.get("reason") or "").strip()
    return ""


def qa_block_html(record, active_role=None):
    signed = qa_signature(record)
    cls = _block_class(active_role, ROLE_QA)
    if signed:
        clock = signed["timestamp"][11:16] if "T" in signed["timestamp"] else signed["timestamp"]
        # QA's word is never "approved" — 21 CFR 11.50 wants each signature's
        # meaning stated, and the quality unit reviews or denies. It never
        # approves the intervention; that is the Supervisor's act.
        denied = signed.get("decision") == "deny"
        confirmed = "Batch disposition denied" if denied else "Batch disposition reviewed"
        denied_cls = " sig-denied" if denied else ""
        return f"""
    <div class="sig-block{cls}">
      <div class="sig-role">Quality Assurance <span class="owner-tag">· quality unit</span></div>
      <div class="sig-meaning">signs to review batch disposition and decide whether the batch can be released — or to deny it, with a reason</div>
      <div class="sig-confirmed{denied_cls}">{confirmed} · {clock} · {signed["name"]}</div>
    </div>
"""
    return f"""
    <div class="sig-block{cls}">
      <div class="sig-role">Quality Assurance <span class="owner-tag">· quality unit</span></div>
      <div class="sig-meaning">signs to review batch disposition and decide whether the batch can be released — or to deny it, with a reason</div>
    </div>
"""


# A recovered value is computed from THIS incident's own limit/target, never
# a fixed number — the old hardcoded "4.3 mm/s" was still above fixture_4's
# real 1.5 mm/s limit, which made "resolved" show a reading that would still
# fail. gt-limit checks recover to a value comfortably under the limit;
# target/tolerance checks recover to the target itself.
def _recovered_from_limit(limit):
    return _trim(round(limit * 0.65, 3))


RESOLVED_ROWS = {
    "vibration_mm_s": ("Vibration", "mm/s", lambda i: _recovered_from_limit(i["max_vibration_mm_s"])),
    "motor_temperature_c": ("Motor temperature", "°C", lambda i: _recovered_from_limit(i["max_motor_temperature_c"])),
    "ejection_force_kn": ("Ejection force", "kN", lambda i: _recovered_from_limit(i["max_ejection_force_kn"])),
    "tablet_thickness_mm": ("Tablet thickness", "mm", lambda i: _trim(i["target_tablet_thickness_mm"])),
    "tablet_weight_mean_mg": ("Tablet weight", "mg", lambda i: _trim(i["labeled_weight_mg"])),
}


def resolved_rows_html(incident):
    """One before → after line per parameter this incident's gate actually
    flagged, plus tablet weight RSD as a standing quality confirmation (it
    has never carried a limit of its own — see _weight_rsd_reading)."""
    violations = limit_violations(incident)
    rows = [
        f'<div>{label}&nbsp; <span class="arrow-from">{incident[key]}</span> → '
        f'<span class="arrow-to">{after_fn(incident)}</span>&nbsp;{unit}</div>'
        for key, (label, unit, after_fn) in RESOLVED_ROWS.items()
        if key in violations
    ]
    if incident.get("tablet_weight_rsd_pct") is not None:
        rows.append(
            f'<div>Weight RSD&nbsp; <span class="arrow-from">{incident["tablet_weight_rsd_pct"]}%</span> → '
            '<span class="arrow-to">1.1%</span></div>'
        )
    return "".join(rows)


def resolved_html(incident):
    # rows is interpolated inline, never alone on its own line: an empty
    # result (no violated field this fixture set exercises today, but the
    # function must stay correct if one ever did) must not leave a
    # whitespace-only line inside this raw HTML block.
    rows = resolved_rows_html(incident)
    return _join_fragments(
        '<div class="resolved-detail">',
        '<div class="eyebrow" style="margin-top:0;">Post-Intervention Verification</div>',
        '<div class="muted" style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;">',
        rows,
        "</div>",
        '<p class="muted" style="margin:8px 0 0;">Maintenance recommendation: re-verify at next scheduled service.</p>',
        f'<div class="quality-flag">Batch {incident["batch_id"]} remains flagged for QA disposition</div>',
        "</div>",
    )


def hold_html(incident, record):
    """The denied outcome — deliberately NOT resolved_html.

    resolved_html shows post-intervention telemetry. On a denial nothing was
    performed and nothing was measured, so those numbers would be invented.
    The only new fact here is the reason QA typed, so that is all this shows.

    Every conditional fragment goes through _join_fragments: an empty value
    alone on a line inside a raw-HTML block is what produced the literal
    </div> regression on an earlier pass.
    """
    reason = qa_denial_reason(record)
    reason_block = (
        '<div class="eyebrow" style="margin-top:12px;">Reason Recorded By Quality Assurance</div>'
        f'<p class="hold-reason">{reason}</p>'
    ) if reason else ""
    return _join_fragments(
        '<div class="hold-detail">',
        '<div class="eyebrow" style="margin-top:0;">Batch On Hold</div>',
        '<p class="hold-reason">The quality unit denied the batch disposition. No intervention was '
        "performed and no post-intervention reading has been taken.</p>",
        reason_block,
        f'<div class="quality-flag">Batch {incident["batch_id"]} stays flagged for QA disposition</div>',
        "</div>",
    )


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


def approval_lane_html(gate, record=None):
    """Lane 3 as one HTML string — the same title, basis line and signature
    blocks the live path renders, minus the buttons, which cannot exist
    inside a markdown string.

    Built from the live fragments on purpose. The hand-written copy this
    replaced had drifted: it still said "signs to approve the intervention"
    while the screen had moved on to the longer, role-specific wording.
    """
    record = record or {"signatures": [], "change_type": gate.get("change_type")}
    return lane_html(
        approval_title_html(),
        approval_intro_html(gate) + supervisor_block_html(record) + qa_block_html(record),
    )


def header_html(incident):
    return (
        f'<span class="incident-id">{incident["incident_id"]}</span>'
        f'<span class="sim-tag">Simulated Plant Data</span>'
        f'<div class="subline">Rotary Tablet Press · Machine {incident["machine_id"]} · '
        f'Batch {incident["batch_id"]} · {incident["product"]}</div>'
    )


def status_html(record=None):
    # Three states, not two. A denial is terminal but it is not a resolution —
    # the incident is still open and the batch is still flagged.
    if record and is_on_hold(record):
        return '<div class="status-banner status-hold">Batch On Hold — Quality Assurance Denied the Disposition</div>'
    if record and is_resolved(record):
        return '<div class="status-banner status-resolved">Incident Resolved — Equipment Returned to Normal Range</div>'
    return '<div class="status-banner">Critical Equipment Incident — Human Approval Required</div>'


def init_record(incident, selected_option, gate):
    rec = st.session_state.get("record")
    incident_changed = rec is None or rec.get("incident_id") != incident["incident_id"]
    option_changed = rec is not None and rec.get("option_id") != selected_option["id"]
    if incident_changed or option_changed:
        st.session_state.record = new_record(incident, selected_option, gate)
        if incident_changed:
            st.session_state.action_open = False
    return st.session_state.record


def _hint(text):
    st.markdown(f'<div class="handoff-hint">{text}</div>', unsafe_allow_html=True)


def denial_lane_html(gate):
    # Reached only when the gate returns DENY. A Deviation on a live limit
    # violation no longer lands here — it has a signature path now — so this
    # copy has to speak for the remaining DENY cases (missing rollback date,
    # speed outside the qualified range, unclassifiable option).
    basis = " · ".join(gate["regulatory_basis"]) or "21 CFR 211.100(a)"
    return lane_html(
        approval_title_html(),
        f'<div class="basis-row" style="color:#dc2626;">Autonomous path denied</div>'
        f'<div class="cfr">{basis}</div>'
        '<p class="muted" style="margin:8px 0 0;">This option cannot be signed off on this screen — '
        "a required condition, such as a rollback review date or a qualified speed range, is missing "
        "or not met. It needs a change-control record instead; the gate has no signature path for it "
        "here.</p>",
    )


QA_DENY_NEEDS_REASON = (
    "This denial has no reason recorded, so nothing was signed. "
    "Type why the batch cannot be released in the box above, then press Deny again."
)


def render_qa_decision():
    """QA's two outcomes, as two separate controls (spec §8).

    21 CFR 211.22 gives the quality unit authority to approve *or reject*, so
    a single button was a rubber stamp. The denial carries a required reason —
    approval-forms-design: a rejection is never a bare click. The reason box
    sits with the Deny control, not with the review control, because only one
    of the two needs it.
    """
    if st.button("Review Batch Disposition", key="btn_qa", type="primary", use_container_width=True):
        sign_qa(st.session_state.record, decision="approve")
        resolve(st.session_state.record)
        st.rerun()
    # The label, the box and the Deny button are one group, tighter to each
    # other than to the Review control above — otherwise the reason box sits
    # equidistant between two buttons and it is not obvious which it belongs to.
    with st.container(key="qa_deny_group", gap=4):
        st.markdown('<div class="deny-label">Reason — required to deny</div>', unsafe_allow_html=True)
        st.text_area(
            "Reason for denial",
            key="qa_deny_reason",
            height=68,
            placeholder="Why can this batch not be released?",
            label_visibility="collapsed",
        )
        if st.button("Deny Batch Disposition", key="btn_qa_deny", use_container_width=True):
            reason = (st.session_state.get("qa_deny_reason") or "").strip()
            if not reason:
                # sign_qa already no-ops on an empty reason, but a no-op the user
                # can't see reads as a broken button. Mark it, name what is wrong,
                # name the fix — and leave QA able to act.
                st.warning(QA_DENY_NEEDS_REASON)
            else:
                # No resolve() here on purpose: a denial has no resolved outcome.
                # sign_qa moves the record straight to the quality-hold state.
                sign_qa(st.session_state.record, decision="deny", reason=reason)
                st.rerun()


def render_approval_lane(incident, gate, record, active_role):
    if gate["decision"] != "HUMAN_APPROVAL":
        st.markdown(denial_lane_html(gate), unsafe_allow_html=True)
        return
    copy = supervisor_copy(record)
    with lane_container("approval", approval_title_html()):
        st.markdown(approval_intro_html(gate), unsafe_allow_html=True)
        st.markdown(supervisor_block_html(record, active_role), unsafe_allow_html=True)
        if record["state"] == STATE_PRESENTED:
            if active_role == ROLE_SUPERVISOR and can_sign(record, ROLE_SUPERVISOR):
                if st.button(copy["button"], key="btn_supervisor", type="primary", use_container_width=True):
                    sign_supervisor(st.session_state.record)
                    st.rerun()
            elif active_role == ROLE_QA:
                _hint(f"Waiting for the Maintenance Supervisor to {copy['waiting_for']} before Quality Assurance can sign.")

        st.markdown(qa_block_html(record, active_role), unsafe_allow_html=True)
        if record["state"] == STATE_SUPERVISOR_SIGNED:
            if active_role == ROLE_QA and can_sign(record, ROLE_QA):
                render_qa_decision()
            elif active_role == ROLE_SUPERVISOR:
                _hint("Switch to Quality Assurance to review the batch disposition next.")

        if is_on_hold(record):
            st.markdown(hold_html(incident, record), unsafe_allow_html=True)
        elif is_resolved(record):
            st.markdown(resolved_html(incident), unsafe_allow_html=True)
        # audit_html is "" until the first signature. An empty markdown call
        # would still occupy a slot in the container's gap rhythm.
        if record["audit"]:
            st.markdown(audit_html(record), unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Pill FactoryOps — Incident Approval", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    render_sidebar()
    incident = load_fixture(st.session_state.get("fixture_n", 1))
    st.session_state.setdefault("selected_option", "C")
    selected_option = option(incident, st.session_state["selected_option"])
    gate = evaluate(incident, selected_option)
    record = init_record(incident, selected_option, gate)
    if is_resolved(record) or is_on_hold(record):
        st.session_state.action_open = True
    action_open = st.session_state.get("action_open", False)
    st.markdown(header_html(incident), unsafe_allow_html=True)
    st.markdown(status_html(record), unsafe_allow_html=True)

    active_role = ROLE_SUPERVISOR
    if action_open:
        st.markdown('<div class="role-label">Acting as (demo stand-in for two logged-in users)</div>', unsafe_allow_html=True)
        active_role = st.radio(
            "Acting as",
            [ROLE_SUPERVISOR, ROLE_QA],
            horizontal=True,
            key="active_role",
            label_visibility="collapsed",
        )

    col_gate, col_options, col_approval = st.columns([2, 1.3, 1.3])
    with col_gate:
        st.markdown(gate_lane_html(incident, gate, show_next=not action_open), unsafe_allow_html=True)
        if not action_open:
            if st.button("Next: recommended intervention", type="primary", use_container_width=True, key="btn_next"):
                st.session_state.action_open = True
                st.rerun()
    with col_options:
        if action_open:
            render_options_lane(incident, record, active_role)
        else:
            st.markdown(options_shell_html(incident), unsafe_allow_html=True)
    with col_approval:
        if action_open:
            render_approval_lane(incident, gate, record, active_role)
        else:
            st.markdown(approval_shell_html(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
