#!/usr/bin/env python3
"""
VeriCore v3.2 – Device Diagnostic & Repair Decision Engine
============================================================

Platforms:
    • iPhone / iOS
    • Android

v3.1 focuses on:
    • Better iOS storage detection
    • Deeper iOS battery diagnostics
    • Battery health / cycle / capacity extraction when exposed
    • Device age calculation
    • IMEI / network information where available
    • Better component evidence
    • Separate automated verification and functional-test scores
    • Inspection completeness
    • Improved repair decision engine
    • VeriCore certificate generation
    • JSON technical report

IMPORTANT:
    VeriCore never claims a component is original merely because
    the device communicates correctly.

    Hardware originality requires evidence. Where the operating
    system does not expose enough information, VeriCore reports:

        VERIFIED
        LIKELY_ORIGINAL
        UNCERTAIN
        REPLACEMENT_SUSPECTED
        MANUAL_TEST_REQUIRED
        NOT_AVAILABLE

    "MANUAL_TEST_REQUIRED" does NOT mean that the component failed.
"""

import subprocess
import json
import re
import hashlib
import uuid
import argparse
from shutil import which
from datetime import datetime


VERICORE_VERSION = "3.2"


# ============================================================
# COMMAND / UTILITY FUNCTIONS
# ============================================================

def run_cmd(cmd, timeout=20):
    """
    Safely execute a command.

    Returns stdout on success, otherwise None.
    """
    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )

        if process.returncode != 0:
            return None

        return process.stdout.strip()

    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError
    ):
        return None


def command_exists(command):
    return which(command) is not None


def safe_int(value):
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def safe_float(value):
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def clean_value(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def human_gb(value):
    """
    Convert bytes to GB.

    Handles both numeric values and values such as:
        256000000000
        256000000000 Bytes
    """
    if value is None:
        return "unreadable"

    value = str(value).strip()

    match = re.search(r"(\d+)", value)

    if not match:
        return "unreadable"

    try:
        bytes_value = int(match.group(1))
        return f"{round(bytes_value / (1024 ** 3))} GB"
    except (ValueError, TypeError):
        return "unreadable"


def generate_certificate_id():
    year = datetime.now().year
    random_part = uuid.uuid4().hex[:8].upper()

    return f"VC-{year}-{random_part}"


def generate_device_fingerprint(*values):
    values = [
        str(value).strip()
        for value in values
        if value not in (None, "", "unreadable")
    ]

    if not values:
        return None

    raw = "|".join(values)

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:24].upper()


def first_available(data, keys):
    """
    Return the first usable value from a dictionary.
    """
    for key in keys:
        value = data.get(key)

        if value not in (None, "", "unreadable"):
            return value

    return None


# ============================================================
# iOS MODEL DATABASE
# ============================================================

IPHONE_MODELS = {

    # iPhone 11
    "iPhone12,1": "iPhone 11",
    "iPhone12,3": "iPhone 11 Pro",
    "iPhone12,5": "iPhone 11 Pro Max",

    # iPhone SE 2
    "iPhone12,8": "iPhone SE (2nd generation)",

    # iPhone 12
    "iPhone13,1": "iPhone 12 mini",
    "iPhone13,2": "iPhone 12",
    "iPhone13,3": "iPhone 12 Pro",
    "iPhone13,4": "iPhone 12 Pro Max",

    # iPhone 13
    "iPhone14,4": "iPhone 13 mini",
    "iPhone14,5": "iPhone 13",
    "iPhone14,2": "iPhone 13 Pro",
    "iPhone14,3": "iPhone 13 Pro Max",

    # iPhone SE 3
    "iPhone14,6": "iPhone SE (3rd generation)",

    # iPhone 14
    "iPhone14,7": "iPhone 14",
    "iPhone14,8": "iPhone 14 Plus",
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",

    # iPhone 15
    "iPhone15,4": "iPhone 15",
    "iPhone15,5": "iPhone 15 Plus",
    "iPhone16,1": "iPhone 15 Pro",
    "iPhone16,2": "iPhone 15 Pro Max",

    # iPhone 16
    "iPhone17,3": "iPhone 16",
    "iPhone17,4": "iPhone 16 Plus",
    "iPhone17,1": "iPhone 16 Pro",
    "iPhone17,2": "iPhone 16 Pro Max",

    # iPhone 16e
    "iPhone17,5": "iPhone 16e",

    # Newer devices can be added as Apple identifiers become known.
}


# ============================================================
# VERICORE DEVICE REFERENCE DATABASE
# ============================================================

