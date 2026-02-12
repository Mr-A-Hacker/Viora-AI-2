import { contextBridge } from 'electron'

if (process.contextIsolated) {
    try {
        contextBridge.exposeInMainWorld('electron', {
            // expose APIs here
        })
    } catch (error) {
        console.error(error)
    }
} else {
    // window.electron = electronAPI
}
