/**
 * ConfidenceBadge -- solo_ok_level을 시각적 뱃지로 표시
 */
import styles from './ConfidenceBadge.module.css';
import { CONFIDENCE_LABELS } from '@/lib/constants';
import type { SoloOkLevel } from '@/lib/types';

interface ConfidenceBadgeProps {
    level: SoloOkLevel;
    lang?: 'ja' | 'ko' | 'en';
    size?: 'sm' | 'md';
}

export default function ConfidenceBadge({
    level,
    lang = 'ja',
    size = 'sm',
}: ConfidenceBadgeProps) {
    const label = CONFIDENCE_LABELS[level]?.[lang] ?? level;

    return (
        <span
            className={`${styles.badge} ${styles[size]}`}
            data-level={level}
        >
            {label}
        </span>
    );
}
