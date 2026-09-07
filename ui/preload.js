// ============================================================
// FILE 3
// /Users/mac/PycharmProjects/VeryCore/ui/preload.js
// ============================================================

const {
    contextBridge,
    ipcRenderer
} = require('electron');


contextBridge.exposeInMainWorld(
    'vericore',
    {

        // ----------------------------------------------------
        // DEVICE DETECTION
        // ----------------------------------------------------

        detectDevice: () => {

            return ipcRenderer.invoke(
                'detect-device'
            );

        },


        // ----------------------------------------------------
        // RUN DIAGNOSTICS
        // ----------------------------------------------------

        runDiagnostics: () => {

            return ipcRenderer.invoke(
                'run-diagnostics'
            );

        },


        // ----------------------------------------------------
        // BACKWARD COMPATIBILITY
        // ----------------------------------------------------

        diagnoseIPhone: () => {

            return ipcRenderer.invoke(
                'run-diagnostics'
            );

        },


        diagnoseAndroid: () => {

            return ipcRenderer.invoke(
                'run-diagnostics'
            );

        }

    }
);