# Reference values are model-level reference data, not measurements.
DEVICE_REFERENCE_DATABASE = {
    "iPhone12,1": {"battery_capacity_mAh": 3110, "charging_max_w": 18, "battery_life_cycles": 500},
    "iPhone12,3": {"battery_capacity_mAh": 3046, "charging_max_w": 18, "battery_life_cycles": 500},
    "iPhone12,5": {"battery_capacity_mAh": 3969, "charging_max_w": 18, "battery_life_cycles": 500},
    "iPhone13,1": {"battery_capacity_mAh": 2227, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone13,2": {"battery_capacity_mAh": 2815, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone13,3": {"battery_capacity_mAh": 3095, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone13,4": {"battery_capacity_mAh": 3687, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone14,4": {"battery_capacity_mAh": 2406, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone14,5": {"battery_capacity_mAh": 3227, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone14,2": {"battery_capacity_mAh": 3095, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone14,3": {"battery_capacity_mAh": 4352, "charging_max_w": 27, "battery_life_cycles": 500},
    "iPhone14,6": {"battery_capacity_mAh": 2018, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone14,7": {"battery_capacity_mAh": 3279, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone14,8": {"battery_capacity_mAh": 4325, "charging_max_w": 20, "battery_life_cycles": 500},
    "iPhone15,2": {"battery_capacity_mAh": 3200, "charging_max_w": 27, "battery_life_cycles": 500},
    "iPhone15,3": {"battery_capacity_mAh": 4323, "charging_max_w": 27, "battery_life_cycles": 500},
    "iPhone15,4": {"battery_capacity_mAh": 3349, "charging_max_w": 27, "battery_life_cycles": 1000},
    "iPhone15,5": {"battery_capacity_mAh": 4383, "charging_max_w": 27, "battery_life_cycles": 1000},
    "iPhone16,1": {"battery_capacity_mAh": 3274, "charging_max_w": 27, "battery_life_cycles": 1000},
    "iPhone16,2": {"battery_capacity_mAh": 4422, "charging_max_w": 27, "battery_life_cycles": 1000},
    "iPhone17,3": {"battery_capacity_mAh": 3561, "charging_max_w": 45, "battery_life_cycles": 1000},
    "iPhone17,4": {"battery_capacity_mAh": 4674, "charging_max_w": 45, "battery_life_cycles": 1000},
    "iPhone17,1": {"battery_capacity_mAh": 3582, "charging_max_w": 45, "battery_life_cycles": 1000},
    "iPhone17,2": {"battery_capacity_mAh": 4685, "charging_max_w": 45, "battery_life_cycles": 1000},
    "iPhone17,5": {"battery_capacity_mAh": 4005, "charging_max_w": 27, "battery_life_cycles": 1000},
}


def get_reference_profile(platform, model_identifier=None, model_name=None):
    if platform == "iOS" and model_identifier in DEVICE_REFERENCE_DATABASE:
        profile = dict(DEVICE_REFERENCE_DATABASE[model_identifier])
        profile.update({"source_type": "VERICORE_MODEL_REFERENCE", "accuracy": "REFERENCE_ESTIMATE", "model_identifier": model_identifier, "model": model_name})
        return profile
    return {"model_identifier": model_identifier, "model": model_name, "battery_capacity_mAh": None, "charging_max_w": None, "battery_life_cycles": None, "source_type": "NO_REFERENCE_DATA", "accuracy": "UNKNOWN"}


# ============================================================
# SCORE SYSTEM
# ============================================================

COMPONENT_STATUS_SCORE = {
    "VERIFIED": 100,
    "LIKELY_ORIGINAL": 90,
    "PASSED": 90,
    "UNCERTAIN": 55,
    "MANUAL_TEST_REQUIRED": 50,
    "REPLACEMENT_SUSPECTED": 25,
    "FAILED": 0,
    "NOT_AVAILABLE": None,
}


FUNCTIONAL_STATUS_SCORE = {
    "PASSED": 100,
    "MANUAL_TEST_REQUIRED": None,
    "NOT_AVAILABLE": None,
    "FAILED": 0,
}


def calculate_component_score(components):
    """
    Score only components for which VeriCore has evidence.

    Unknown/manual tests do not directly reduce the score.
    """
    scores = []

    for component in components.values():

        if not isinstance(component, dict):
            continue

        status = component.get("status")

        score = COMPONENT_STATUS_SCORE.get(status)

        if score is not None:
            scores.append(score)

    if not scores:
        return None

    return round(sum(scores) / len(scores))


def calculate_functional_score(functional_tests):
    """
    Score only completed functional tests.

    A manual test is not a failure.
    """
    scores = []

    for test in functional_tests.values():

        if not isinstance(test, dict):
            continue

        status = test.get("status")

        score = FUNCTIONAL_STATUS_SCORE.get(status)

        if score is not None:
            scores.append(score)

    if not scores:
        return None

    return round(sum(scores) / len(scores))


def calculate_battery_score(battery):
    """Score battery health primarily, with cycle count as context."""
    health = safe_int(battery.get("health_percent"))
    cycles = safe_int(battery.get("cycles"))
    reference_cycles = safe_int(battery.get("reference_cycle_life"))
    if health is None and cycles is None:
        return None
    health_score = None
    if health is not None:
        if health >= 95: health_score = 100
        elif health >= 90: health_score = 97
        elif health >= 85: health_score = 92
        elif health >= 80: health_score = 85
        elif health >= 75: health_score = 72
        elif health >= 70: health_score = 58
        elif health >= 60: health_score = 40
        else: health_score = 20
    cycle_score = None
    if cycles is not None and reference_cycles:
        ratio = cycles / reference_cycles
        if ratio <= .30: cycle_score = 100
        elif ratio <= .60: cycle_score = 90
        elif ratio <= .80: cycle_score = 80
        elif ratio <= 1.00: cycle_score = 70
        elif ratio <= 1.25: cycle_score = 55
        else: cycle_score = 35
    elif cycles is not None:
        cycle_score = 100 if cycles <= 300 else 85 if cycles <= 600 else 70 if cycles <= 1000 else 45
    if health_score is not None and cycle_score is not None:
        score = round((health_score * .75) + (cycle_score * .25))
    else:
        score = health_score if health_score is not None else cycle_score
    return max(0, min(100, score))


def calculate_vericore_score(device):
    """
    Calculate the current VeriCore score.

    The score is based on available evidence.

    Missing tests do NOT automatically make a good device fail.
    """

    component_score = calculate_component_score(
        device.get("components", {})
    )

    functional_score = calculate_functional_score(
        device.get("functional_tests", {})
    )

    battery = device.get(
        "battery",
        {}
    )

    battery_score = calculate_battery_score(
        battery
    )

    scores = []

    if component_score is not None:
        scores.append(
            ("components", component_score, 0.45)
        )

    if functional_score is not None:
        scores.append(
            ("functional", functional_score, 0.30)
        )

    if battery_score is not None:
        scores.append(
            ("battery", battery_score, 0.25)
        )

    if not scores:
        return {
            "score": None,
            "component_score": component_score,
            "functional_score": functional_score,
            "battery_score": battery_score,
            "confidence": "LOW"
        }

    total_weight = sum(
        weight
        for _, _, weight in scores
    )

    weighted_score = sum(
        score * weight
        for _, score, weight in scores
    ) / total_weight

    # --------------------------------------------------------
    # Activation
    # --------------------------------------------------------

    activation_state = str(
        device.get("activation_state", "")
    ).lower()

    if activation_state in (
        "activation locked",
        "activationlocked",
        "locked"
    ):
        weighted_score -= 25

    # --------------------------------------------------------
    # Failed functional tests
    # --------------------------------------------------------

    failed_tests = [
        test
        for test in device.get(
            "functional_tests",
            {}
        ).values()
        if isinstance(test, dict)
        and test.get("status") == "FAILED"
    ]

    weighted_score -= len(failed_tests) * 8

    final_score = max(
        0,
        min(
            100,
            round(weighted_score)
        )
    )

    available_categories = len(scores)

    if available_categories >= 3:
        confidence = "HIGH"

    elif available_categories == 2:
        confidence = "MEDIUM"

    else:
        confidence = "LOW"

    return {
        "score": final_score,
        "component_score": component_score,
        "functional_score": functional_score,
        "battery_score": battery_score,
        "confidence": confidence
    }


# ============================================================
# INSPECTION COMPLETENESS
# ============================================================

def calculate_inspection_completeness(device):
    """
    Determines how much of the complete VeriCore inspection
    has actually been performed.
    """

    tests = device.get(
        "functional_tests",
        {}
    )

    if not tests:
        return {
            "percentage": 0,
            "status": "NOT_STARTED"
        }

    total = len(tests)

    completed = sum(
        1
        for test in tests.values()
        if test.get("status") in (
            "PASSED",
            "FAILED"
        )
    )

    percentage = round(
        (completed / total) * 100
    )

    if percentage == 0:
        status = "NOT_STARTED"

    elif percentage < 50:
        status = "IN_PROGRESS"

    elif percentage < 100:
        status = "PARTIAL"

    else:
        status = "COMPLETE"

    return {
        "percentage": percentage,
        "completed_tests": completed,
        "total_tests": total,
        "status": status
    }


# ============================================================
# iOS INFORMATION
# ============================================================

def ios_available():
    return (
        command_exists("ideviceinfo")
        and command_exists("idevice_id")
    )


def detect_ios_devices():
    output = run_cmd(
        ["idevice_id", "-l"]
    )

    if not output:
        return []

    return [
        line.strip()
        for line in output.splitlines()
        if line.strip()
    ]


def parse_ideviceinfo(text):
    data = {}

    if not text:
        return data

    for line in text.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        data[key.strip()] = value.strip()

    return data


def get_ios_domain(udid, domain):
    """
    Query an additional iOS lockdown domain.

    Example:
        com.apple.mobile.battery
        com.apple.disk_usage
    """

    command = [
        "ideviceinfo"
    ]

    if udid:
        command.extend([
            "-u",
            udid
        ])

    command.extend([
        "-q",
        domain
    ])

    output = run_cmd(command)

    if not output:
        return {}

    return parse_ideviceinfo(
        output
    )


def merge_data(*dictionaries):
    """
    Merge dictionaries without replacing an already
    useful value with an empty value.
    """

    result = {}

    for dictionary in dictionaries:

        if not dictionary:
            continue

        for key, value in dictionary.items():

            if value in (
                None,
                "",
                "unreadable"
            ):
                continue

            result[key] = value

    return result


# ============================================================
# iOS DEVICE CONDITION
# ============================================================

def get_iphone_condition(model_number):
    """
    Apple model-number sales-origin classification.

    M = originally sold as new
    F = originally sold as refurbished
    N = replacement device
    P = personalized

    This does NOT describe the device's current condition.
    """

    model_number = clean_value(
        model_number
    )

    if not model_number:

        return {
            "origin": "UNKNOWN",
            "evidence": "Model number unavailable"
        }

    first_character = model_number[0].upper()

    mapping = {
        "M": (
            "NEW_RETAIL_ORIGIN",
            "Originally sold as a new retail unit"
        ),
        "F": (
            "REFURBISHED_ORIGIN",
            "Originally sold as a refurbished unit"
        ),
        "N": (
            "REPLACEMENT_ORIGIN",
            "Apple replacement device"
        ),
        "P": (
            "PERSONALIZED_ORIGIN",
            "Personalized device"
        )
    }

    if first_character in mapping:

        origin, evidence = mapping[
            first_character
        ]

        return {
            "origin": origin,
            "evidence": evidence
        }

    return {
        "origin": "UNKNOWN",
        "evidence": "Unknown model-number prefix"
    }


# ============================================================
# BATTERY REFERENCE / ESTIMATION ENGINE
# ============================================================

def cycle_assessment(cycles, expected_cycles=None):
    if cycles is None:
        return "UNKNOWN"
    if expected_cycles:
        ratio = cycles / expected_cycles
        if ratio <= 0.30: return "LOW_USAGE"
        if ratio <= 0.60: return "MODERATE_USAGE"
        if ratio <= 1.00: return "HIGH_USAGE"
        return "VERY_HIGH_USAGE"
    if cycles <= 300: return "LOW_USAGE"
    if cycles <= 600: return "MODERATE_USAGE"
    if cycles <= 1000: return "HIGH_USAGE"
    return "VERY_HIGH_USAGE"


def calculate_battery_reference_metrics(battery, reference_profile):
    reference_capacity = reference_profile.get("battery_capacity_mAh")
    health = safe_int(battery.get("health_percent"))
    cycles = safe_int(battery.get("cycles"))
    estimated_capacity = None
    capacity_loss = None
    if reference_capacity and health is not None:
        estimated_capacity = round(reference_capacity * (health / 100.0))
        capacity_loss = max(0, reference_capacity - estimated_capacity)
    battery["reference_capacity_mAh"] = reference_capacity
    battery["estimated_current_capacity_mAh"] = estimated_capacity
    battery["estimated_capacity_loss_mAh"] = capacity_loss
    battery["reference_charging_max_w"] = reference_profile.get("charging_max_w")
    battery["reference_cycle_life"] = reference_profile.get("battery_life_cycles")
    battery["cycle_assessment"] = cycle_assessment(cycles, reference_profile.get("battery_life_cycles"))

    if health is not None:
        if health >= 90:
            battery["status"] = "GOOD"
        elif health >= 80:
            battery["status"] = "FAIR"
        elif health >= 70:
            battery["status"] = "DEGRADED"
        else:
            battery["status"] = "REPAIR_RECOMMENDED"
    elif cycles is not None or reference_capacity is not None:
        battery["status"] = "PARTIAL_DATA"

    if health is not None and reference_capacity:
        battery["capacity_calculation"] = f"{reference_capacity} × {health}% = {estimated_capacity} mAh"
        battery["capacity_accuracy"] = "ESTIMATED"
    elif health is None:
        battery["capacity_calculation"] = None
        battery["capacity_accuracy"] = "NOT_CALCULATED"
    else:
        battery["capacity_calculation"] = None
        battery["capacity_accuracy"] = "NO_REFERENCE_CAPACITY"
    return battery


def prompt_integer(prompt, minimum=0, maximum=None):
    while True:
        value = input(prompt).strip()
        if value == "": return None
        parsed = safe_int(value)
        if parsed is None:
            print("[!] Please enter a valid number or press Enter to skip.")
            continue
        if parsed < minimum:
            print(f"[!] Value must be at least {minimum}.")
            continue
        if maximum is not None and parsed > maximum:
            print(f"[!] Value must be at most {maximum}.")
            continue
        return parsed


def collect_manual_battery_data(battery, reference_profile):
    health_missing = battery.get("health_percent") is None
    cycles_missing = battery.get("cycles") is None
    if not health_missing and not cycles_missing:
        return battery
    if SKIP_MANUAL_PROMPTS:
        return battery
    print()
    print("-" * 70)
    print("VERICORE BATTERY MANUAL DATA")
    print("-" * 70)
    print("Some battery information is not exposed automatically.")
    print("Manual values are stored as MANUAL_INPUT in the report.")
    print("Press Enter to skip a value.")
    if reference_profile.get("battery_capacity_mAh"):
        print(f"Reference battery capacity: {reference_profile['battery_capacity_mAh']} mAh")
    if health_missing:
        health = prompt_integer("Enter battery health (%): ", 0, 100)
        if health is not None:
            battery["health_percent"] = health
            battery.setdefault("manual_input", []).append("health_percent")
    if cycles_missing:
        cycles = prompt_integer("Enter battery cycle count: ", 0)
        if cycles is not None:
            battery["cycles"] = cycles
            battery.setdefault("manual_input", []).append("cycles")
    return battery


# ============================================================
# iOS BATTERY DIAGNOSTICS
# ============================================================

def parse_ios_battery(data):
    """
    Extract battery information from all available iOS data.

    Different iOS versions expose different fields.

    VeriCore checks several possible field names rather than
    assuming that one field exists on every device.
    """

    battery = {
        "status": "NOT_AVAILABLE",
        "health_percent": None,
        "cycles": None,
        "current_capacity_mAh": None,
        "design_capacity_mAh": None,
        "reference_capacity_mAh": None,
        "estimated_current_capacity_mAh": None,
        "estimated_capacity_loss_mAh": None,
        "reference_charging_max_w": None,
        "reference_cycle_life": None,
        "cycle_assessment": "UNKNOWN",
        "capacity_calculation": None,
        "capacity_accuracy": "NOT_CALCULATED",
        "manual_input": [],
        "reported_runtime_charge_value": None,
        "nominal_capacity_mAh": None,
        "temperature_c": None,
        "voltage_mv": None,
        "current_ma": None,
        "charging": None,
        "fully_charged": None,
        "raw_source_fields": [],
        "warning": None
    }

    # --------------------------------------------------------
    # Health
    # --------------------------------------------------------

    health_keys = [
        "BatteryHealth",
        "BatteryHealthPercentage",
        "BatteryHealthPercent",
        "HealthPercent",
        "MaximumCapacityPercent",
        "MaximumCapacityPercentage"
    ]

    for key in health_keys:

        value = safe_int(
            data.get(key)
        )

        if value is not None and 0 <= value <= 100:

            battery["health_percent"] = value

            battery["raw_source_fields"].append(
                key
            )

            break

    # --------------------------------------------------------
    # Cycles
    # --------------------------------------------------------

    cycle_keys = [
        "CycleCount",
        "BatteryCycleCount",
        "CycleCountMax"
    ]

    for key in cycle_keys:

        value = safe_int(
            data.get(key)
        )

        if value is not None and value >= 0:

            battery["cycles"] = value

            battery["raw_source_fields"].append(
                key
            )

            break

    # --------------------------------------------------------
    # Runtime charge telemetry (NOT physical battery capacity)
    # --------------------------------------------------------
    for key in ["BatteryCurrentCapacity", "CurrentCapacity"]:
        value = safe_int(data.get(key))
        if value is not None and value >= 0:
            battery["reported_runtime_charge_value"] = value
            battery["raw_source_fields"].append(key)
            break

    # --------------------------------------------------------
    # Design capacity
    # --------------------------------------------------------

    design_capacity_keys = [
        "DesignCapacity",
        "BatteryDesignCapacity",
        "DesignCapacityRaw"
    ]

    for key in design_capacity_keys:

        value = safe_int(
            data.get(key)
        )

        if value is not None and value > 0:

            battery["design_capacity_mAh"] = value

            battery["raw_source_fields"].append(
                key
            )

            break

    # --------------------------------------------------------
    # Nominal capacity
    # --------------------------------------------------------

    nominal_capacity_keys = [
        "NominalCapacity",
        "BatteryNominalCapacity"
    ]

    for key in nominal_capacity_keys:

        value = safe_int(
            data.get(key)
        )

        if value is not None and value > 0:

            battery["nominal_capacity_mAh"] = value

            battery["raw_source_fields"].append(
                key
            )

            break

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    temperature_keys = [
        "Temperature",
        "BatteryTemperature"
    ]

    for key in temperature_keys:

        value = safe_int(
            data.get(key)
        )

        if value is not None:

            # iOS often exposes temperature in 0.01 °C
            if abs(value) > 1000:
                battery["temperature_c"] = round(
                    value / 100.0,
                    2
                )

            # Some sources expose 0.1 °C
            elif abs(value) > 100:
                battery["temperature_c"] = round(
                    value / 10.0,
                    1
                )

            else:
                battery["temperature_c"] = value

            battery["raw_source_fields"].append(
                key
            )

            break

    # --------------------------------------------------------
    # Voltage
    # --------------------------------------------------------

    voltage_keys = [
        "Voltage",
        "BatteryVoltage"
    ]

    for key in voltage_keys:

        value = safe_int(
            data.get(key)
        )

        if value is not None and value > 0:

            battery["voltage_mv"] = value

            battery["raw_source_fields"].append(
                key
            )

            break

    # --------------------------------------------------------
    # Charging
    # --------------------------------------------------------

    charging_keys = [
        "BatteryIsCharging",
        "IsCharging"
    ]

    for key in charging_keys:

        value = data.get(key)

        if value is not None:

            battery["charging"] = str(
                value
            ).lower() in (
                "1",
                "true",
                "yes"
            )

            battery["raw_source_fields"].append(
                key
            )

            break

    # --------------------------------------------------------
    # Fully charged
    # --------------------------------------------------------

    fully_charged_keys = [
        "BatteryFullyCharged",
        "FullyCharged"
    ]

    for key in fully_charged_keys:

        value = data.get(key)

        if value is not None:

            battery["fully_charged"] = str(
                value
            ).lower() in (
                "1",
                "true",
                "yes"
            )

            battery["raw_source_fields"].append(
                key
            )

            break

    # --------------------------------------------------------
    # Infer health from capacity if available
    # --------------------------------------------------------

    if (
        battery["health_percent"] is None
        and battery["current_capacity_mAh"] is not None
        and battery["design_capacity_mAh"] is not None
        and battery["design_capacity_mAh"] > 0
    ):

        calculated_health = round(
            (
                battery["current_capacity_mAh"]
                /
                battery["design_capacity_mAh"]
            ) * 100
        )

        battery["health_percent"] = max(
            0,
            min(
                100,
                calculated_health
            )
        )

    # --------------------------------------------------------
    # Battery status
    # --------------------------------------------------------

    health = battery["health_percent"]

    if health is not None:

        if health >= 90:
            battery["status"] = "GOOD"

        elif health >= 80:
            battery["status"] = "FAIR"

        elif health >= 70:
            battery["status"] = "DEGRADED"

        else:
            battery["status"] = "REPAIR_RECOMMENDED"

    elif battery["cycles"] is not None:

        battery["status"] = "PARTIAL_DATA"

    elif (
        battery["current_capacity_mAh"] is not None
        or battery["voltage_mv"] is not None
        or battery["temperature_c"] is not None
    ):

        battery["status"] = "PARTIAL_DATA"

    else:

        battery["status"] = "NOT_AVAILABLE"

    # --------------------------------------------------------
    # Warnings
    # --------------------------------------------------------

    warnings = []

    if health is not None:

        if health < 80:
            warnings.append(
                "Battery health is below 80%"
            )

        elif health < 85:
            warnings.append(
                "Battery health is below 85%"
            )

    if battery["temperature_c"] is not None:

        temperature = battery["temperature_c"]

        if temperature >= 45:
            warnings.append(
                "Battery temperature is elevated"
            )

    if not battery["raw_source_fields"]:

        warnings.append(
            "Battery diagnostic fields were not exposed "
            "by the connected iOS diagnostic interface"
        )

    battery["warning"] = (
        "; ".join(warnings)
        if warnings
        else None
    )

    return battery


# ============================================================
# iOS STORAGE
# ============================================================

def parse_ios_storage(data):
    """
    Try multiple iOS storage fields.
    """

    total_keys = [
        "TotalDiskCapacity",
        "TotalDataCapacity",
        "TotalDataAvailable",
        "DiskUsage",
        "TotalCapacity"
    ]

    total_bytes = None

    for key in total_keys:

        value = data.get(key)

        if value is None:
            continue

        match = re.search(
            r"(\d+)",
            str(value)
        )

        if match:

            candidate = safe_int(
                match.group(1)
            )

            if candidate and candidate > 1_000_000_000:

                total_bytes = candidate
                break

    return {
        "total": human_gb(total_bytes),
        "raw_bytes": total_bytes
    }


# ============================================================
# iOS DEVICE AGE
# ============================================================

def calculate_days_used(data):
    """
    Calculate days since activation.
    """

    activation_keys = [
        "ActivationDate",
        "ActivationDateTime"
    ]

    activation_value = first_available(
        data,
        activation_keys
    )

    if not activation_value:
        return None

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S"
    ]

    for date_format in formats:

        try:

            activation_date = datetime.strptime(
                str(activation_value).split("+")[0],
                date_format
            )

            days = (
                datetime.now() - activation_date
            ).days

            if days >= 0:
                return days

        except ValueError:
            continue

    return None


# ============================================================
# WIFI / BLUETOOTH — AUTOMATIC HARDWARE-PRESENCE CHECK
# ============================================================

_MAC_PATTERN = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")


def ios_wifi_bluetooth_check(udid):
    """
    Automatic (non-interactive) WiFi/Bluetooth radio check.

    This confirms the radio enumerates with a valid hardware
    address - real automated evidence the chip is alive and
    talking to iOS. It does NOT confirm a live network/pairing,
    which still needs a technician to actually join a network.
    """
    wifi_data = get_ios_domain(udid, "com.apple.mobile.wifi_connections")
    bt_data = get_ios_domain(udid, "com.apple.Bluetooth")

    wifi_mac = first_available(wifi_data, ["WiFiAddress"])
    bt_mac = first_available(bt_data, ["BluetoothAddress"])

    def evaluate(mac, label):
        if mac and _MAC_PATTERN.match(mac):
            return {
                "name": label,
                "status": "PASSED",
                "evidence": f"{label} radio enumerated with valid hardware address ({mac})",
            }
        return {
            "name": label,
            "status": "MANUAL_TEST_REQUIRED",
            "evidence": f"{label} hardware address not exposed by lockdown service; connect to a known network/device to confirm",
        }

    return (
        evaluate(wifi_mac, "Wi-Fi"),
        evaluate(bt_mac, "Bluetooth"),
    )


def android_wifi_bluetooth_check(device_id):
    """
    Automatic (non-interactive) WiFi/Bluetooth check for Android.

    Reads live dumpsys state - if the radio is enabled AND has
    a MAC/connection reported, that's real automated evidence.
    """
    wifi_dump = run_cmd(["adb", "-s", device_id, "shell", "dumpsys", "wifi"]) or ""
    bt_dump = run_cmd(["adb", "-s", device_id, "shell", "dumpsys", "bluetooth_manager"]) or ""

    wifi_mac_match = re.search(r"mac[_ ]?address[:\s]+([0-9A-Fa-f:]{17})", wifi_dump, re.IGNORECASE)
    wifi_enabled = bool(re.search(r"Wi-Fi is enabled", wifi_dump))

    bt_enabled = bool(re.search(r"enabled:\s*true", bt_dump, re.IGNORECASE))

    if wifi_mac_match and wifi_enabled:
        wifi_test = {
            "name": "Wi-Fi",
            "status": "PASSED",
            "evidence": f"Wi-Fi radio enabled with hardware address ({wifi_mac_match.group(1)})",
        }
    elif wifi_enabled:
        wifi_test = {
            "name": "Wi-Fi",
            "status": "PASSED",
            "evidence": "Wi-Fi radio reports enabled state",
        }
    else:
        wifi_test = {
            "name": "Wi-Fi",
            "status": "MANUAL_TEST_REQUIRED",
            "evidence": "Could not confirm Wi-Fi radio state automatically",
        }

    if bt_enabled:
        bt_test = {
            "name": "Bluetooth",
            "status": "PASSED",
            "evidence": "Bluetooth service reports enabled state",
        }
    else:
        bt_test = {
            "name": "Bluetooth",
            "status": "MANUAL_TEST_REQUIRED",
            "evidence": "Could not confirm Bluetooth radio state automatically",
        }

    return wifi_test, bt_test


# ============================================================
# GENUINE-PARTS CHECK LOADER (from parts_check_capture.py)
# ============================================================

def load_parts_check_result(path):
    """
    Load OCR-derived genuine-parts results produced by
    parts_check_capture.py. Returns {} if not provided/unreadable
    so VeriCore degrades gracefully to MANUAL_TEST_REQUIRED /
    the existing heuristics.
    """
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


# ============================================================
# MANUAL TEST COLLECTION (interactive, technician-facing)
# ============================================================

SKIP_MANUAL_PROMPTS = False


def prompt_choice(prompt_text, choices):
    """
    Ask for a single-letter choice. Empty input means "skip".
    Re-prompts on anything else.
    """
    valid = {c.upper() for c in choices}

    while True:
        value = input(prompt_text).strip().upper()

        if value == "":
            return None

        if value in valid:
            return value

        print(f"[!] Please enter one of: {', '.join(sorted(valid))} (or press Enter to skip).")


def collect_manual_functional_tests(functional_tests):
    """
    Walk every functional test still marked MANUAL_TEST_REQUIRED
    and let the technician record a real PASSED/FAILED result.

    Nothing here fabricates a result: leaving a prompt blank keeps
    the test at MANUAL_TEST_REQUIRED, exactly as before.
    """
    if SKIP_MANUAL_PROMPTS:
        return functional_tests

    pending = [
        name
        for name, test in functional_tests.items()
        if isinstance(test, dict) and test.get("status") == "MANUAL_TEST_REQUIRED"
    ]

    if not pending:
        return functional_tests

    print()
    print("-" * 70)
    print("VERICORE MANUAL FUNCTIONAL TESTS")
    print("-" * 70)
    print("Perform each physical test, then record the result.")
    print("Press Enter to skip a test and leave it pending.")

    for name in pending:
        test = functional_tests[name]
        label = test.get("name", name)
        guidance = test.get("evidence")

        print(f"\n{label}")

        if guidance:
            print(f"  Guidance : {guidance}")

        choice = prompt_choice(
            "  Result [P]assed / [F]ailed / Enter to skip: ",
            {"P", "F"}
        )

        if choice == "P":

            test["status"] = "PASSED"
            test["evidence"] = (
                f"Manually tested by technician: PASSED"
                + (f" ({guidance})" if guidance else "")
            )
            test["manual_input"] = True

        elif choice == "F":

            failure_note = input(
                "  Optional note on the failure (Enter to skip): "
            ).strip()

            test["status"] = "FAILED"
            test["evidence"] = (
                f"Manually tested by technician: FAILED"
                + (f" — {failure_note}" if failure_note else "")
            )
            test["manual_input"] = True

    return functional_tests


def collect_manual_component_checks(components):
    """
    Walk every component still marked MANUAL_TEST_REQUIRED and let
    the technician record a real originality verdict after physical
    inspection.

    This does NOT touch components already resolved by parts-check
    OCR (VERIFIED/REPLACEMENT_SUSPECTED) or by automatic evidence
    (LIKELY_ORIGINAL from True Tone, USB comms, etc.) — only items
    that genuinely still say MANUAL_TEST_REQUIRED.
    """
    if SKIP_MANUAL_PROMPTS:
        return components

    pending = [
        name
        for name, component in components.items()
        if isinstance(component, dict) and component.get("status") == "MANUAL_TEST_REQUIRED"
    ]

    if not pending:
        return components

    print()
    print("-" * 70)
    print("VERICORE MANUAL COMPONENT INSPECTION")
    print("-" * 70)
    print("Physically inspect each component for originality, then record it.")
    print("Press Enter to skip and leave it pending.")

    for name in pending:
        component = components[name]
        label = component.get("name", name)
        warning = component.get("warning")

        print(f"\n{label}")

        if warning:
            print(f"  Note     : {warning}")

        choice = prompt_choice(
            "  Result [G]enuine / [S]uspected replacement / Enter to skip: ",
            {"G", "S"}
        )

        component.setdefault("evidence", [])

        if choice == "G":

            component["status"] = "VERIFIED"
            component["confidence"] = "HIGH"
            component["evidence"].append(
                "Manually inspected by technician: appears genuine"
            )

        elif choice == "S":

            note = input(
                "  Optional note on what looked off (Enter to skip): "
            ).strip()

            component["status"] = "REPLACEMENT_SUSPECTED"
            component["confidence"] = "HIGH"
            component["evidence"].append(
                "Manually inspected by technician: suspected non-genuine/replacement part"
                + (f" — {note}" if note else "")
            )

    return components


# ============================================================
# iOS COMPONENT ANALYSIS
# ============================================================

def analyze_ios_components(
    general_data,
    battery_data,
    parts_check=None
):
    parts_check = parts_check or {}
    components = {}

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    display = {
        "name": "Display",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "MEDIUM",
        "evidence": [],
        "warning": None
    }

    display_check = parts_check.get("display_parts_check")

    if display_check == "WARNING":

        display["status"] = "REPLACEMENT_SUSPECTED"
        display["confidence"] = "HIGH"
        display["evidence"].append(
            "Settings app reported a non-genuine display warning (OCR-verified)"
        )

    elif display_check == "GENUINE":

        display["status"] = "VERIFIED"
        display["confidence"] = "HIGH"
        display["evidence"].append(
            "No genuine-parts warning found for display in Settings > About (OCR-verified)"
        )

    else:

        true_tone = first_available(
            general_data,
            [
                "TrueToneAvailable",
                "TrueToneCapability"
            ]
        )

        if true_tone == "1":

            display["status"] = "LIKELY_ORIGINAL"

            display["evidence"].append(
                "True Tone capability reported available"
            )

            display["warning"] = (
                "True Tone availability is evidence only; "
                "physical originality requires further verification"
            )

        elif true_tone == "0":

            display["status"] = "REPLACEMENT_SUSPECTED"

            display["evidence"].append(
                "True Tone capability reported unavailable"
            )

            display["warning"] = (
                "Display may have been replaced or configuration "
                "may be incomplete"
            )

        else:

            display["evidence"].append(
                "No reliable display authenticity field available"
            )

    components["display"] = display

    # --------------------------------------------------------
    # BATTERY
    # --------------------------------------------------------

    battery_status = battery_data.get(
        "status",
        "NOT_AVAILABLE"
    )

    if battery_status == "GOOD":
        component_status = "LIKELY_ORIGINAL"

    elif battery_status == "FAIR":
        component_status = "UNCERTAIN"

    elif battery_status == "DEGRADED":
        component_status = "UNCERTAIN"

    elif battery_status == "REPAIR_RECOMMENDED":
        component_status = "REPLACEMENT_SUSPECTED"

    elif battery_status == "PARTIAL_DATA":
        component_status = "UNCERTAIN"

    else:
        component_status = "NOT_AVAILABLE"

    battery_component = {
        "name": "Battery",
        "status": component_status,
        "confidence": "MEDIUM",
        "health_percent": battery_data.get(
            "health_percent"
        ),
        "cycles": battery_data.get(
            "cycles"
        ),
        "current_capacity_mAh": battery_data.get(
            "estimated_current_capacity_mAh"
        ),
        "design_capacity_mAh": battery_data.get(
            "reference_capacity_mAh"
        ),
        "estimated_capacity_loss_mAh": battery_data.get(
            "estimated_capacity_loss_mAh"
        ),
        "cycle_assessment": battery_data.get(
            "cycle_assessment"
        ),
        "temperature_c": battery_data.get(
            "temperature_c"
        ),
        "voltage_mv": battery_data.get(
            "voltage_mv"
        ),
        "evidence": [],
        "warning": battery_data.get(
            "warning"
        )
    }

    if battery_component[
        "health_percent"
    ] is not None:

        battery_component[
            "evidence"
        ].append(
            "Battery health data available"
        )

    if battery_component[
        "cycles"
    ] is not None:

        battery_component[
            "evidence"
        ].append(
            "Battery cycle count available"
        )

    if battery_component[
        "current_capacity_mAh"
    ] is not None:

        battery_component[
            "evidence"
        ].append(
            "Battery capacity data available"
        )

    battery_check = parts_check.get("battery_parts_check")

    if battery_check == "WARNING":

        battery_component["status"] = "REPLACEMENT_SUSPECTED"
        battery_component["confidence"] = "HIGH"
        battery_component["evidence"].append(
            "Settings app reported a non-genuine battery warning (OCR-verified)"
        )

    elif battery_check == "GENUINE":

        battery_component["status"] = "VERIFIED"
        battery_component["confidence"] = "HIGH"
        battery_component["evidence"].append(
            "No genuine-parts warning found for battery in Settings > About (OCR-verified)"
        )

    components["battery"] = battery_component

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    camera = {
        "name": "Camera",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "MEDIUM",
        "evidence": [],
        "warning": (
            "Camera functionality and originality "
            "require dedicated functional testing"
        )
    }

    camera_fields = [
        "RearCameraCapability",
        "FrontCameraCapability",
        "CameraCapabilities"
    ]

    for field in camera_fields:

        value = general_data.get(field)

        if value:

            camera["evidence"].append(
                f"{field}: {value}"
            )

    camera_check = parts_check.get("camera_parts_check")

    if camera_check == "WARNING":

        camera["status"] = "REPLACEMENT_SUSPECTED"
        camera["confidence"] = "HIGH"
        camera["evidence"].append(
            "Settings app reported a non-genuine camera warning (OCR-verified)"
        )
        camera["warning"] = None

    elif camera_check == "GENUINE":

        camera["status"] = "VERIFIED"
        camera["confidence"] = "HIGH"
        camera["evidence"].append(
            "No genuine-parts warning found for camera in Settings > About (OCR-verified)"
        )
        camera["warning"] = None

    components["camera"] = camera

    # --------------------------------------------------------
    # BIOMETRICS
    # --------------------------------------------------------

    biometrics = {
        "name": "Biometrics",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "MEDIUM",
        "evidence": [],
        "warning": (
            "Enrollment status does not prove biometric "
            "hardware originality"
        )
    }

    face_id = general_data.get(
        "FaceIDEnrolled"
    )

    touch_id = general_data.get(
        "TouchIDEnrolled"
    )

    if face_id == "1":

        biometrics["evidence"].append(
            "Face ID enrollment detected"
        )

    if touch_id == "1":

        biometrics["evidence"].append(
            "Touch ID enrollment detected"
        )

    if biometrics["evidence"]:

        biometrics["status"] = "LIKELY_ORIGINAL"

    components["biometrics"] = biometrics

    # --------------------------------------------------------
    # SPEAKERS
    # --------------------------------------------------------

    components["speakers"] = {
        "name": "Speakers",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "LOW",
        "evidence": [],
        "warning": (
            "Speaker output must be physically tested"
        )
    }

    # --------------------------------------------------------
    # MICROPHONES
    # --------------------------------------------------------

    components["microphones"] = {
        "name": "Microphones",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "LOW",
        "evidence": [],
        "warning": (
            "Microphones must be tested using recording/playback"
        )
    }

    # --------------------------------------------------------
    # CHARGING PORT
    # --------------------------------------------------------

    components["charging_port"] = {
        "name": "Charging Port",
        "status": "LIKELY_ORIGINAL",
        "confidence": "MEDIUM",
        "evidence": [
            "USB communication established successfully"
        ],
        "warning": (
            "USB communication does not prove the physical "
            "condition of the charging port"
        )
    }

    return components


# ============================================================
# iOS FUNCTIONAL TESTS
# ============================================================

def ios_functional_tests(data, udid=None):
    tests = {}

    # --------------------------------------------------------
    # USB
    # --------------------------------------------------------

    tests["usb_connection"] = {
        "name": "USB Communication",
        "status": "PASSED",
        "evidence": (
            "Device successfully communicated through "
            "libimobiledevice"
        )
    }

    # --------------------------------------------------------
    # Activation
    # --------------------------------------------------------

    activation = data.get(
        "ActivationState"
    )

    if activation:

        if activation.lower() in (
            "activated",
            "deviceactivated"
        ):

            tests["activation"] = {
                "name": "Activation",
                "status": "PASSED",
                "evidence": activation
            }

        else:

            tests["activation"] = {
                "name": "Activation",
                "status": "FAILED",
                "evidence": activation
            }

    else:

        tests["activation"] = {
            "name": "Activation",
            "status": "MANUAL_TEST_REQUIRED",
            "evidence": (
                "Activation state unavailable"
            )
        }

    # --------------------------------------------------------
    # Physical tests
    # --------------------------------------------------------

    tests["display"] = {
        "name": "Display",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Check OLED/LCD image, brightness, "
            "dead pixels, burn-in and uniformity"
        )
    }

    tests["touchscreen"] = {
        "name": "Touchscreen",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Run multi-point touch test across the entire panel"
        )
    }

    tests["rear_camera"] = {
        "name": "Rear Camera",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test every rear camera, focus, stabilization "
            "and video recording"
        )
    }

    tests["front_camera"] = {
        "name": "Front Camera",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test front camera, focus and video"
        )
    }

    tests["face_id"] = {
        "name": "Face ID",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Perform Face ID enrollment and unlock test"
        )
    }

    tests["speakers"] = {
        "name": "Speakers",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test earpiece and loudspeaker"
        )
    }

    tests["microphones"] = {
        "name": "Microphones",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Record and playback audio using all microphones"
        )
    }

    tests["charging"] = {
        "name": "Charging",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test wired charging, connection stability "
            "and charging behavior"
        )
    }

    tests["buttons"] = {
        "name": "Physical Buttons",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test power, volume and action/mute controls"
        )
    }

    tests["vibration"] = {
        "name": "Haptics / Vibration",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Perform vibration and haptic feedback test"
        )
    }

    # --------------------------------------------------------
    # Wi-Fi / Bluetooth — now automatic
    # --------------------------------------------------------

    if udid:

        wifi_test, bluetooth_test = ios_wifi_bluetooth_check(udid)

        tests["wifi"] = wifi_test
        tests["bluetooth"] = bluetooth_test

    else:

        tests["wifi"] = {
            "name": "Wi-Fi",
            "status": "MANUAL_TEST_REQUIRED",
            "evidence": (
                "Connect to a known Wi-Fi network"
            )
        }

        tests["bluetooth"] = {
            "name": "Bluetooth",
            "status": "MANUAL_TEST_REQUIRED",
            "evidence": (
                "Pair with a Bluetooth accessory"
            )
        }

    return tests


