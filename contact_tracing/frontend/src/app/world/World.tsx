import styles from './World.module.css'
import {useEffect, useRef, useState} from "react";
import Engine from '../../engine/Engine'
import {useCookies} from "react-cookie";
import * as React from "react";

type Props = {
    engineRef: React.RefObject<Engine | null>

    setCamera: React.Dispatch<React.SetStateAction<{
        x: number,
        y: number,
    }>>

    setPosition: React.Dispatch<React.SetStateAction<{
        x: number,
        y: number,
    }>>
}

export type Account = {
    account_name: string,
    account_id: number,
    x: number,
    y: number,
}

export type Dimensions = {
    w: number,
    h: number,
}

export default function World(props: Props) {
    const [cookies] = useCookies(['account_id'])

    const [hoveredAccount, setHoveredAccount] = useState<Account | null>(null)
    const [cursor, setCursor] = useState({x: 0, y: 0})

    const canvasRef = useRef<HTMLCanvasElement | null>(null)
    const intervalRef = useRef<number | null>(null)

    useEffect(() => {
        let cancelled = false;

        const init = async () => {
            const response = await fetch('/api/world/dimensions');
            if (!response.ok) throw new Error('failed to acquire world dimensions from the backend server');

            const response_auth = await fetch('/api/auth/check');
            if (!response_auth.ok) throw new Error('failed to authenticate');

            const response_accounts = await fetch('/api/accounts');
            if (!response_accounts.ok) throw new Error('failed to get accounts');

            const dimensions: Dimensions = await response.json();
            const accounts: Account[] = await response_accounts.json();
            const account: Account = await response_auth.json();

            if (cancelled) return;

            if (props.engineRef.current) {
                props.engineRef.current.stop();
            }

            const engine = new Engine(canvasRef.current!, dimensions, account, accounts, (account, cursor) => {
                setHoveredAccount(account)
                setCursor(cursor)
            })
            engine.start()

            props.engineRef.current = engine;

            intervalRef.current = window.setInterval(() => {
                props.setCamera(engine.getCamera())
                props.setPosition(engine.getPosition())
            }, 100)
        }

        init()

        return () => {
            cancelled = true

            if (intervalRef.current !== null) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }

            if (props.engineRef.current !== null) {
                props.engineRef.current.stop()
                props.engineRef.current = null
            }
        }
    }, [cookies.account_id]);

    return (
        <div className={styles.World}>
            <canvas
                ref={canvasRef}
            />

            {hoveredAccount && (
                <div
                    className={styles.HoveredAccount}

                    style={{
                        left: cursor.x + 12,
                        top: cursor.y + 12,
                    }}
                >
                    <h3><span>account id:</span><span>{hoveredAccount.account_id}</span></h3>
                    <h3><span>account name:</span><span>{hoveredAccount.account_name}</span></h3>
                </div>
            )}
        </div>
    )
}