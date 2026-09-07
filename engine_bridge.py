#!/usr/bin/env python3

import sys
import json
import importlib.util
from pathlib import Path


# ============================================================
# VERICORE ENGINE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Your actual 5000+ line VeriCore Python engine
ENGINE_PATH = BASE_DIR / "main.py"


# ============================================================
# LOAD VERICORE ENGINE
# ============================================================

def load_engine():

    if not ENGINE_PATH.exists():

        raise FileNotFoundError(
            f"VeriCore engine not found:\n{ENGINE_PATH}"
        )

    spec = importlib.util.spec_from_file_location(
        "vericore_engine",
        ENGINE_PATH
    )

    if spec is None or spec.loader is None:

        raise RuntimeError(
            f"Could not load VeriCore engine:\n{ENGINE_PATH}"
        )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


# ============================================================
# MAKE DATA JSON SAFE
# ============================================================

def json_safe(value):

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool)
    ):
        return value

    if isinstance(value, dict):

        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple)
    ):

        return [
            json_safe(item)
            for item in value
        ]

    return str(value)


# ============================================================
# STATUS LABELS
#
# Turns the engine's internal status vocabulary into short,
# human-readable text for the UI, without changing its meaning.
# ============================================================

STATUS_LABELS = {
    "VERIFIED": "Verified genuine",
    "LIKELY_ORIGINAL": "Likely original",
    "UNCERTAIN": "Uncertain",
    "REPLACEMENT_SUSPECTED": "Replacement suspected",
    "MANUAL_TEST_REQUIRED": "Manual test required",
    "NOT_AVAILABLE": "Not available",
    "PASSED": "Passed",
    "FAILED": "Failed",
}


def status_label(status):
    if not status:
        return None
    return STATUS_LABELS.get(status, status)


# ============================================================
# UI MAPPING — DEVICE (for the detectDevice() IPC channel)
#
# index.html reads, for iPhone:
#   platform, name, model, productType, iosVersion,
#   serialNumber, udid, connection
# and for Android:
#   platform, manufacturer, model, androidVersion,
#   serial, connection
# ============================================================

def map_device_for_ui(device):

    if not device:
        return {}

    platform = device.get("platform")

    if platform == "iOS":

        return {
            "platform": "iPhone",
            "name": device.get("device_name"),
            "model": device.get("model"),
            "productType": device.get("model_identifier"),
            "iosVersion": device.get("ios_version"),
            "serialNumber": device.get("serial"),
            "udid": device.get("udid"),
            "connection": "USB (libimobiledevice)"
        }

    if platform == "Android":

        return {
            "platform": "Android",
            "manufacturer": device.get("manufacturer"),
            "model": device.get("device_name"),
            "androidVersion": device.get("android_version"),
            "serial": device.get("serial"),
            "connection": "USB (ADB)"
        }

    # Unknown/unsupported platform — pass through what we have
    # rather than fabricating fields the engine never produced.
    return {
        "platform": platform
    }


# ============================================================
# UI MAPPING — DIAGNOSTICS (for the runDiagnostics() IPC channel)
#
# index.html reads:
#   data.device.{model, manufacturer, iosVersion, androidVersion,
#                serialNumber, serial, connection, connectionPort}
#   data.battery.{health, designCapacity, cycleCount,
#                 currentCapacity, chargingStatus, temperature,
#                 voltage}
#   data.hardware.{storage, availableStorage, usedStorage, ram,
#                  cpu, camera, sensors}
#   data.verification.{suspiciousComponents, ...}
# ============================================================

