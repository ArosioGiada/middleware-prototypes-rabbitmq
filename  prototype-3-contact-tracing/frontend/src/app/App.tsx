import styles from './App.module.css'
import World from "./world/World.tsx";
import Sidebar from "./sidebar/Sidebar.tsx";
import {useEffect, useRef, useState} from "react";
import AuthorisationPopup from "./authorisation_popup/AuthorisationPopup.tsx";
import type Engine from "../engine/Engine.ts";

function App() {
    const [camera, setCamera] = useState({x: 0, y: 0})
    const [position, setPosition] = useState({x: 0, y: 0})
    const [authorisationInProgress, setAuthorisationInProgress] = useState(false)
    const engineRef = useRef<Engine | null>(null)

    useEffect(() => {
        const load = async () => {
            const response = await fetch('/api/auth/check', {
                method: 'GET'
            });

            if (response.status == 500) {
                throw new Error('failed to access backend server')
            }

            if (response.ok) {
                setAuthorisationInProgress(false)
            } else {
                setAuthorisationInProgress(true)
            }
        }

        load()
    }, []);

    return (
        <div className={styles.App}>
            {authorisationInProgress && <AuthorisationPopup onClose={() => {setAuthorisationInProgress(false)}}/>}
            <Sidebar camera={camera} position={position} engineRef={engineRef}/>
            <World setCamera={setCamera} setPosition={setPosition} engineRef={engineRef}/>
        </div>
    )
}
export default App
