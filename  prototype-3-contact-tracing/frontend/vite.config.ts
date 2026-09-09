import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react-swc'
import fs from "node:fs";

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        https: {
            cert: fs.readFileSync('../assets/localhost.pem'),
            key: fs.readFileSync('../assets/localhost-key.pem'),
        },
        proxy: {
            "/api": {
                target: "https://localhost:8080",
                changeOrigin: true,
                secure: false,
            }
        }
    }
})
