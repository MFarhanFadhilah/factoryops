ROLE_SUPERVISOR = "Maintenance Supervisor"
ROLE_QA = "Quality Assurance"

CHANGE_TYPES = ("Repair", "Temporary Change", "Deviation", "Standard/Routine")

DECISIONS = ("ALLOW", "DENY", "HUMAN_APPROVAL")


def classify(option):
    change_type = (option or {}).get("gamp_change_type")
    if change_type in CHANGE_TYPES:
        return change_type
    return None


# (measured field, approved-limit field, violation key) for every CQA-linked
# parameter checked by simple "outside its approved limit" (gt). Shared shape
# with app.py's evidence panel, so the gate and the screen read the same list
# of what this incident's decision actually rests on and can't drift apart —
# a new failure mode (e.g. ejection force for sticking/picking) is one row
# here, not a change to the gate's control flow.
CQA_LIMIT_CHECKS = (
    ("vibration_mm_s", "max_vibration_mm_s", "vibration_mm_s"),
    ("motor_temperature_c", "max_motor_temperature_c", "motor_temperature_c"),
    ("ejection_force_kn", "max_ejection_force_kn", "ejection_force_kn"),
)

# (measured field, target field, tolerance field, violation key) for
# CQA-linked parameters checked by absolute deviation from a target instead
# of a plain ceiling.
CQA_TOLERANCE_CHECKS = (
    ("tablet_weight_mean_mg", "labeled_weight_mg", "tablet_weight_tolerance_pct", "tablet_weight_mean_mg", True),
    ("tablet_thickness_mm", "target_tablet_thickness_mm", "tablet_thickness_tolerance_mm", "tablet_thickness_mm", False),
)


def limit_violations(incident):
    violations = []
    for value_field, limit_field, key in CQA_LIMIT_CHECKS:
        value = incident.get(value_field)
        limit = incident.get(limit_field)
        if value is not None and limit is not None and value > limit:
            violations.append(key)
    for value_field, target_field, tolerance_field, key, tolerance_is_pct in CQA_TOLERANCE_CHECKS:
        value = incident.get(value_field)
        target = incident.get(target_field)
        tolerance = incident.get(tolerance_field)
        if value is None or target is None or tolerance is None:
            continue
        deviation = abs(value - target)
        if tolerance_is_pct:
            deviation = deviation / target * 100
        if deviation > tolerance:
            violations.append(key)
    return violations


def _speed_in_qualified_range(incident, proposed_rpm):
    qualified = incident.get("qualified_speed_range_rpm")
    if not qualified or len(qualified) != 2 or proposed_rpm is None:
        return False
    low, high = qualified
    return low <= proposed_rpm <= high


def _result(decision, approvers, basis, change_type, quality_flag):
    return {
        "decision": decision,
        "required_approvers": list(approvers),
        "regulatory_basis": list(basis),
        "change_type": change_type,
        "quality_flag": quality_flag,
    }


def evaluate(incident, option):
    change_type = classify(option)
    quality_flag = bool(incident.get("batch_id")) and bool(limit_violations(incident))

    if change_type is None:
        return _result("DENY", [], ["GAMP 5 App O6 p.307"], None, quality_flag)

    if change_type == "Standard/Routine":
        return _result(
            "ALLOW",
            [],
            ["GAMP 5 App O6 p.307"],
            change_type,
            quality_flag,
        )

    if change_type == "Deviation" and limit_violations(incident):
        # Autonomous continuation is denied (rule 1) — but a human choosing to
        # continue is not the same thing. 21 CFR 211.100(b) requires the
        # deviation to be "recorded and justified," which is a signed act, not
        # a dead end. The operating unit signs; the quality unit reviews too
        # whenever a CQA-linked parameter has moved (rule 5), same as Repair.
        approvers = [ROLE_SUPERVISOR]
        basis = ["21 CFR 211.100(b)"]
        if quality_flag:
            approvers.append(ROLE_QA)
            basis.append("21 CFR 211.22")
        return _result("HUMAN_APPROVAL", approvers, basis, change_type, quality_flag)

    proposed_rpm = option.get("proposed_turret_speed_rpm")
    if proposed_rpm is not None and not _speed_in_qualified_range(incident, proposed_rpm):
        return _result(
            "DENY",
            [],
            ["EU Annex 11 ¶10", "21 CFR 211.68(b)"],
            change_type,
            quality_flag,
        )

    if change_type == "Temporary Change":
        if not option.get("rollback_review_by"):
            return _result(
                "DENY",
                [],
                ["GAMP 5 App O6 p.307", "21 CFR 211.100(a)"],
                change_type,
                quality_flag,
            )
        if proposed_rpm is None or not _speed_in_qualified_range(incident, proposed_rpm):
            return _result(
                "DENY",
                [],
                ["GAMP 5 App O6 p.307", "21 CFR 211.100(a)"],
                change_type,
                quality_flag,
            )
        return _result(
            "HUMAN_APPROVAL",
            [ROLE_SUPERVISOR, ROLE_QA],
            ["GAMP 5 App O6 p.307", "21 CFR 211.100(a)"],
            change_type,
            quality_flag,
        )

    if change_type == "Repair" and not option.get("changes_specification"):
        approvers = [ROLE_SUPERVISOR]
        basis = ["GAMP 5 App O6 p.307", "21 CFR 211.68(a)"]
        if quality_flag:
            approvers.append(ROLE_QA)
            basis.append("21 CFR 211.22")
        return _result("HUMAN_APPROVAL", approvers, basis, change_type, quality_flag)

    return _result("DENY", [], ["21 CFR 211.100(a)"], change_type, quality_flag)


def signatures_satisfy(required_approvers, signatures):
    signed_roles = {entry.get("role") for entry in signatures}
    return all(role in signed_roles for role in required_approvers)