# ============================================================
# iOS DETECTION
# ============================================================

def detect_ios(parts_check=None):
    devices = detect_ios_devices()

    if not devices:
        return None

    udid = devices[0]

    general_data = get_ios_domain(
        udid,
        "com.apple.mobile.lockdown_cache"
    )

    # The regular ideviceinfo query contains many important fields.
    regular_output = run_cmd([
        "ideviceinfo",
        "-u",
        udid
    ])

    regular_data = parse_ideviceinfo(
        regular_output
    )

    # Battery domain
    battery_domain = get_ios_domain(
        udid,
        "com.apple.mobile.battery"
    )

    # Disk domain
    disk_domain = get_ios_domain(
        udid,
        "com.apple.disk_usage"
    )

    # Mobile device domain, if available
    mobile_device_domain = get_ios_domain(
        udid,
        "com.apple.mobile.device"
    )

    data = merge_data(
        general_data,
        regular_data,
        battery_domain,
        disk_domain,
        mobile_device_domain
    )

    if not data:
        return None

    model_identifier = data.get(
        "ProductType"
    )

    model_name = IPHONE_MODELS.get(
        model_identifier,
        model_identifier or "Unknown iPhone"
    )

    reference_profile = get_reference_profile("iOS", model_identifier, model_name)

    model_number = data.get(
        "ModelNumber"
    )

    origin = get_iphone_condition(
        model_number
    )

    battery = parse_ios_battery(
        data
    )

    battery = collect_manual_battery_data(battery, reference_profile)
    battery = calculate_battery_reference_metrics(battery, reference_profile)

    storage = parse_ios_storage(
        data
    )

    components = analyze_ios_components(
        data,
        battery,
        parts_check
    )

    functional_tests = ios_functional_tests(
        data,
        udid
    )

    components = collect_manual_component_checks(components)
    functional_tests = collect_manual_functional_tests(functional_tests)

    days_used = calculate_days_used(
        data
    )

    serial = data.get(
        "SerialNumber"
    )

    device_udid = data.get(
        "UniqueDeviceID"
    )

    imei = first_available(
        data,
        [
            "InternationalMobileEquipmentIdentity",
            "IMEI"
        ]
    )

    imei2 = first_available(
        data,
        [
            "InternationalMobileEquipmentIdentity2",
            "IMEI2"
        ]
    )

    device = {
        "platform": "iOS",

        "device_name": data.get(
            "DeviceName",
            "Unknown iPhone"
        ),

        "model": model_name,

        "model_identifier": model_identifier,

        "model_number": model_number,

        "ios_version": data.get(
            "ProductVersion"
        ),

        "build_version": data.get(
            "BuildVersion"
        ),

        "serial": serial,

        "udid": device_udid,

        "imei": imei,

        "imei2": imei2,

        "device_fingerprint": generate_device_fingerprint(
            serial,
            device_udid,
            model_identifier
        ),

        "activation_state": data.get(
            "ActivationState"
        ),

        "sales_origin": origin,

        "storage": storage,

        "reference_profile": reference_profile,

        "days_used": days_used,

        "battery": battery,

        "components": components,

        "functional_tests": functional_tests,

        "raw_selected_fields": {
            "ProductType": data.get(
                "ProductType"
            ),
            "ProductVersion": data.get(
                "ProductVersion"
            ),
            "BuildVersion": data.get(
                "BuildVersion"
            ),
            "ActivationState": data.get(
                "ActivationState"
            ),
            "ModelNumber": data.get(
                "ModelNumber"
            ),
            "SerialNumber": data.get(
                "SerialNumber"
            ),
            "TrueToneAvailable": data.get(
                "TrueToneAvailable"
            ),
            "TotalDiskCapacity": data.get(
                "TotalDiskCapacity"
            ),
            "TotalDataCapacity": data.get(
                "TotalDataCapacity"
            ),
            "BatteryCapacity": data.get(
                "BatteryCapacity"
            ),
            "CycleCount": data.get(
                "CycleCount"
            ),
            "BatteryCurrentCapacity": data.get(
                "BatteryCurrentCapacity"
            )
        }
    }

    # --------------------------------------------------------
    # Scores
    # --------------------------------------------------------

    score_data = calculate_vericore_score(
        device
    )

    device["scores"] = score_data

    device["vericore_score"] = (
        score_data["score"]
    )

    device["inspection_completeness"] = (
        calculate_inspection_completeness(
            device
        )
    )

    return device


