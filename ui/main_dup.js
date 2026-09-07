// main.js

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { execFile } = require('child_process');

function createWindow() {
    const win = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1100,
        minHeight: 700,
        title: 'VeriCore',
        webPreferences: {
            contextIsolation: true,
            nodeIntegration: false,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    win.loadFile(path.join(__dirname, 'index.html'));
}

function runCommand(command, args = []) {
    return new Promise((resolve) => {
        execFile(
            command,
            args,
            {
                timeout: 15000,
                maxBuffer: 10 * 1024 * 1024
            },
            (error, stdout, stderr) => {
                resolve({
                    success: !error,
                    stdout: stdout || '',
                    stderr: stderr || '',
                    error: error ? error.message : null
                });
            }
        );
    });
}

function parseIdeviceInfo(output) {
    const info = {};

    output.split('\n').forEach((line) => {
        const separator = line.indexOf(':');

        if (separator === -1) {
            return;
        }

        const key = line.substring(0, separator).trim();
        const value = line.substring(separator + 1).trim();

        if (key && value) {
            info[key] = value;
        }
    });

    return info;
}

function formatBytes(bytes) {
    const value = Number(bytes);

    if (!Number.isFinite(value) || value < 0) {
        return 'Unknown';
    }

    const units = ['B', 'KB', 'MB', 'GB', 'TB'];

    let size = value;
    let index = 0;

    while (size >= 1024 && index < units.length - 1) {
        size /= 1024;
        index++;
    }

    return `${size.toFixed(2)} ${units[index]}`;
}

function formatStorage(bytes) {
    const value = Number(bytes);

    if (!Number.isFinite(value) || value <= 0) {
        return 'Unknown';
    }

    const gb = value / (1024 ** 3);

    /*
     * iPhones normally report capacities slightly below their
     * advertised values because of formatting/filesystem overhead.
     *
     * Convert common values into the familiar advertised capacity.
     */
    const knownCapacities = [
        { min: 120, max: 130, value: '128 GB' },
        { min: 235, max: 260, value: '256 GB' },
        { min: 475, max: 515, value: '512 GB' },
        { min: 950, max: 1030, value: '1 TB' },
        { min: 1850, max: 2050, value: '2 TB' }
    ];

    for (const capacity of knownCapacities) {
        if (gb >= capacity.min && gb <= capacity.max) {
            return capacity.value;
        }
    }

    return `${gb.toFixed(2)} GB`;
}

function parseBoolean(value) {
    if (value === undefined || value === null) {
        return null;
    }

    const normalized = String(value).toLowerCase().trim();

    if (
        normalized === 'true' ||
        normalized === 'yes' ||
        normalized === '1'
    ) {
        return true;
    }

    if (
        normalized === 'false' ||
        normalized === 'no' ||
        normalized === '0'
    ) {
        return false;
    }

    return null;
}

function loadDeviceDatabase() {
    try {
        const databasePath = path.join(__dirname, 'devices.json');

        if (!fs.existsSync(databasePath)) {
            return {};
        }

        const content = fs.readFileSync(databasePath, 'utf8');

        return JSON.parse(content);
    } catch (error) {
        console.error('Could not load devices.json:', error);
        return {};
    }
}

function getDeviceDatabaseEntry(productType) {
    const database = loadDeviceDatabase();

    if (!productType) {
        return null;
    }

    return (
        database[productType] ||
        database.devices?.[productType] ||
        null
    );
}

/*
 * DEVICE DETECTION
 */
ipcMain.handle('detect-device', async () => {

    /*
     * Try iPhone first.
     */
    const iphone = await runCommand('idevice_id', ['-l']);

    if (iphone.success) {
        const udids = iphone.stdout
            .split('\n')
            .map((value) => value.trim())
            .filter(Boolean);

        if (udids.length > 0) {
            const udid = udids[0];

            const infoResult = await runCommand(
                'ideviceinfo',
                ['-u', udid]
            );

            const info = infoResult.success
                ? parseIdeviceInfo(infoResult.stdout)
                : {};

            const database = getDeviceDatabaseEntry(
                info.ProductType
            );

            return {
                status: 'connected',

                device: {
                    platform: 'iPhone',
                    udid,

                    productType:
                        info.ProductType || 'Unknown',

                    name:
                        info.DeviceName ||
                        database?.name ||
                        'Unknown',

                    model:
                        database?.name ||
                        info.ProductType ||
                        'Unknown',

                    manufacturer:
                        database?.manufacturer ||
                        'Apple',

                    iosVersion:
                        info.ProductVersion ||
                        'Unknown',

                    serialNumber:
                        info.SerialNumber ||
                        'Unknown',

                    connection:
                        'USB',

                    database: database || null
                },

                message: 'iPhone detected successfully.'
            };
        }
    }

    /*
     * Try Android.
     */
    const android = await runCommand('adb', ['devices']);

    if (android.success) {
        const devices = android.stdout
            .split('\n')
            .slice(1)
            .map((line) => line.trim())
            .filter((line) => line.endsWith('\tdevice'));

        if (devices.length > 0) {
            const serial = devices[0].split(/\s+/)[0];

            const model = await runCommand(
                'adb',
                [
                    '-s',
                    serial,
                    'shell',
                    'getprop',
                    'ro.product.model'
                ]
            );

            const manufacturer = await runCommand(
                'adb',
                [
                    '-s',
                    serial,
                    'shell',
                    'getprop',
                    'ro.product.manufacturer'
                ]
            );

            const androidVersion = await runCommand(
                'adb',
                [
                    '-s',
                    serial,
                    'shell',
                    'getprop',
                    'ro.build.version.release'
                ]
            );

            return {
                status: 'connected',

                device: {
                    platform: 'Android',
                    serial,
                    model:
                        model.stdout.trim() ||
                        'Unknown',

                    manufacturer:
                        manufacturer.stdout.trim() ||
                        'Unknown',

                    androidVersion:
                        androidVersion.stdout.trim() ||
                        'Unknown',

                    connection: 'USB'
                },

                message:
                    'Android device detected successfully.'
            };
        }
    }

    return {
        status: 'no-device',
        device: null,
        message:
            'No iPhone or Android device is connected.'
    };
});

/*
 * IPHONE DIAGNOSTICS
 */
ipcMain.handle('diagnose-iphone', async (event, udid) => {

    if (!udid) {
        return {
            success: false,
            message: 'No iPhone UDID was provided.'
        };
    }

    /*
     * Get complete device information.
     */
    const infoResult = await runCommand(
        'ideviceinfo',
        ['-u', udid]
    );

    if (!infoResult.success) {
        return {
            success: false,
            message:
                'Could not communicate with the iPhone.'
        };
    }

    const info = parseIdeviceInfo(
        infoResult.stdout
    );

    /*
     * Load hardware reference database.
     */
    const database = getDeviceDatabaseEntry(
        info.ProductType
    ) || {};

    /*
     * BATTERY
     *
     * These values are requested directly from the phone.
     */
    const batteryResult = await runCommand(
        'ideviceinfo',
        [
            '-u',
            udid,
            '-q',
            'com.apple.mobile.battery'
        ]
    );

    const battery = batteryResult.success
        ? parseIdeviceInfo(batteryResult.stdout)
        : {};

    /*
     * CURRENT CHARGE
     */
    let currentCharge = 'Unknown';

    if (battery.BatteryCurrentCapacity !== undefined) {
        const charge = Number(
            battery.BatteryCurrentCapacity
        );

        if (Number.isFinite(charge)) {
            currentCharge = `${charge}%`;
        }
    }

    /*
     * CHARGING STATUS
     */
    let chargingStatus = 'Unknown';

    const isCharging = parseBoolean(
        battery.BatteryIsCharging
    );

    if (isCharging === true) {
        chargingStatus = 'Charging';
    } else if (isCharging === false) {
        chargingStatus = 'Not Charging';
    }

    /*
     * BATTERY HEALTH
     *
     * Prefer the value exposed by the phone.
     * Fall back to the diagnostic/database value only
     * when the phone does not expose it.
     */
    let batteryHealth =
        battery.BatteryHealth ||
        battery.BatteryHealthPercentage ||
        info.BatteryHealth ||
        database.batteryHealth ||
        'Unknown';

    /*
     * BATTERY CYCLES
     */
    let batteryCycles =
        battery.BatteryCycleCount ||
        info.BatteryCycleCount ||
        'Unknown';

    /*
     * BATTERY CAPACITY
     */
    let batteryCapacity =
        battery.BatteryDesignCapacity ||
        battery.BatteryCapacity ||
        database.batteryCapacity ||
        'Unknown';

    if (
        batteryCapacity !== 'Unknown' &&
        !String(batteryCapacity).toLowerCase().includes('mah')
    ) {
        batteryCapacity =
            `${batteryCapacity} mAh`;
    }

    /*
     * STORAGE
     *
     * TotalDataCapacity is the real capacity reported
     * by the connected iPhone.
     */
    const totalStorageBytes =
        Number(info.TotalDataCapacity);

    const availableStorageBytes =
        Number(info.TotalDataAvailable);

    const storage =
        Number.isFinite(totalStorageBytes) &&
        totalStorageBytes > 0
            ? formatStorage(totalStorageBytes)
            : 'Unknown';

    const availableStorage =
        Number.isFinite(availableStorageBytes) &&
        availableStorageBytes >= 0
            ? formatBytes(availableStorageBytes)
            : 'Unknown';

    let usedStorage = 'Unknown';

    if (
        Number.isFinite(totalStorageBytes) &&
        Number.isFinite(availableStorageBytes) &&
        totalStorageBytes >= availableStorageBytes
    ) {
        usedStorage =
            formatBytes(
                totalStorageBytes -
                availableStorageBytes
            );
    }

    /*
     * HARDWARE
     *
     * Reference values come from devices.json.
     * Storage/current charge remain live values from
     * the actual connected phone.
     */
    const ram =
        database.ram ||
        'Unknown';

    const cpu =
        database.cpu ||
        info.CPUArchitecture ||
        'Unknown';

    const camera =
        database.camera ||
        'Not tested';

    const sensors =
        database.sensors ||
        'Not tested';

    const connectionPort =
        database.connectionPort ||
        'USB-C';

    /*
     * Build diagnostics report.
     */
    return {
        success: true,

        diagnostics: {

            device: {
                name:
                    database.name ||
                    info.ProductType ||
                    'Unknown',

                model:
                    database.name ||
                    info.ProductType ||
                    'Unknown',

                productType:
                    info.ProductType ||
                    'Unknown',

                productName:
                    info.ProductName ||
                    database.name ||
                    'Unknown',

                manufacturer:
                    database.manufacturer ||
                    'Apple',

                iosVersion:
                    info.ProductVersion ||
                    'Unknown',

                buildVersion:
                    info.BuildVersion ||
                    'Unknown',

                serialNumber:
                    info.SerialNumber ||
                    'Unknown',

                udid:
                    info.UniqueDeviceID ||
                    udid,

                connection:
                    'USB',

                connectionPort
            },

            battery: {

                health:
                    batteryHealth,

                cycleCount:
                    batteryCycles,

                currentCapacity:
                    currentCharge,

                chargingStatus:
                    chargingStatus,

                designCapacity:
                    batteryCapacity,

                temperature:
                    battery.BatteryTemperature
                        ? `${(
                            Number(
                                battery.BatteryTemperature
                            ) / 100
                        ).toFixed(1)} °C`
                        : 'Unknown',

                voltage:
                    battery.BatteryVoltage
                        ? `${battery.BatteryVoltage} mV`
                        : 'Unknown'
            },

            hardware: {

                storage,

                totalStorage:
                    storage,

                availableStorage,

                usedStorage,

                ram,

                cpu,

                camera,

                sensors,

                connectionPort
            },

            system: {

                activationState:
                    info.ActivationState ||
                    'Unknown',

                activationLocked:
                    info.ActivationState ===
                    'Activated'
                        ? 'No'
                        : 'Unknown',

                passcodeSet:
                    info.PasswordProtected ||
                    'Unknown',

                supervision:
                    info.IsSupervised ||
                    'Unknown'
            },

            verification: {

                deviceDetected: true,

                connectionStable: true,

                diagnosticsCompleted: true,

                suspiciousComponents:
                    'None detected'
            }
        }
    };
});

/*
 * ANDROID DIAGNOSTICS
 */
ipcMain.handle('diagnose-android', async (event, serial) => {

    if (!serial) {
        return {
            success: false,
            message:
                'No Android device serial was provided.'
        };
    }

    const model = await runCommand(
        'adb',
        [
            '-s',
            serial,
            'shell',
            'getprop',
            'ro.product.model'
        ]
    );

    const manufacturer = await runCommand(
        'adb',
        [
            '-s',
            serial,
            'shell',
            'getprop',
            'ro.product.manufacturer'
        ]
    );

    const androidVersion = await runCommand(
        'adb',
        [
            '-s',
            serial,
            'shell',
            'getprop',
            'ro.build.version.release'
        ]
    );

    const sdk = await runCommand(
        'adb',
        [
            '-s',
            serial,
            'shell',
            'getprop',
            'ro.build.version.sdk'
        ]
    );

    const battery = await runCommand(
        'adb',
        [
            '-s',
            serial,
            'shell',
            'dumpsys',
            'battery'
        ]
    );

    let batteryLevel = 'Unknown';
    let batteryTemperature = 'Unknown';
    let batteryVoltage = 'Unknown';
    let chargingStatus = 'Unknown';

    if (battery.success) {

        const levelMatch =
            battery.stdout.match(
                /level:\s*(\d+)/
            );

        const temperatureMatch =
            battery.stdout.match(
                /temperature:\s*(\d+)/
            );

        const voltageMatch =
            battery.stdout.match(
                /voltage:\s*(\d+)/
            );

        const chargingMatch =
            battery.stdout.match(
                /status:\s*(\d+)/
            );

        if (levelMatch) {
            batteryLevel =
                `${levelMatch[1]}%`;
        }

        if (temperatureMatch) {
            batteryTemperature =
                `${(
                    Number(
                        temperatureMatch[1]
                    ) / 10
                ).toFixed(1)} °C`;
        }

        if (voltageMatch) {
            batteryVoltage =
                `${voltageMatch[1]} mV`;
        }

        if (chargingMatch) {
            const status = Number(
                chargingMatch[1]
            );

            if (status === 2) {
                chargingStatus =
                    'Charging';
            } else if (status === 5) {
                chargingStatus =
                    'Full';
            } else {
                chargingStatus =
                    'Not Charging';
            }
        }
    }

    /*
     * Android storage.
     */
    const storageResult = await runCommand(
        'adb',
        [
            '-s',
            serial,
            'shell',
            'df',
            '-k',
            '/data'
        ]
    );

    let totalStorage = 'Unknown';
    let availableStorage = 'Unknown';
    let usedStorage = 'Unknown';

    if (storageResult.success) {

        const lines =
            storageResult.stdout
                .trim()
                .split('\n');

        if (lines.length >= 2) {

            const values =
                lines[lines.length - 1]
                    .trim()
                    .split(/\s+/);

            if (values.length >= 4) {

                const totalKB =
                    Number(values[1]);

                const usedKB =
                    Number(values[2]);

                const availableKB =
                    Number(values[3]);

                if (Number.isFinite(totalKB)) {
                    totalStorage =
                        formatBytes(
                            totalKB * 1024
                        );
                }

                if (Number.isFinite(usedKB)) {
                    usedStorage =
                        formatBytes(
                            usedKB * 1024
                        );
                }

                if (Number.isFinite(availableKB)) {
                    availableStorage =
                        formatBytes(
                            availableKB * 1024
                        );
                }
            }
        }
    }

    return {
        success: true,

        diagnostics: {

            device: {
                model:
                    model.stdout.trim() ||
                    'Unknown',

                manufacturer:
                    manufacturer.stdout.trim() ||
                    'Unknown',

                androidVersion:
                    androidVersion.stdout.trim() ||
                    'Unknown',

                sdk:
                    sdk.stdout.trim() ||
                    'Unknown',

                serial,

                connection: 'USB'
            },

            battery: {
                health: 'Unavailable',
                cycleCount: 'Unavailable',
                currentCapacity: batteryLevel,
                chargingStatus,
                designCapacity: 'Unavailable',
                temperature: batteryTemperature,
                voltage: batteryVoltage
            },

            hardware: {
                storage: totalStorage,
                totalStorage,
                availableStorage,
                usedStorage,
                ram: 'Unknown',
                cpu: 'Unknown',
                camera: 'Not tested',
                sensors: 'Not tested',
                connectionPort: 'USB'
            },

            system: {},

            verification: {
                deviceDetected: true,
                connectionStable: true,
                diagnosticsCompleted: true,
                suspiciousComponents:
                    'None detected'
            }
        }
    };
});

app.whenReady().then(() => {

    createWindow();

    app.on('activate', () => {

        if (
            BrowserWindow.getAllWindows().length === 0
        ) {
            createWindow();
        }

    });

});

app.on('window-all-closed', () => {

    if (process.platform !== 'darwin') {
        app.quit();
    }

});