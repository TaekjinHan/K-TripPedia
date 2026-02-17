/**
 * SaveButton -- Place Detail에 붙일 저장 토글 버튼
 *
 * 전략:
 * 1. 로컬 스냅샷 먼저 반영(오프라인/실패에도 UX 유지)
 * 2. 온라인 + Supabase 가능하면 서버 동기화(best-effort)
 */
'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { ensureAnonSession } from '@/lib/auth';
import { isSaved, toggleSaved } from '@/lib/savedSnapshot';
import type { PlaceSummary } from '@/lib/savedSnapshot';
import styles from './SaveButton.module.css';

export default function SaveButton({ place }: { place: PlaceSummary }) {
    const [saved, setSaved] = useState(false);
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        setSaved(isSaved(place.id));
    }, [place.id]);

    const onClick = async () => {
        setBusy(true);

        // 1) 로컬 스냅샷 먼저 반영
        const nextState = toggleSaved(place);
        const nextSaved = nextState.items.some((it) => it.place.id === place.id);
        setSaved(nextSaved);

        // 2) 온라인 + supabase -> 서버 동기화(best-effort)
        if (navigator.onLine) {
            try {
                const userId = await ensureAnonSession();
                if (userId) {
                    if (nextSaved) {
                        await supabase
                            .from('bookmarks')
                            .insert({ user_id: userId, place_id: place.id });
                    } else {
                        await supabase
                            .from('bookmarks')
                            .delete()
                            .eq('user_id', userId)
                            .eq('place_id', place.id);
                    }
                }
            } catch {
                // 서버 동기화 실패해도 로컬은 유지
            }
        }

        setBusy(false);
    };

    return (
        <button
            onClick={onClick}
            disabled={busy}
            className={`${styles.saveButton} ${saved ? styles.saved : ''}`}
            aria-label={saved ? '저장 해제' : '저장'}
        >
            <svg
                width={18}
                height={18}
                viewBox="0 0 24 24"
                fill={saved ? 'currentColor' : 'none'}
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            >
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
            </svg>
            <span>{saved ? '保存済み' : '保存'}</span>
            {busy && <span className={styles.spinner} />}
        </button>
    );
}