# ============================================================
# ANDROID
# ============================================================

def android_available():
    return command_exists("adb")


def android_connected_devices():
    output = run_cmd(
        ["adb", "devices"]
    )

    if not output:
        return []

    devices = []

    for line in output.splitlines()[1:]:

        line = line.strip()

        if "\tdevice" in line:

            device_id = line.split()[0]

            if device_id:
                devices.append(
                    device_id
                )

    return devices


def adb_shell(device_id, command):
    if isinstance(command, str):
        command = command.split()

    return run_cmd(
        [
            "adb",
            "-s",
            device_id,
            "shell"
        ] + command
    )


def android_property(
    device_id,
    property_name
):
    value = run_cmd([
        "adb",
        "-s",
        device_id,
        "shell",
        "getprop",
        property_name
    ])

    return (
        value
        if value
        else "unreadable"
    )


# ============================================================
# ANDROID BATTERY
# ============================================================

def android_battery_diagnostics(
    device_id
):
    dump = run_cmd([
        "adb",
        "-s",
        device_id,
        "shell",
        "dumpsys",
        "battery"
    ]) or ""

    battery = {
        "status": "NOT_AVAILABLE",
        "health_percent": None,
        "level": None,
        "cycles": None,
        "temperature_c": None,
        "voltage_mv": None,
        "charging": None,
        "health_state": "UNKNOWN",
        "warning": None
    }

    def extract(key):
        pattern = (
            rf"^\s*{re.escape(key)}"
            rf"\s*:\s*(.+)$"
        )

        match = re.search(
            pattern,
            dump,
            re.MULTILINE
        )

        if match:
            return match.group(1).strip()

        return None

    # --------------------------------------------------------
    # Level
    # --------------------------------------------------------

    level = safe_int(
        extract("level")
    )

    if level is not None:
        battery["level"] = level

    # --------------------------------------------------------
    # Health
    # --------------------------------------------------------

    health_code = extract(
        "health"
    )

    health_map = {
        "1": "UNKNOWN",
        "2": "GOOD",
        "3": "OVERHEAT",
        "4": "DEAD",
        "5": "OVER_VOLTAGE",
        "6": "FAILURE",
        "7": "COLD"
    }

    if health_code:

        battery["health_state"] = (
            health_map.get(
                str(health_code),
                str(health_code)
            )
        )

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    temperature = safe_int(
        extract("temperature")
    )

    if temperature is not None:

        battery["temperature_c"] = round(
            temperature / 10,
            1
        )

    # --------------------------------------------------------
    # Voltage
    # --------------------------------------------------------

    voltage = safe_int(
        extract("voltage")
    )

    if voltage is not None:
        battery["voltage_mv"] = voltage

    # --------------------------------------------------------
    # Charging
    # --------------------------------------------------------

    charging_values = [
        extract("AC powered"),
        extract("USB powered"),
        extract("Wireless powered")
    ]

    battery["charging"] = any(
        str(value).lower() == "true"
        for value in charging_values
        if value is not None
    )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if battery["health_state"] == "GOOD":

        battery["status"] = "GOOD"

    elif battery["health_state"] in (
        "OVERHEAT",
        "OVER_VOLTAGE",
        "COLD"
    ):

        battery["status"] = "DEGRADED"

    elif battery["health_state"] in (
        "DEAD",
        "FAILURE"
    ):

        battery["status"] = "REPAIR_RECOMMENDED"

    elif battery["level"] is not None:

        battery["status"] = "PARTIAL_DATA"

    return battery


