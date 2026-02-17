'use client';

import { useMemo, useState } from 'react';
import { useTranslation } from '@/hooks/useTranslation';
import { useLanguageContext } from '@/contexts/LanguageContext';
import {
    formatPointDisplay,
    getPointTier,
    getSoloPassLevel,
    normalizeTotalPoints,
} from '@/lib/points';
import styles from './Pass.module.css';

interface PassCardProps {
    guestId: string | null;
    memberSince: string | null;
    totalPoints: number;
}

function formatMemberSince(value: string | null, lang: 'ko' | 'ja'): string {
    if (!value) return '-';

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;

    return new Intl.DateTimeFormat(lang === 'ko' ? 'ko-KR' : 'ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).format(parsed);
}

function maskGuestId(guestId: string | null, fallback: string): string {
    if (!guestId) return fallback;
    const compact = guestId.replace(/-/g, '').toUpperCase();
    const left = compact.slice(0, 4);
    const right = compact.slice(-4);
    return `HK-${left}-${right}`;
}

export default function PassCard({ guestId, memberSince, totalPoints }: PassCardProps) {
    const t = useTranslation();
    const { lang } = useLanguageContext();
    const [flipped, setFlipped] = useState(false);

    const normalizedPoints = useMemo(
        () => normalizeTotalPoints(totalPoints),
        [totalPoints],
    );

    const tier = getPointTier(normalizedPoints);
    const passLevel = getSoloPassLevel(normalizedPoints);

    const qrPayload = useMemo(() => {
        if (!guestId) return null;

        const encodedUserId =
            typeof window !== 'undefined' && typeof window.btoa === 'function'
                ? window.btoa(guestId)
                : guestId;

        return JSON.stringify({
            type: 'HITORIOK_PASS',
            encodedUserId,
        });
    }, [guestId]);

    const qrDataUrl = useMemo(() => {
        if (!qrPayload) return null;
        return `https://api.qrserver.com/v1/create-qr-code/?size=220x220&margin=0&data=${encodeURIComponent(qrPayload)}`;
    }, [qrPayload]);

    return (
        <div className={styles.cardWrap}>
            <button
                type="button"
                className={styles.flipButton}
                onClick={() => setFlipped((prev) => !prev)}
                aria-label={t('pass.flipHint')}
            >
                {t('pass.flipHint')}
            </button>

            <div className={`${styles.cardScene} ${flipped ? styles.isFlipped : ''}`}>
                <article className={`${styles.cardFace} ${styles.cardFront}`}>
                    <header className={styles.cardHeader}>
                        <span className={styles.cardBrand}>HITORIOK</span>
                        <span className={styles.cardTier}>{tier}</span>
                    </header>

                    <div className={styles.cardLevel}>{passLevel}</div>

                    <div className={styles.cardMetaGrid}>
                        <div>
                            <span className={styles.metaLabel}>{t('pass.cardNumber')}</span>
                            <div className={styles.metaValue}>
                                {maskGuestId(guestId, t('pass.guestFallback'))}
                            </div>
                        </div>
                        <div>
                            <span className={styles.metaLabel}>{t('pass.memberSince')}</span>
                            <div className={styles.metaValue}>{formatMemberSince(memberSince, lang)}</div>
                        </div>
                    </div>

                    <footer className={styles.cardFooter}>
                        <span>{t('pass.points')}</span>
                        <strong>{formatPointDisplay(normalizedPoints)}</strong>
                    </footer>
                </article>

                <article className={`${styles.cardFace} ${styles.cardBack}`}>
                    <div className={styles.magneticStripe} />
                    <h3 className={styles.backTitle}>{t('pass.backTitle')}</h3>
                    <p className={styles.backDescription}>{t('pass.backDescription')}</p>
                    <div className={styles.qrPlaceholder}>
                        {qrDataUrl ? (
                            <img
                                src={qrDataUrl}
                                alt={t('pass.qrAlt')}
                                className={styles.qrImage}
                            />
                        ) : (
                            t('pass.qrPlaceholder')
                        )}
                    </div>
                </article>
            </div>
        </div>
    );
}
