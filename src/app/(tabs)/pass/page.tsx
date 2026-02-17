'use client';

import { useEffect, useState } from 'react';
import { ensureAnonSession, getStoredHitoriUserId, getStoredMemberSince } from '@/lib/auth';
import { supabase } from '@/lib/supabase';
import { useTranslation } from '@/hooks/useTranslation';
import { formatPointDisplay, getPointTier, normalizeTotalPoints } from '@/lib/points';
import PassCard from './PassCard';
import styles from './Pass.module.css';

export default function PassPage() {
    const t = useTranslation();
    const [guestId, setGuestId] = useState<string | null>(null);
    const [memberSince, setMemberSince] = useState<string | null>(null);
    const [totalPoints, setTotalPoints] = useState(0);

    useEffect(() => {
        const init = async () => {
            const localUserId = getStoredHitoriUserId();
            if (localUserId) setGuestId(localUserId);

            const localSince = getStoredMemberSince();
            if (localSince) setMemberSince(localSince);

            const sessionUserId = await ensureAnonSession();
            const resolvedUserId = sessionUserId || localUserId;
            if (!resolvedUserId) return;

            setGuestId(resolvedUserId);

            const { data: totalPointsRaw, error } = await supabase.rpc(
                'get_user_total_points',
                {
                    target_user_id: resolvedUserId,
                },
            );

            if (error) {
                console.warn('[PassPage] Failed to load total points:', error.message);
                return;
            }

            const nextTotal = Number(totalPointsRaw ?? 0);

            setTotalPoints(normalizeTotalPoints(nextTotal));
        };

        init();
    }, []);

    const tier = getPointTier(totalPoints);

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>{t('pass.title')}</h1>
                <p className={styles.subtitle}>{t('pass.subtitle')}</p>
            </header>

            <PassCard
                guestId={guestId}
                memberSince={memberSince}
                totalPoints={totalPoints}
            />

            <section className={styles.summaryBox}>
                <h2 className={styles.summaryTitle}>{t('my.pointsTitle')}</h2>
                <p className={styles.summaryValue}>{formatPointDisplay(totalPoints)}</p>
                <p className={styles.summaryTier}>{t('pass.tier')}: {tier}</p>
            </section>
        </div>
    );
}