# ============================================================
# ANDROID COMPONENTS
# ============================================================

def analyze_android_components(
    device_id,
    battery
):
    components = {}

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    density = android_property(
        device_id,
        "ro.sf.lcd_density"
    )

    components["display"] = {
        "name": "Display",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "MEDIUM",
        "evidence": (
            [f"LCD density: {density}"]
            if density != "unreadable"
            else []
        ),
        "warning": (
            "Display originality requires component evidence "
            "and physical inspection"
        )
    }

    # --------------------------------------------------------
    # Battery
    # --------------------------------------------------------

    battery_status = battery.get(
        "status"
    )

    if battery_status == "GOOD":
        component_status = "LIKELY_ORIGINAL"

    elif battery_status == "REPAIR_RECOMMENDED":
        component_status = "REPLACEMENT_SUSPECTED"

    elif battery_status == "NOT_AVAILABLE":
        component_status = "NOT_AVAILABLE"

    else:
        component_status = "UNCERTAIN"

    components["battery"] = {
        "name": "Battery",
        "status": component_status,
        "confidence": "MEDIUM",
        "health_percent": battery.get(
            "health_percent"
        ),
        "level": battery.get(
            "level"
        ),
        "cycles": battery.get(
            "cycles"
        ),
        "reference_capacity_mAh": battery.get("reference_capacity_mAh"),
        "estimated_current_capacity_mAh": battery.get("estimated_current_capacity_mAh"),
        "estimated_capacity_loss_mAh": battery.get("estimated_capacity_loss_mAh"),
        "cycle_assessment": battery.get("cycle_assessment"),
        "temperature_c": battery.get(
            "temperature_c"
        ),
        "voltage_mv": battery.get(
            "voltage_mv"
        ),
        "health_state": battery.get(
            "health_state"
        ),
        "evidence": [
            "Android battery service inspected"
        ],
        "warning": (
            "Generic ADB cannot independently prove "
            "battery originality"
        )
    }

    # --------------------------------------------------------
    # Camera
    # --------------------------------------------------------

    components["camera"] = {
        "name": "Camera",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "MEDIUM",
        "evidence": [],
        "warning": (
            "Test all camera modules physically"
        )
    }

    # --------------------------------------------------------
    # Biometrics
    # --------------------------------------------------------

    biometric_dump = adb_shell(
        device_id,
        [
            "dumpsys",
            "biometrics"
        ]
    )

    if biometric_dump:

        components["biometrics"] = {
            "name": "Biometrics",
            "status": "UNCERTAIN",
            "confidence": "LOW",
            "evidence": [
                "Biometric service detected"
            ],
            "warning": (
                "Service availability does not prove "
                "hardware originality"
            )
        }

    else:

        components["biometrics"] = {
            "name": "Biometrics",
            "status": "MANUAL_TEST_REQUIRED",
            "confidence": "LOW",
            "evidence": [],
            "warning": (
                "Biometric hardware requires functional testing"
            )
        }

    # --------------------------------------------------------
    # Speakers
    # --------------------------------------------------------

    components["speakers"] = {
        "name": "Speakers",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "LOW",
        "evidence": [],
        "warning": "Audio test required"
    }

    # --------------------------------------------------------
    # Microphones
    # --------------------------------------------------------

    components["microphones"] = {
        "name": "Microphones",
        "status": "MANUAL_TEST_REQUIRED",
        "confidence": "LOW",
        "evidence": [],
        "warning": "Recording test required"
    }

    # --------------------------------------------------------
    # USB / Charging
    # --------------------------------------------------------

    components["charging_port"] = {
        "name": "USB / Charging Port",
        "status": "LIKELY_ORIGINAL",
        "confidence": "MEDIUM",
        "evidence": [
            "ADB communication established"
        ],
        "warning": (
            "USB communication does not prove physical "
            "port condition"
        )
    }

    return components


