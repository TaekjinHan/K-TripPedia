/**
 * ConfidenceBadge -- solo_ok_level을 시각적 뱃지로 표시
 */
'use client';

import styles from './ConfidenceBadge.module.css';
import { CONFIDENCE_LABELS } from '@/lib/constants';
import type { SoloOkLevel } from '@/lib/types';
import { useLanguageContext } from '@/contexts/LanguageContext';
import type { AppLanguage } from '@/locales';

interface ConfidenceBadgeProps {
    level: SoloOkLevel;
    lang?: AppLanguage | 'en';
    size?: 'sm' | 'md';
}

export default function ConfidenceBadge({
    level,
    lang,
    size = 'sm',
}: ConfidenceBadgeProps) {
    const { lang: contextLang } = useLanguageContext();
    const resolvedLang = lang ?? contextLang;
    const label = CONFIDENCE_LABELS[level]?.[resolvedLang] ?? level;

    return (
        <span
            className={`${styles.badge} ${styles[size]}`}
            data-level={level}
        >
            {label}
        </span>
    );
}
