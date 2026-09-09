import styles from './Sidebar.module.css'
import Contacts from "./contacts/Contacts.tsx";
import * as React from "react";
import type Engine from "../../engine/Engine.ts";

type Props = {
    engineRef: React.RefObject<Engine | null>
    camera: {x: number, y: number}
    position: {x: number, y: number}
}

export default function Sidebar(props: Props) {
    return (
        <div className={styles.Sidebar}>
            <div className={styles.Coordinates}>
                <h1>cam: [{props.camera.x.toFixed(2)}][{props.camera.y.toFixed(2)}]</h1>
                <h1>pos: [{props.position.x.toFixed(0)}][{props.position.y.toFixed(0)}]</h1>
            </div>


            <Contacts engineRef={props.engineRef}/>
        </div>
    )
}