# ============================================================
# ANDROID FUNCTIONAL TESTS
# ============================================================

def android_functional_tests(
    device_id
):
    tests = {}

    tests["usb_connection"] = {
        "name": "USB Communication",
        "status": "PASSED",
        "evidence": (
            "ADB communication established"
        )
    }

    tests["display"] = {
        "name": "Display",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Check dead pixels, burn-in, brightness "
            "and uniformity"
        )
    }

    tests["touchscreen"] = {
        "name": "Touchscreen",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Perform full multi-point touch test"
        )
    }

    tests["rear_camera"] = {
        "name": "Rear Camera",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test every rear camera and video mode"
        )
    }

    tests["front_camera"] = {
        "name": "Front Camera",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test front camera and video"
        )
    }

    tests["biometrics"] = {
        "name": "Biometrics",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test fingerprint / face unlock"
        )
    }

    tests["speakers"] = {
        "name": "Speakers",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test earpiece and loudspeaker"
        )
    }

    tests["microphones"] = {
        "name": "Microphones",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test all microphones"
        )
    }

    tests["charging"] = {
        "name": "Charging",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test wired/wireless charging where applicable"
        )
    }

    tests["buttons"] = {
        "name": "Physical Buttons",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Test power, volume and other physical buttons"
        )
    }

    tests["vibration"] = {
        "name": "Vibration / Haptics",
        "status": "MANUAL_TEST_REQUIRED",
        "evidence": (
            "Perform vibration test"
        )
    }

    # --------------------------------------------------------
    # Wi-Fi / Bluetooth — now automatic
    # --------------------------------------------------------

    wifi_test, bluetooth_test = android_wifi_bluetooth_check(device_id)

    tests["wifi"] = wifi_test
    tests["bluetooth"] = bluetooth_test

    return tests


# ============================================================
# ANDROID DETECTION
# ============================================================

