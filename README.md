# VeriCore

VeriCore is a device diagnostic and repair decision engine for iPhone/iOS and Android devices. It collects information exposed by the operating system, evaluates hardware evidence, runs supported functional checks, and writes a JSON technical report.

VeriCore is deliberately conservative: a component is not marked as original merely because the device communicates correctly. Results can include `VERIFIED`, `LIKELY_ORIGINAL`, `UNCERTAIN`, `REPLACEMENT_SUSPECTED`, `MANUAL_TEST_REQUIRED`, and `NOT_AVAILABLE`.

## Features

- iPhone/iOS inspection through `libimobiledevice`
- Android inspection through Android Debug Bridge (ADB)
- Battery, storage, operating system, network, component, and device information
- Automated verification and functional-test scoring
- Repair decision and inspection completeness summaries
- JSON report and VeriCore certificate generation
- Optional Electron desktop interface

## Requirements

- macOS or another platform that provides Python 3 and the required device tools
- Python 3.8 or newer
- For the desktop interface: Node.js 22.12 or newer and npm
- For iPhone/iOS: `libimobiledevice`
- For Android: Android Platform Tools (`adb`)

On macOS with Homebrew:

```bash
brew install libimobiledevice
brew install android-platform-tools
```

Install the device tool that matches the platform you need. VeriCore can inspect either platform from the same installation.

## Command-line usage

From the repository root:

```bash
python3 main.py
```

Optional arguments:

```text
--skip-manual         Skip interactive manual-test prompts.
--parts-check PATH    Load an OCR-verified parts_check.json result.
```

For example:

```bash
python3 main.py --skip-manual
python3 main.py --parts-check path/to/parts_check.json
```

The engine detects a connected supported device, prints a diagnostic report, and writes a JSON report in the repository directory using a certificate-based filename.

Before inspecting a device:

- iPhone: connect it by USB, unlock it, and trust the computer when prompted.
- Android: connect it by USB, enable USB debugging, and accept the computer authorization prompt.

## Desktop interface

The Electron application lives in `ui/` and launches the Python engine through `engine_bridge.py`.

```bash
cd ui
npm install
npm start
```

The UI expects `python3` to be available on `PATH` and uses the same iOS and Android command-line tools as the CLI.

## Project layout

```text
main.py             Core diagnostic and report engine
engine_bridge.py    JSON bridge used by the Electron UI
ui/                 Electron application
*_report.json       Example or generated diagnostic reports
```

## Reports and privacy

Reports may contain serial numbers, UDIDs, device fingerprints, network information, and diagnostic details. Review and redact reports before publishing them. Generated reports are ignored by the repository's `.gitignore` by default.

Diagnostic results are evidence-based estimates, not a guarantee of hardware originality or a substitute for qualified physical inspection. Values unavailable from the operating system are reported as unavailable or uncertain.

## Development

No third-party Python packages are required by the current engine. The Electron development dependency is installed from `ui/package.json`.

There is currently no automated test suite. A basic smoke check for the Python CLI is:

```bash
python3 -m py_compile main.py engine_bridge.py
python3 main.py --help
```

## License

VeriCore is available under the MIT License. See [LICENSE](LICENSE).

The Electron runtime and other bundled dependencies retain their own licenses. See the dependency metadata in `ui/package-lock.json` for details.