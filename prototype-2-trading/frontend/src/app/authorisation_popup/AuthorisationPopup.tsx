import styles from './AuthorisationPopup.module.css'
import {useRef} from "react";

type Props = {
    onClose: () => void,
}

export default function AuthorisationPopup(props: Props) {
    const accountNameRef = useRef<HTMLInputElement | null>(null);

    return (
        <div className={styles.AuthorisationPopup}>
            <div className={styles.Inner}>
                <h3>Authorise in the system</h3>

                <input ref={accountNameRef} placeholder={'username'} />

                <button onClick={async () => {
                    if (!accountNameRef.current) return
                    const account_name = accountNameRef.current.value

                    await fetch('/api/auth', {
                        method: 'POST',
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({account_name}),
                    })

                    props.onClose()
                }}>authorise</button>
            </div>
        </div>
    )
}