def detect_android():

    devices = android_connected_devices()

    if not devices:
        return None

    device_id = devices[0]

    model = android_property(
        device_id,
        "ro.product.model"
    )

    brand = android_property(
        device_id,
        "ro.product.brand"
    )

    manufacturer = android_property(
        device_id,
        "ro.product.manufacturer"
    )

    reference_profile = get_reference_profile("Android", model, model)

    android_version = android_property(
        device_id,
        "ro.build.version.release"
    )

    sdk = android_property(
        device_id,
        "ro.build.version.sdk"
    )

    serial = android_property(
        device_id,
        "ro.serialno"
    )

    build_fingerprint = android_property(
        device_id,
        "ro.build.fingerprint"
    )

    storage_bytes = android_property(
        device_id,
        "ro.boot.flash.size"
    )

    ram_bytes = android_property(
        device_id,
        "ro.boot.ram.size"
    )

    battery = android_battery_diagnostics(
        device_id
    )

    battery = collect_manual_battery_data(battery, reference_profile)
    battery = calculate_battery_reference_metrics(battery, reference_profile)

    components = analyze_android_components(
        device_id,
        battery
    )

    functional_tests = android_functional_tests(
        device_id
    )

    components = collect_manual_component_checks(components)
    functional_tests = collect_manual_functional_tests(functional_tests)

    device = {
        "platform": "Android",

        "device_id": device_id,

        "device_name": model,

        "brand": brand,

        "manufacturer": manufacturer,

        "android_version": android_version,

        "sdk": sdk,

        "serial": serial,

        "build_fingerprint": build_fingerprint,

        "storage": {
            "total": human_gb(
                storage_bytes
            ),
            "raw_bytes": (
                safe_int(storage_bytes)
            )
        },

        "ram_size": human_gb(
            ram_bytes
        ),

        "reference_profile": reference_profile,

        "activation_state": None,

        "sales_origin": {
            "origin": "UNKNOWN",
            "evidence": (
                "Android does not expose a universal "
                "new/refurbished/replacement classification"
            )
        },

        "battery": battery,

        "components": components,

        "functional_tests": functional_tests,

        "device_fingerprint": generate_device_fingerprint(
            serial,
            build_fingerprint,
            model
        )
    }

    score_data = calculate_vericore_score(
        device
    )

    device["scores"] = score_data

    device["vericore_score"] = (
        score_data["score"]
    )

    device["inspection_completeness"] = (
        calculate_inspection_completeness(
            device
        )
    )

    return device


# ============================================================
# REPAIR DECISION ENGINE
# ============================================================

def determine_repair_decision(
    device
):
    """
    Important v3.1 change:

    A device with many untested components is NOT automatically
    rejected.

    It is classified as INSPECTION_INCOMPLETE.

    Only actual failures or sufficiently poor evidence trigger
    repair/recycle decisions.
    """

    score = device.get(
        "vericore_score"
    )

    completeness = device.get(
        "inspection_completeness",
        {}
    )

    components = device.get(
        "components",
        {}
    )

    functional_tests = device.get(
        "functional_tests",
        {}
    )

    failed_components = []
    suspected_replacements = []
    manual_tests = []
    failed_tests = []

    # --------------------------------------------------------
    # Components
    # --------------------------------------------------------

    for name, component in components.items():

        status = component.get(
            "status"
        )

        if status == "FAILED":
            failed_components.append(name)

        elif status == "REPLACEMENT_SUSPECTED":
            suspected_replacements.append(name)

        elif status == "MANUAL_TEST_REQUIRED":
            manual_tests.append(name)

    # --------------------------------------------------------
    # Functional tests
    # --------------------------------------------------------

    for name, test in functional_tests.items():

        status = test.get(
            "status"
        )

        if status == "FAILED":
            failed_tests.append(name)
        elif status == "MANUAL_TEST_REQUIRED" and name not in manual_tests:
            manual_tests.append(name)

    # --------------------------------------------------------
    # Critical failures
    # --------------------------------------------------------

    critical_components = {
        "display",
        "battery",
        "biometrics",
        "charging_port"
    }

    critical_failure = any(
        item in critical_components
        for item in failed_components
    )

    if critical_failure:

        return {
            "decision": "REPAIR_REQUIRED",
            "priority": "HIGH",
            "reason": (
                "A critical component failed inspection."
            ),
            "failed_components": failed_components,
            "failed_tests": failed_tests,
            "suspected_replacements": suspected_replacements,
            "manual_tests_required": manual_tests
        }

    # --------------------------------------------------------
    # Failed functional tests
    # --------------------------------------------------------

    if failed_tests:

        return {
            "decision": "REPAIR_REQUIRED",
            "priority": "HIGH",
            "reason": (
                "One or more functional tests failed."
            ),
            "failed_components": failed_components,
            "failed_tests": failed_tests,
            "suspected_replacements": suspected_replacements,
            "manual_tests_required": manual_tests
        }

    # --------------------------------------------------------
    # Suspected replacement
    # --------------------------------------------------------

    if suspected_replacements:

        return {
            "decision": "TECHNICIAN_REVIEW_REQUIRED",
            "priority": "MEDIUM",
            "reason": (
                "One or more components show evidence that "
                "may indicate replacement or degradation."
            ),
            "failed_components": failed_components,
            "failed_tests": failed_tests,
            "suspected_replacements": suspected_replacements,
            "manual_tests_required": manual_tests
        }

    # --------------------------------------------------------
    # Inspection incomplete
    # --------------------------------------------------------

    if completeness.get(
        "percentage",
        0
    ) < 100:

        return {
            "decision": "INSPECTION_INCOMPLETE",
            "priority": "MEDIUM",
            "reason": (
                "The device has not completed the full "
                "VeriCore functional inspection."
            ),
            "failed_components": failed_components,
            "failed_tests": failed_tests,
            "suspected_replacements": suspected_replacements,
            "manual_tests_required": manual_tests
        }

    # --------------------------------------------------------
    # No score
    # --------------------------------------------------------

    if score is None:

        return {
            "decision": "TECHNICIAN_REVIEW_REQUIRED",
            "priority": "MEDIUM",
            "reason": (
                "Insufficient diagnostic data is available."
            ),
            "failed_components": failed_components,
            "failed_tests": failed_tests,
            "suspected_replacements": suspected_replacements,
            "manual_tests_required": manual_tests
        }

    # --------------------------------------------------------
    # Complete inspection
    # --------------------------------------------------------

    if score >= 90:

        decision = "READY_FOR_RESALE"
        priority = "NONE"

    elif score >= 80:

        decision = "READY_FOR_RESALE_AFTER_REVIEW"
        priority = "LOW"

    elif score >= 65:

        decision = "REPAIR_RECOMMENDED"
        priority = "MEDIUM"

    elif score >= 50:

        decision = "REPAIR_REQUIRED"
        priority = "HIGH"

    else:

        decision = "RECYCLE_OR_REBUILD"
        priority = "HIGH"

    return {
        "decision": decision,
        "priority": priority,
        "reason": (
            "Full VeriCore inspection completed."
        ),
        "failed_components": failed_components,
        "failed_tests": failed_tests,
        "suspected_replacements": suspected_replacements,
        "manual_tests_required": manual_tests
    }


# ============================================================
# CERTIFICATE
# ============================================================

def certificate_grade(score):
    if score is None:
        return "PENDING"

    if score >= 95:
        return "A+"

    if score >= 90:
        return "A"

    if score >= 80:
        return "B"

    if score >= 70:
        return "C"

    if score >= 60:
        return "D"

    return "E"


def generate_certificate(
    device,
    repair_decision
):
    score = device.get(
        "vericore_score"
    )

    completeness = device.get(
        "inspection_completeness",
        {}
    )

    certificate_id = generate_certificate_id()

    if completeness.get(
        "percentage",
        0
    ) < 100:

        status = "PENDING_MANUAL_INSPECTION"

    elif repair_decision.get(
        "decision"
    ) not in (
        "READY_FOR_RESALE",
        "READY_FOR_RESALE_AFTER_REVIEW"
    ):

        status = "NOT_CERTIFIED"

    else:

        status = "VALID"

    return {
        "certificate_id": certificate_id,

        "vericore_version": VERICORE_VERSION,

        "issued_at": datetime.now().isoformat(
            timespec="seconds"
        ),

        "grade": certificate_grade(
            score
        ),

        "score": score,

        "inspection_completeness": completeness.get(
            "percentage",
            0
        ),

        "decision": repair_decision.get(
            "decision"
        ),

        "certificate_status": status,

        "device_fingerprint": device.get(
            "device_fingerprint"
        )
    }


# ============================================================
# FINAL REPORT
# ============================================================

def build_repair_report(
    device
):
    repair_decision = determine_repair_decision(
        device
    )

    certificate = generate_certificate(
        device,
        repair_decision
    )

    return {
        "vericore": {
            "software": "VeriCore",
            "version": VERICORE_VERSION,
            "inspection_type": (
                "DEVICE_DIAGNOSTIC_AND_REPAIR_ASSESSMENT"
            ),
            "inspection_timestamp": datetime.now().isoformat(
                timespec="seconds"
            )
        },

        "device": device,

        "repair_decision": repair_decision,

        "certificate": certificate
    }


# ============================================================
# TERMINAL DISPLAY
# ============================================================

def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_battery_summary(battery):
    print_header("BATTERY DIAGNOSTICS")

    print(f"Status             : {battery.get('status', 'UNKNOWN')}")

    health = battery.get("health_percent")
    print(f"Health             : {health if health is not None else 'unreadable'}{'%' if health is not None else ''}")

    cycles = battery.get("cycles")
    print(f"Cycles             : {cycles if cycles is not None else 'unreadable'}")

    reference_capacity = battery.get("reference_capacity_mAh")
    print(f"Reference Capacity : {reference_capacity if reference_capacity is not None else 'unavailable'}{' mAh' if reference_capacity is not None else ''}")

    estimated_capacity = battery.get("estimated_current_capacity_mAh")
    print(f"Estimated Capacity : {estimated_capacity if estimated_capacity is not None else 'unavailable'}{' mAh' if estimated_capacity is not None else ''}")

    capacity_loss = battery.get("estimated_capacity_loss_mAh")
    print(f"Estimated Loss     : {capacity_loss if capacity_loss is not None else 'unavailable'}{' mAh' if capacity_loss is not None else ''}")

    calculation = battery.get("capacity_calculation")
    if calculation:
        print(f"Calculation        : {calculation}")

    print(f"Capacity Accuracy  : {battery.get('capacity_accuracy', 'UNKNOWN')}")
    print(f"Cycle Assessment   : {battery.get('cycle_assessment', 'UNKNOWN')}")

    expected_cycles = battery.get("reference_cycle_life")
    print(f"Reference Cycles   : {expected_cycles if expected_cycles is not None else 'unavailable'}")

    expected_wattage = battery.get("reference_charging_max_w")
    print(f"Expected Max Charge: ~{expected_wattage} W" if expected_wattage is not None else "Expected Max Charge: unavailable")

    temperature = battery.get("temperature_c")
    print(f"Temperature        : {temperature if temperature is not None else 'unreadable'}{' °C' if temperature is not None else ''}")

    voltage = battery.get("voltage_mv")
    print(f"Voltage            : {voltage if voltage is not None else 'unreadable'}{' mV' if voltage is not None else ''}")

    charging = battery.get("charging")
    charging_display = "unreadable" if charging is None else ("Charging" if charging else "Not charging")
    print(f"Charging           : {charging_display}")

    manual_input = battery.get("manual_input", [])
    if manual_input:
        print(f"Manual Input       : {', '.join(manual_input)}")

    warning = battery.get("warning")
    if warning:
        print(f"Warning            : {warning}")


