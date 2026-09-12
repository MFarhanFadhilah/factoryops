ROLE_SUPERVISOR = "Maintenance Supervisor"
ROLE_QA = "Quality Assurance"

CHANGE_TYPES = ("Repair", "Temporary Change", "Deviation", "Standard/Routine")

DECISIONS = ("ALLOW", "DENY", "HUMAN_APPROVAL")


def classify(option):
    change_type = (option or {}).get("gamp_change_type")
    if change_type in CHANGE_TYPES:
        return change_type
    return None


def limit_violations(incident):
    violations = []
    vibration = incident.get("vibration_mm_s")
    max_vibration = incident.get("max_vibration_mm_s")
    if vibration is not None and max_vibration is not None and vibration > max_vibration:
        violations.append("vibration_mm_s")
    temperature = incident.get("motor_temperature_c")
    max_temperature = incident.get("max_motor_temperature_c")
    if temperature is not None and max_temperature is not None and temperature > max_temperature:
        violations.append("motor_temperature_c")
    mean_mg = incident.get("tablet_weight_mean_mg")
    labeled = incident.get("labeled_weight_mg")
    tolerance = incident.get("tablet_weight_tolerance_pct")
    if mean_mg is not None and labeled is not None and tolerance is not None:
        delta_pct = abs(mean_mg - labeled) / labeled * 100
        if delta_pct > tolerance:
            violations.append("tablet_weight_mean_mg")
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
        return _result(
            "DENY",
            [],
            ["21 CFR 211.100(b)"],
            change_type,
            quality_flag,
        )

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
