import styles from './Contacts.module.css'
import {useRef, useState} from "react";
import * as React from "react";
import type Engine from "../../../engine/Engine.ts";
import Contact from "./contact/Contact.tsx";

type Props = {
    engineRef: React.RefObject<Engine | null>
}

export default function Contacts(props: Props) {
    const [contacts, setContacts] = useState<number[]>([])
    const inputRef = useRef<HTMLInputElement | null>(null);
    const [error, setError] = useState<string | null>(null)

    return (
        <div className={styles.Contacts}>
            <div className={styles.Search}>
                <input ref={inputRef} placeholder={"🔎 account id"}/>
                <button onClick={async () => {
                    setContacts([])
                    if (inputRef.current === null) return

                    const response = await fetch(`/api/accounts/${inputRef.current.value}/contacts`);
                    if (!response.ok) setError('failed to get contacts of a specific user from the backend')

                    const contacts: number[] = await response.json()

                    if (contacts.length === 0) setError('contact list is empty'); else setError(null);
                    setContacts(contacts)
                }}>show</button>

            </div>
            <div className={styles.Container}>
                {error !== null && <h3 className={styles.Error}>{error}</h3>}

                {contacts.map((account_id) => <Contact key={account_id} account_id={account_id} account_name={props.engineRef.current?.getAccountName(account_id) ?? "no name"}/>)}
            </div>
        </div>
    )
}