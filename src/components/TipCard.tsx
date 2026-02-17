/**
 * TipCard -- 공략 팁 카드
 */
import styles from './TipCard.module.css';
import { TIP_LABELS } from '@/lib/constants';

interface TipCardProps {
    tipType: string;
    textKo: string;
    textJa?: string | null;
    priority: number;
}

export default function TipCard({ tipType, textKo, textJa, priority }: TipCardProps) {
    const label = TIP_LABELS[tipType]?.ja ?? tipType;

    return (
        <div className={styles.card} data-priority={priority > 70 ? 'high' : 'normal'}>
            <div className={styles.tag}>{label}</div>
            <p className={styles.text}>{textKo}</p>
            {textJa && <p className={styles.textJa}>{textJa}</p>}
        </div>
    );
}