def print_component_summary(
    components
):
    print_header(
        "COMPONENT ANALYSIS"
    )

    for name, component in components.items():

        print(
            f"\n{name.upper()}"
        )

        print(
            f"  Status     : "
            f"{component.get('status')}"
        )

        print(
            f"  Confidence : "
            f"{component.get('confidence')}"
        )

        evidence = component.get(
            "evidence",
            []
        )

        for item in evidence:
            print(
                f"  Evidence   : "
                f"{item}"
            )

        warning = component.get(
            "warning"
        )

        if warning:

            print(
                f"  Warning    : "
                f"{warning}"
            )


def print_functional_summary(
    functional_tests
):
    print_header(
        "FUNCTIONAL TESTS"
    )

    for name, test in functional_tests.items():

        print(
            f"{name.upper():24} "
            f"{test.get('status')}"
        )

        evidence = test.get(
            "evidence"
        )

        if evidence:
            print(
                f"  └─ {evidence}"
            )


def print_report(report):

    device = report[
        "device"
    ]

    scores = device.get(
        "scores",
        {}
    )

    decision = report[
        "repair_decision"
    ]

    certificate = report[
        "certificate"
    ]

    print_header(
        "VERICORE v3.2 – DEVICE DIAGNOSTIC REPORT"
    )

    print(
        f"Platform           : "
        f"{device.get('platform')}"
    )

    print(
        f"Device             : "
        f"{device.get('device_name', 'Unknown')}"
    )

    if device.get("model"):

        print(
            f"Model              : "
            f"{device.get('model')}"
        )

    if device.get("model_identifier"):

        print(
            f"Model Identifier   : "
            f"{device.get('model_identifier')}"
        )

    if device.get("brand"):

        print(
            f"Brand              : "
            f"{device.get('brand')}"
        )

    if device.get("ios_version"):

        print(
            f"iOS                : "
            f"{device.get('ios_version')}"
        )

    if device.get("android_version"):

        print(
            f"Android            : "
            f"{device.get('android_version')}"
        )

    storage = device.get(
        "storage",
        {}
    )

    if isinstance(storage, dict):

        print(
            f"Storage            : "
            f"{storage.get('total', 'unreadable')}"
        )

    else:

        print(
            f"Storage            : "
            f"{storage}"
        )

    if device.get("ram_size"):

        print(
            f"RAM                : "
            f"{device.get('ram_size')}"
        )

    if device.get("serial"):

        print(
            f"Serial             : "
            f"{device.get('serial')}"
        )

    if device.get("imei"):

        print(
            f"IMEI               : "
            f"{device.get('imei')}"
        )

    print(
        f"Activation         : "
        f"{device.get('activation_state', 'Unknown')}"
    )

    sales_origin = device.get(
        "sales_origin",
        {}
    )

    if isinstance(
        sales_origin,
        dict
    ):

        print(
            f"Sales Origin       : "
            f"{sales_origin.get('origin', 'UNKNOWN')}"
        )

    print()

    # --------------------------------------------------------
    # Scores
    # --------------------------------------------------------

    print_header(
        "VERICORE SCORES"
    )

    score = scores.get(
        "score"
    )

    print(
        f"Overall Score      : "
        f"{score if score is not None else 'PENDING'}"
        f"{'/100' if score is not None else ''}"
    )

    print(
        f"Component Score    : "
        f"{scores.get('component_score', 'PENDING')}"
    )

    print(
        f"Functional Score   : "
        f"{scores.get('functional_score', 'PENDING')}"
    )

    print(
        f"Battery Score      : "
        f"{scores.get('battery_score', 'PENDING')}"
    )

    print(
        f"Score Confidence   : "
        f"{scores.get('confidence', 'LOW')}"
    )

    completeness = device.get(
        "inspection_completeness",
        {}
    )

    print(
        f"Inspection         : "
        f"{completeness.get('percentage', 0)}%"
    )

    print(
        f"Inspection Status  : "
        f"{completeness.get('status', 'UNKNOWN')}"
    )

    # --------------------------------------------------------
    # Battery
    # --------------------------------------------------------

    print_battery_summary(
        device.get(
            "battery",
            {}
        )
    )

    # --------------------------------------------------------
    # Components
    # --------------------------------------------------------

    print_component_summary(
        device.get(
            "components",
            {}
        )
    )

    # --------------------------------------------------------
    # Functional
    # --------------------------------------------------------

    print_functional_summary(
        device.get(
            "functional_tests",
            {}
        )
    )

    # --------------------------------------------------------
    # Repair decision
    # --------------------------------------------------------

    print_header(
        "REPAIR DECISION"
    )

    print(
        f"Decision           : "
        f"{decision.get('decision')}"
    )

    print(
        f"Priority           : "
        f"{decision.get('priority')}"
    )

    print(
        f"Reason             : "
        f"{decision.get('reason')}"
    )

    failed_components = decision.get(
        "failed_components",
        []
    )

    if failed_components:

        print(
            "\nFailed Components:"
        )

        for item in failed_components:
            print(
                f"  • {item}"
            )

    failed_tests = decision.get(
        "failed_tests",
        []
    )

    if failed_tests:

        print(
            "\nFailed Tests:"
        )

        for item in failed_tests:
            print(
                f"  • {item}"
            )

    suspected = decision.get(
        "suspected_replacements",
        []
    )

    if suspected:

        print(
            "\nReplacement Suspected:"
        )

        for item in suspected:
            print(
                f"  • {item}"
            )

    manual = decision.get(
        "manual_tests_required",
        []
    )

    if manual:

        print(
            "\nManual Tests Remaining:"
        )

        for item in manual:
            print(
                f"  • {item}"
            )

    # --------------------------------------------------------
    # Certificate
    # --------------------------------------------------------

    print_header(
        "VERICORE CERTIFICATE"
    )

    print(
        f"Certificate ID     : "
        f"{certificate.get('certificate_id')}"
    )

    print(
        f"Grade              : "
        f"{certificate.get('grade')}"
    )

    print(
        f"Score              : "
        f"{certificate.get('score', 'PENDING')}"
    )

    print(
        f"Inspection         : "
        f"{certificate.get('inspection_completeness', 0)}%"
    )

    print(
        f"Status             : "
        f"{certificate.get('certificate_status')}"
    )


# ============================================================
# REPORT EXPORT
# ============================================================

def save_report(
    report,
    filename=None
):
    if filename is None:

        certificate_id = report[
            "certificate"
        ][
            "certificate_id"
        ]

        filename = (
            f"{certificate_id}_report.json"
        )

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                report,
                file,
                indent=4,
                ensure_ascii=False
            )

        return filename

    except OSError as error:

        print(
            f"[!] Could not save report: {error}"
        )

        return None


# ============================================================
# DEVICE DETECTION
# ============================================================

def detect_device(parts_check=None):

    # --------------------------------------------------------
    # iOS
    # --------------------------------------------------------

    if ios_available():

        try:

            ios = detect_ios(parts_check)

            if ios:
                return ios

        except Exception as error:

            print(
                f"[!] iOS detection error: {error}"
            )

    # --------------------------------------------------------
    # Android
    # --------------------------------------------------------

    if android_available():

        try:

            android = detect_android()

            if android:
                return android

        except Exception as error:

            print(
                f"[!] Android detection error: {error}"
            )

    return None


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="VeriCore device inspector"
    )

    parser.add_argument(
        "--parts-check",
        default=None,
        help=(
            "Path to a parts_check.json produced by "
            "parts_check_capture.py (OCR-verified genuine-parts "
            "results for battery/display/camera)."
        )
    )

    parser.add_argument(
        "--skip-manual",
        action="store_true",
        help=(
            "Skip all interactive manual-test prompts (battery, "
            "functional tests, component inspection). Items that "
            "would have been prompted stay MANUAL_TEST_REQUIRED."
        )
    )

    args = parser.parse_args()

    global SKIP_MANUAL_PROMPTS
    SKIP_MANUAL_PROMPTS = args.skip_manual

    parts_check = load_parts_check_result(
        args.parts_check
    )

    print()

    print(
        "╔══════════════════════════════════════════════════════════════╗"
    )

    print(
        "║              VERICORE v3.2 DEVICE INSPECTOR                ║"
    )

    print(
        "║       Diagnostic & Repair Decision Engine                  ║"
    )

    print(
        "╚══════════════════════════════════════════════════════════════╝"
    )

    print()

    print(
        "[*] Detecting connected device..."
    )

    device = detect_device(parts_check)

    if not device:

        print()

        print(
            "[✖] No supported device detected."
        )

        print()

        print(
            "iPhone:"
        )

        print(
            "  • Install libimobiledevice"
        )

        print(
            "  • Connect the iPhone by USB"
        )

        print(
            "  • Unlock the iPhone"
        )

        print(
            "  • Trust the computer"
        )

        print()

        print(
            "Android:"
        )

        print(
            "  • Install Android Platform Tools"
        )

        print(
            "  • Enable USB debugging"
        )

        print(
            "  • Accept the computer authorization prompt"
        )

        return

    print()

    print(
        "[✔] Device detected successfully."
    )

    report = build_repair_report(
        device
    )

    print_report(
        report
    )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    filename = save_report(
        report
    )

    if filename:

        print()

        print(
            f"[✔] JSON report saved: {filename}"
        )

    # --------------------------------------------------------
    # Raw JSON
    # --------------------------------------------------------

    print_header(
        "RAW VERICORE JSON"
    )

    print(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()