def map_diagnostics_for_ui(device, report):

    if not device or not report:
        return {}

    platform = device.get("platform")

    battery_raw = device.get("battery", {}) or {}
    storage_raw = device.get("storage", {}) or {}
    components = device.get("components", {}) or {}

    decision = report.get("repair_decision", {}) or {}
    certificate = report.get("certificate", {}) or {}
    scores = device.get("scores", {}) or {}
    completeness = device.get("inspection_completeness", {}) or {}

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device_section = {
        "model": device.get("model") or device.get("device_name"),

        "manufacturer": (
            "Apple" if platform == "iOS"
            else device.get("manufacturer")
        ),

        "iosVersion": device.get("ios_version"),
        "androidVersion": device.get("android_version"),

        "serialNumber": device.get("serial") if platform == "iOS" else None,
        "serial": device.get("serial") if platform == "Android" else None,

        "connection": (
            "USB (libimobiledevice)" if platform == "iOS"
            else "USB (ADB)" if platform == "Android"
            else None
        ),

        # The engine has no concept of a physical USB port index -
        # left unset rather than invented. The UI already falls
        # back to "Unknown" for undefined values.
        "connectionPort": None
    }

    # --------------------------------------------------------
    # Battery
    #
    # Every value here is labeled for what it actually is
    # (reference vs. estimated), matching VeriCore's own
    # "never overstate certainty" principle from main.py.
    # --------------------------------------------------------

    health = battery_raw.get("health_percent")
    reference_capacity = battery_raw.get("reference_capacity_mAh")
    estimated_capacity = battery_raw.get("estimated_current_capacity_mAh")
    cycles = battery_raw.get("cycles")
    charging = battery_raw.get("charging")
    temperature = battery_raw.get("temperature_c")
    voltage = battery_raw.get("voltage_mv")

    battery_section = {
        "health": (
            f"{health}%" if health is not None else None
        ),

        "designCapacity": (
            f"{reference_capacity} mAh (model reference)"
            if reference_capacity else None
        ),

        "cycleCount": (
            str(cycles) if cycles is not None else None
        ),

        "currentCapacity": (
            f"{estimated_capacity} mAh (estimated)"
            if estimated_capacity else None
        ),

        "chargingStatus": (
            "Charging" if charging is True
            else "Not charging" if charging is False
            else None
        ),

        "temperature": (
            f"{temperature} °C" if temperature is not None else None
        ),

        "voltage": (
            f"{voltage} mV" if voltage is not None else None
        )
    }

    # --------------------------------------------------------
    # Hardware
    #
    # storage/availableStorage/usedStorage come straight from
    # the engine's df-based Android reading / corrected iOS
    # reading. cpu and sensors are left unset - the engine does
    # not collect that data, and fabricating a value would be
    # worse than showing "Unknown".
    # --------------------------------------------------------

    camera_component = components.get("camera", {}) or {}

    hardware_section = {
        "storage": storage_raw.get("total"),
        "availableStorage": storage_raw.get("available"),
        "usedStorage": storage_raw.get("used"),

        "ram": device.get("ram_size") if platform == "Android" else None,

        "cpu": None,

        "camera": status_label(camera_component.get("status")),

        "sensors": None
    }

    # --------------------------------------------------------
    # Verification
    #
    # suspiciousComponents mirrors the repair decision engine's
    # own findings rather than re-deriving anything. The extra
    # fields below aren't read by the current index.html, but
    # are here so the "Verification" panel can be wired to real
    # data instead of the hardcoded checkmarks it uses today.
    # --------------------------------------------------------

    suspicious = []
    suspicious.extend(decision.get("failed_components", []))
    suspicious.extend(decision.get("suspected_replacements", []))
    suspicious.extend(decision.get("failed_tests", []))

    verification_section = {
        "suspiciousComponents": (
            ", ".join(sorted(set(suspicious)))
            if suspicious else "None detected"
        ),

        "deviceDetected": True,
        "connectionStable": True,
        "diagnosticsComplete": completeness.get("percentage", 0) == 100,

        "inspectionCompletenessPercent": completeness.get("percentage", 0),
        "manualTestsRemaining": decision.get("manual_tests_required", []),

        "overallScore": scores.get("score"),
        "decision": decision.get("decision"),
        "priority": decision.get("priority"),
        "certificateGrade": certificate.get("grade")
    }

    return {
        "device": device_section,
        "battery": battery_section,
        "hardware": hardware_section,
        "verification": verification_section
    }


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        # ----------------------------------------------------
        # LOAD YOUR REAL VERICORE ENGINE
        # ----------------------------------------------------

        engine = load_engine()


        # ----------------------------------------------------
        # PREVENT INTERACTIVE INPUT
        #
        # Electron must never get stuck waiting for input()
        # from the Python engine. This patches every manual-
        # prompt entry point the engine currently has
        # (collect_manual_battery_data) and, defensively, any
        # that a future engine version might add
        # (collect_manual_functional_tests /
        # collect_manual_component_checks) - patched only if
        # present, so this stays safe against older or newer
        # copies of main.py.
        # ----------------------------------------------------

        noop_patches = {
            "collect_manual_battery_data":
                lambda battery, reference_profile: battery,

            "collect_manual_functional_tests":
                lambda functional_tests: functional_tests,

            "collect_manual_component_checks":
                lambda components: components,
        }

        for name, noop in noop_patches.items():

            if hasattr(engine, name):
                setattr(engine, name, noop)

        if hasattr(engine, "SKIP_MANUAL_PROMPTS"):
            engine.SKIP_MANUAL_PROMPTS = True


        # ----------------------------------------------------
        # DETECT DEVICE
        # ----------------------------------------------------

        device = engine.detect_device()


        if not device:

            print(
                json.dumps(
                    {
                        "success": False,

                        "status": "no-device",

                        "message":
                            "No supported iPhone or Android "
                            "device was detected."
                    },

                    ensure_ascii=False
                )
            )

            return 0


        # ----------------------------------------------------
        # BUILD COMPLETE VERICORE REPORT
        # ----------------------------------------------------

        report = engine.build_repair_report(
            device
        )


        # ----------------------------------------------------
        # SHAPE FOR THE UI
        # ----------------------------------------------------

        ui_device = map_device_for_ui(device)
        ui_diagnostics = map_diagnostics_for_ui(device, report)

        platform_label = (
            "iPhone" if device.get("platform") == "iOS"
            else device.get("platform")
        )


        # ----------------------------------------------------
        # RETURN EVERYTHING TO ELECTRON
        #
        # "device" matches what the detectDevice() IPC channel
        # expects. "diagnostics" matches what the
        # runDiagnostics() IPC channel expects. "raw" carries
        # the full untouched engine output for anything the UI
        # doesn't map yet.
        # ----------------------------------------------------

        result = {

            "success": True,

            "status": "connected",

            "message": f"{platform_label} detected and diagnostics completed.",

            "device": ui_device,

            "diagnostics": ui_diagnostics,

            "raw": {
                "device": json_safe(device),
                "report": json_safe(report)
            }
        }


        print(
            json.dumps(
                result,
                ensure_ascii=False
            )
        )


        return 0


    except Exception as error:

        print(
            json.dumps(
                {
                    "success": False,

                    "status": "error",

                    "message": str(error)
                },

                ensure_ascii=False
            )
        )

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )