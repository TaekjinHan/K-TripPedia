/**
 * TipCard -- 공략 팁 카드
 */
'use client';

import styles from './TipCard.module.css';
import { TIP_LABELS } from '@/lib/constants';
import { useLanguageContext } from '@/contexts/LanguageContext';

interface TipCardProps {
    tipType: string;
    textKo: string;
    textJa?: string | null;
    priority: number;
}

export default function TipCard({ tipType, textKo, textJa, priority }: TipCardProps) {
    const { lang } = useLanguageContext();
    const label = TIP_LABELS[tipType]?.[lang] ?? tipType;

    const bodyText = lang === 'ja' ? textJa || textKo : textKo;
    const subText = lang === 'ja' ? textKo : textJa;

    return (
        <div className={styles.card} data-priority={priority > 70 ? 'high' : 'normal'}>
            <div className={styles.tag}>{label}</div>
            <p className={styles.text}>{bodyText}</p>
            {subText && <p className={styles.textJa}>{subText}</p>}
        </div>
    );
}
