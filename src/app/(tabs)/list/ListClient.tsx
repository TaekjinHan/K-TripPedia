/**
 * ListClient -- 리스트 탭 클라이언트 컴포넌트
 *
 * Supabase에서 places + solo_profile을 가져와서
 * 카드 리스트로 표시 + FilterModal로 필터링
 */
'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import ConfidenceBadge from '@/components/ConfidenceBadge';
import FilterModal, {
    INITIAL_FILTER,
    type FilterState,
} from '@/components/FilterModal';
import { CATEGORY_LABELS } from '@/lib/constants';
import { useTranslation } from '@/hooks/useTranslation';
import { useLanguageContext } from '@/contexts/LanguageContext';
import { getSoloAllowedLabel } from '@/lib/labels';
import type { SoloOkLevel, SoloAllowed } from '@/lib/types';
import styles from './ListClient.module.css';

interface PlaceItem {
    id: string;
    name_ko: string;
    name_ja: string | null;
    category: string;
    address: string;
    solo_ok_level: SoloOkLevel;
    solo_allowed: SoloAllowed;
    counter_seat: string | null;
    best_time_note: string | null;
}

export default function ListClient() {
    const t = useTranslation();
    const { lang } = useLanguageContext();
    const [items, setItems] = useState<PlaceItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<FilterState>(INITIAL_FILTER);
    const [showFilter, setShowFilter] = useState(false);

    useEffect(() => {
        const fetchPlaces = async () => {
            setLoading(true);

            const { data, error } = await supabase
                .from('places')
                .select(`
          id,
          name_ko,
          name_ja,
          category,
          address,
          solo_profile (
            solo_ok_level,
            solo_allowed,
            counter_seat,
            best_time_note
          )
        `)
                .order('name_ko');

            if (error) {
                console.error('[ListClient] Fetch error:', error);
                setLoading(false);
                return;
            }

            const rows: PlaceItem[] = ((data ?? []) as unknown[]).map((r: unknown) => {
                const row = r as {
                    id: string;
                    name_ko: string;
                    name_ja: string | null;
                    category: string;
                    address: string;
                    solo_profile: {
                        solo_ok_level: SoloOkLevel;
                        solo_allowed: SoloAllowed;
                        counter_seat: string | null;
                        best_time_note: string | null;
                    } | null;
                };
                return {
                    id: row.id,
                    name_ko: row.name_ko,
                    name_ja: row.name_ja,
                    category: row.category,
                    address: row.address,
                    solo_ok_level: row.solo_profile?.solo_ok_level ?? 'LOW',
                    solo_allowed: row.solo_profile?.solo_allowed ?? 'YES',
                    counter_seat: row.solo_profile?.counter_seat ?? null,
                    best_time_note: row.solo_profile?.best_time_note ?? null,
                };
            });

            setItems(rows);
            setLoading(false);
        };

        fetchPlaces();
    }, []);

    /** 필터 적용 */
    const filtered = useMemo(() => {
        return items.filter((p) => {
            if (filter.categories.length > 0 && !filter.categories.includes(p.category)) {
                return false;
            }
            if (filter.soloOkLevels.length > 0 && !filter.soloOkLevels.includes(p.solo_ok_level)) {
                return false;
            }
            if (filter.counterSeatOnly && p.counter_seat !== 'Y') {
                return false;
            }
            return true;
        });
    }, [items, filter]);

    const hasActiveFilter =
        filter.categories.length > 0 ||
        filter.soloOkLevels.length > 0 ||
        filter.counterSeatOnly;

    const handleApplyFilter = useCallback((f: FilterState) => {
        setFilter(f);
    }, []);

    return (
        <div className={styles.container}>
            {/* 헤더 */}
            <div className={styles.header}>
                <span className={styles.title}>{t('list.title')}</span>
                <button
                    className={`${styles.filterBtn} ${hasActiveFilter ? styles.filterActive : ''}`}
                    onClick={() => setShowFilter(true)}
                >
                    <svg width={16} height={16} viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <line x1="4" y1="6" x2="20" y2="6" />
                        <line x1="7" y1="12" x2="17" y2="12" />
                        <line x1="10" y1="18" x2="14" y2="18" />
                    </svg>
                    <span>{t('list.filter')}</span>
                    {hasActiveFilter && (
                        <span className={styles.filterCount}>
                            {filter.categories.length +
                                filter.soloOkLevels.length +
                                (filter.counterSeatOnly ? 1 : 0)}
                        </span>
                    )}
                </button>
            </div>

            {/* 결과 수 */}
            <div className={styles.resultBar}>
                {loading
                    ? t('list.loading')
                    : `${filtered.length}${t('list.countSuffix')}`}
            </div>

            {/* 리스트 */}
            {!loading && filtered.length === 0 ? (
                <div className={styles.empty}>
                    {hasActiveFilter
                        ? t('list.emptyFiltered')
                        : t('list.emptyAll')}
                </div>
            ) : (
                <ul className={styles.list}>
                    {filtered.map((p) => (
                        <li key={p.id}>
                            <Link href={`/place/${p.id}`} className={styles.card}>
                                <div className={styles.cardTop}>
                                    <div className={styles.nameGroup}>
                                        <span className={styles.name}>{p.name_ko}</span>
                                        {p.name_ja && (
                                            <span className={styles.nameJa}>{p.name_ja}</span>
                                        )}
                                    </div>
                                    <ConfidenceBadge level={p.solo_ok_level} />
                                </div>
                                <div className={styles.cardMeta}>
                                    <span className={styles.category}>
                                        {CATEGORY_LABELS[p.category]?.[lang] ?? p.category}
                                    </span>
                                    <span className={styles.divider}>|</span>
                                    <span className={styles.allowed}>
                                        {getSoloAllowedLabel(p.solo_allowed, lang)}
                                    </span>
                                    {p.counter_seat === 'Y' && (
                                        <>
                                            <span className={styles.divider}>|</span>
                                            <span className={styles.counter}>{t('list.counter')}</span>
                                        </>
                                    )}
                                </div>
                                <div className={styles.address}>{p.address}</div>
                                {p.best_time_note && (
                                    <div className={styles.timeNote}>{p.best_time_note}</div>
                                )}
                            </Link>
                        </li>
                    ))}
                </ul>
            )}

            {/* 필터 모달 */}
            <FilterModal
                isOpen={showFilter}
                current={filter}
                onApply={handleApplyFilter}
                onClose={() => setShowFilter(false)}
            />
        </div>
    );
}
