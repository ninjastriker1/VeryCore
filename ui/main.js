// ============================================================
// FILE 2
// /Users/mac/PycharmProjects/VeryCore/ui/main.js
// ============================================================

const {
    app,
    BrowserWindow,
    ipcMain
} = require('electron');

const path = require('path');
const {
    execFile
} = require('child_process');


let mainWindow = null;


// ============================================================
// CREATE WINDOW
// ============================================================

function createWindow() {

    mainWindow = new BrowserWindow({

        width: 1400,
        height: 900,

        minWidth: 1100,
        minHeight: 700,

        title: 'VeriCore',

        webPreferences: {

            contextIsolation: true,

            nodeIntegration: false,

            preload: path.join(
                __dirname,
                'preload.js'
            )
        }
    });


    mainWindow.loadFile(
        path.join(
            __dirname,
            'index.html'
        )
    );
}


// ============================================================
// RUN PYTHON VERICORE ENGINE
// ============================================================

function runPythonEngine() {

    return new Promise((resolve) => {

        const bridgePath = path.join(
            __dirname,
            '..',
            'engine_bridge.py'
        );


        execFile(
            'python3',
            [
                bridgePath
            ],
            {
                cwd: path.dirname(bridgePath),

                timeout: 60000,

                maxBuffer: 20 * 1024 * 1024
            },

            (error, stdout, stderr) => {

                const rawOutput = (
                    stdout || ''
                ).trim();


                if (!rawOutput) {

                    resolve({

                        success: false,

                        status: 'error',

                        message:
                            stderr ||
                            (
                                error
                                    ? error.message
                                    : 'Python engine returned no data.'
                            )
                    });

                    return;
                }


                try {

                    const result =
                        JSON.parse(rawOutput);

                    resolve(result);

                } catch (parseError) {

                    resolve({

                        success: false,

                        status: 'error',

                        message:
                            'VeriCore Python engine returned invalid JSON.',

                        details: rawOutput,

                        pythonError:
                            stderr || null,

                        parseError:
                            parseError.message
                    });
                }
            }
        );
    });
}


// ============================================================
// DEVICE DETECTION
// ============================================================

ipcMain.handle(
    'detect-device',
    async () => {

        return await runPythonEngine();

    }
);


// ============================================================
// RUN DIAGNOSTICS
// ============================================================

ipcMain.handle(
    'run-diagnostics',
    async () => {

        return await runPythonEngine();

    }
);


// ============================================================
// APPLICATION READY
// ============================================================

app.whenReady().then(() => {

    createWindow();


    app.on(
        'activate',
        () => {

            if (
                BrowserWindow.getAllWindows().length === 0
            ) {

                createWindow();

            }
        }
    );
});


// ============================================================
// APPLICATION CLOSE
// ============================================================

app.on(
    'window-all-closed',
    () => {

        if (
            process.platform !== 'darwin'
        ) {

            app.quit();

        }
    }
);