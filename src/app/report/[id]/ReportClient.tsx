/**
 * ReportClient -- 체험 리포트 제출 클라이언트 컴포넌트
 *
 * /report/[id] 에서 렌더.
 * observations 테이블에 INSERT, optimistic UI 제공.
 */
'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { ensureAnonSession } from '@/lib/auth';
import { submitReportAction } from '@/app/actions/submitReport';
import {
    SOLO_OUTCOME_OPTIONS,
    SEAT_TYPE_OPTIONS,
    STAFF_REACTION_OPTIONS,
    MEAL_PERIOD_OPTIONS,
} from '@/lib/constants';
import { useTranslation } from '@/hooks/useTranslation';
import { useLanguageContext } from '@/contexts/LanguageContext';
import styles from './Report.module.css';

type SubmitStatus = 'idle' | 'submitting' | 'success' | 'error';

export default function ReportClient() {
    const t = useTranslation();
    const { lang } = useLanguageContext();
    const params = useParams();
    const router = useRouter();
    const placeId = params.id as string;

    const [placeName, setPlaceName] = useState('');
    const [soloOutcome, setSoloOutcome] = useState('');
    const [seatType, setSeatType] = useState('');
    const [staffReaction, setStaffReaction] = useState('');
    const [mealPeriod, setMealPeriod] = useState('');
    const [memo, setMemo] = useState('');
    const [pointEarned, setPointEarned] = useState<number | null>(null);
    const [status, setStatus] = useState<SubmitStatus>('idle');
    const [errorKey, setErrorKey] = useState('report.error');

    /** 장소 이름 가져오기 */
    useEffect(() => {
        if (!placeId) return;
        supabase
            .from('places')
            .select('name_ko')
            .eq('id', placeId)
            .single()
            .then(({ data }) => {
                if (data) setPlaceName(data.name_ko);
            });
    }, [placeId]);

    const canSubmit = soloOutcome !== '' && status !== 'submitting';

    const handleSubmit = async () => {
        if (!canSubmit) return;
        setStatus('submitting');
        setPointEarned(null);
        setErrorKey('report.error');

        try {
            const userId = await ensureAnonSession();
            if (!userId) {
                throw new Error('Missing user session');
            }

            const result = await submitReportAction({
                userId,
                placeId,
                soloOutcome,
                seatType: seatType || null,
                staffReaction: staffReaction || null,
                mealPeriod: mealPeriod || null,
                memo: memo.trim() || null,
            });

            if (!result.ok) {
                if (result.errorCode === 'ALREADY_SUBMITTED_TODAY') {
                    setErrorKey('report.errorDuplicateToday');
                }

                setStatus('error');
                return;
            }

            setPointEarned(result.pointsGranted);

            setStatus('success');
            setTimeout(() => {
                router.push(`/place/${placeId}`);
                router.refresh();
            }, 1500);
        } catch (e) {
            console.error('[ReportClient] Submit error:', e);
            setErrorKey('report.error');
            setStatus('error');
        }
    };

    return (
        <div className={styles.container}>
            {/* 상단 네비 */}
            <div className={styles.nav}>
                <button className={styles.navBackBtn} onClick={() => router.back()}>
                    <svg width={20} height={20} viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <polyline points="15 18 9 12 15 6" />
                    </svg>
                    <span>{t('common.back')}</span>
                </button>
            </div>

            <div className={styles.header}>
                <h1 className={styles.title}>{t('report.title')}</h1>
                {placeName && <p className={styles.placeName}>{placeName}</p>}
            </div>

            {/* 결과(필수) */}
            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>
                    {t('report.result')} <span className={styles.required}>*{t('report.required')}</span>
                </h3>
                <div className={styles.optionGroup}>
                    {SOLO_OUTCOME_OPTIONS.map((opt) => (
                        <button
                            key={opt.value}
                            className={`${styles.optionBtn} ${soloOutcome === opt.value ? styles.optionActive : ''}`}
                            onClick={() => setSoloOutcome(opt.value)}
                            data-outcome={opt.value}
                        >
                            {lang === 'ko' ? opt.labelKo : opt.labelJa}
                        </button>
                    ))}
                </div>
            </div>

            {/* 좌석 타입 */}
            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>{t('report.seatType')}</h3>
                <div className={styles.optionGroup}>
                    {SEAT_TYPE_OPTIONS.map((opt) => (
                        <button
                            key={opt.value}
                            className={`${styles.optionBtn} ${seatType === opt.value ? styles.optionActive : ''}`}
                            onClick={() => setSeatType(seatType === opt.value ? '' : opt.value)}
                        >
                            {lang === 'ko' ? opt.labelKo : opt.labelJa}
                        </button>
                    ))}
                </div>
            </div>

            {/* 직원 반응 */}
            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>{t('report.staffReaction')}</h3>
                <div className={styles.optionGroup}>
                    {STAFF_REACTION_OPTIONS.map((opt) => (
                        <button
                            key={opt.value}
                            className={`${styles.optionBtn} ${staffReaction === opt.value ? styles.optionActive : ''}`}
                            onClick={() => setStaffReaction(staffReaction === opt.value ? '' : opt.value)}
                        >
                            {lang === 'ko' ? opt.labelKo : opt.labelJa}
                        </button>
                    ))}
                </div>
            </div>

            {/* 식사 시간대 */}
            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>{t('report.mealPeriod')}</h3>
                <div className={styles.optionGroup}>
                    {MEAL_PERIOD_OPTIONS.map((opt) => (
                        <button
                            key={opt.value}
                            className={`${styles.optionBtn} ${mealPeriod === opt.value ? styles.optionActive : ''}`}
                            onClick={() => setMealPeriod(mealPeriod === opt.value ? '' : opt.value)}
                        >
                            {lang === 'ko' ? opt.labelKo : opt.labelJa}
                        </button>
                    ))}
                </div>
            </div>

            {/* 메모 */}
            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>{t('report.memo')}</h3>
                <textarea
                    className={styles.textarea}
                    placeholder={t('report.memoPlaceholder')}
                    value={memo}
                    onChange={(e) => setMemo(e.target.value)}
                    rows={3}
                    maxLength={300}
                />
                <div className={styles.charCount}>{memo.length}/300</div>
            </div>

            {/* 제출 버튼 */}
            <div className={styles.footer}>
                {status === 'success' ? (
                    <div className={styles.successMsg}>
                        {t('report.success')}
                        {pointEarned !== null && (
                            <div className={styles.pointEarned}>
                                {t('report.pointEarned', { points: pointEarned })}
                            </div>
                        )}
                    </div>
                ) : status === 'error' ? (
                    <div className={styles.errorMsg}>
                        {t(errorKey)}
                        <button className={styles.retryBtn} onClick={() => setStatus('idle')}>
                            {t('common.retry')}
                        </button>
                    </div>
                ) : (
                    <button
                        className={styles.submitBtn}
                        disabled={!canSubmit}
                        onClick={handleSubmit}
                    >
                        {status === 'submitting' ? t('report.submitting') : t('report.submit')}
                    </button>
                )}
            </div>
        </div>
    );
}
