import styles from './Contact.module.css'

type Props = {
    account_id: number
    account_name: string
}

export default function Contact(props: Props) {
    return (
        <div className={styles.Contact}>
            <h3><span>account id:</span><span>{props.account_id}</span></h3>
            <h3><span>account name:</span><span>{props.account_name}</span></h3>
        </div>
    )
}