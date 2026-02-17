/**
 * PlaceCard -- 지도에서 마커 클릭 시 하단에 표시되는 미니 카드
 */
'use client';

import Link from 'next/link';
import ConfidenceBadge from './ConfidenceBadge';
import { CATEGORY_LABELS } from '@/lib/constants';
import { useTranslation } from '@/hooks/useTranslation';
import { useLanguageContext } from '@/contexts/LanguageContext';
import { getSoloAllowedLabel } from '@/lib/labels';
import type { SoloOkLevel, SoloAllowed } from '@/lib/types';
import styles from './PlaceCard.module.css';

export interface PlaceCardData {
    id: string;
    name_ko: string;
    name_ja: string | null;
    category: string;
    address: string;
    solo_ok_level: SoloOkLevel;
    solo_allowed: SoloAllowed;
    min_portions_required: number | null;
    counter_seat: string | null;
    best_time_note: string | null;
}

interface PlaceCardProps {
    place: PlaceCardData;
    onClose?: () => void;
}

export default function PlaceCard({ place, onClose }: PlaceCardProps) {
    const t = useTranslation();
    const { lang } = useLanguageContext();
    const categoryLabel = CATEGORY_LABELS[place.category]?.[lang] ?? place.category;

    return (
        <div className={styles.card}>
            <button className={styles.closeBtn} onClick={onClose} aria-label={t('common.close')}>
                <svg width={18} height={18} viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
            </button>

            <Link href={`/place/${place.id}`} className={styles.cardLink}>
                <div className={styles.header}>
                    <div className={styles.nameGroup}>
                        <span className={styles.name}>{place.name_ko}</span>
                        {place.name_ja && (
                            <span className={styles.nameJa}>{place.name_ja}</span>
                        )}
                    </div>
                    <ConfidenceBadge level={place.solo_ok_level} />
                </div>

                <div className={styles.meta}>
                    <span className={styles.category}>{categoryLabel}</span>
                    <span className={styles.divider}>|</span>
                    <span className={styles.allowed}>{getSoloAllowedLabel(place.solo_allowed, lang)}</span>
                    {place.min_portions_required && place.min_portions_required >= 2 && (
                        <>
                            <span className={styles.divider}>|</span>
                            <span className={styles.portions}>
                                {t('placeDetail.minOrderValue', {
                                    count: place.min_portions_required,
                                })}
                            </span>
                        </>
                    )}
                </div>

                {place.best_time_note && (
                    <div className={styles.timeNote}>
                        {place.best_time_note}
                    </div>
                )}

                <div className={styles.address}>{place.address}</div>

                <div className={styles.cta}>
                    {t('placeDetail.viewDetail')}
                    <svg width={14} height={14} viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <polyline points="9 18 15 12 9 6" />
                    </svg>
                </div>
            </Link>
        </div>
    );
}
