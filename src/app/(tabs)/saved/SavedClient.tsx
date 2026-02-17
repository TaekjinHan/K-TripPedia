/**
 * SavedClient -- Saved 탭 클라이언트 컴포넌트
 *
 * 전략:
 * 1. 항상 로컬 스냅샷으로 즉시 렌더(오프라인 대응)
 * 2. 온라인이면 Supabase bookmarks -> 로컬 스냅샷 덮어쓰기(정합성 확보)
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { ensureAnonSession } from '@/lib/auth';
import {
    getSavedPlaces,
    replaceSavedWithPlaces,
    type PlaceSummary,
} from '@/lib/savedSnapshot';
import { useTranslation } from '@/hooks/useTranslation';
import { useLanguageContext } from '@/contexts/LanguageContext';
import { CONFIDENCE_LABELS } from '@/lib/constants';
import styles from './SavedClient.module.css';

type SyncStatus = 'offline' | 'syncing' | 'ready';

export default function SavedClient() {
    const t = useTranslation();
    const { lang } = useLanguageContext();
    const [places, setPlaces] = useState<PlaceSummary[]>([]);
    const [status, setStatus] = useState<SyncStatus>('ready');

    // 1) 로컬 스냅샷으로 즉시 렌더
    useEffect(() => {
        setPlaces(getSavedPlaces());
    }, []);

    // 2) 온라인이면 서버 동기화
    useEffect(() => {
        const syncFromServer = async () => {
            if (!navigator.onLine) {
                setStatus('offline');
                return;
            }
            setStatus('syncing');

            try {
                const userId = await ensureAnonSession();
                if (!userId) {
                    setStatus('ready');
                    return;
                }

                const { data: bookmarkRows } = await supabase
                    .from('bookmarks')
                    .select('place_id')
                    .eq('user_id', userId);

                const ids = (bookmarkRows ?? []).map((r) => r.place_id).filter(Boolean);
                if (!ids.length) {
                    replaceSavedWithPlaces([]);
                    setPlaces([]);
                    setStatus('ready');
                    return;
                }

                const { data: placeRows, error: pErr } = await supabase
                    .from('places')
                    .select('id,name_ko,name_ja,category,address,lat,lng')
                    .in('id', ids);

                if (pErr) throw pErr;

                const { data: profRows } = await supabase
                    .from('solo_profile')
                    .select('place_id,solo_ok_level,solo_allowed')
                    .in('place_id', ids);

                const profMap = new Map(
                    (profRows ?? []).map((r) => [r.place_id, r]),
                );

                const merged: PlaceSummary[] = (placeRows ?? []).map((p) => {
                    const prof = profMap.get(p.id);
                    return {
                        id: p.id,
                        name_ko: p.name_ko,
                        name_ja: p.name_ja,
                        category: p.category,
                        address: p.address,
                        lat: p.lat,
                        lng: p.lng,
                        solo_ok_level: prof?.solo_ok_level,
                        solo_allowed: prof?.solo_allowed,
                    };
                });

                replaceSavedWithPlaces(merged);
                setPlaces(merged);
            } catch {
                // 동기화 실패해도 로컬은 유지
            } finally {
                setStatus('ready');
            }
        };

        syncFromServer();
    }, []);

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>{t('saved.title')}</h1>
                {status === 'offline' && (
                    <span className={styles.badge}>{t('saved.offline')}</span>
                )}
                {status === 'syncing' && (
                    <span className={styles.badge}>{t('saved.syncing')}</span>
                )}
            </header>

            {places.length === 0 ? (
                <div className={styles.empty}>
                    <p>{t('saved.emptyTitle')}</p>
                    <p className={styles.emptyHint}>
                        {t('saved.emptyHint')}
                    </p>
                </div>
            ) : (
                <ul className={styles.list}>
                    {places.map((p) => (
                        <li key={p.id}>
                            <Link href={`/place/${p.id}`} className={styles.card}>
                                <div className={styles.cardMain}>
                                    <span className={styles.placeName}>{p.name_ko}</span>
                                    {p.name_ja && (
                                        <span className={styles.placeNameJa}>{p.name_ja}</span>
                                    )}
                                </div>
                                <div className={styles.cardMeta}>
                                    <span className={styles.address}>{p.address}</span>
                                    {p.solo_ok_level && (
                                        <span
                                            className={styles.level}
                                            data-level={p.solo_ok_level}
                                        >
                                            {CONFIDENCE_LABELS[p.solo_ok_level]?.[lang] ?? p.solo_ok_level}
                                        </span>
                                    )}
                                </div>
                            </Link>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
