/**
 * PlaceDetailClient -- 장소 상세 페이지 클라이언트 컴포넌트
 *
 * Supabase에서 places + solo_profile + solo_rules + tips를 가져와서
 * 상세 정보(ConfidenceBadge + RulePanel + TipCard + SaveButton) 표시
 */
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import ConfidenceBadge from '@/components/ConfidenceBadge';
import RulePanel from '@/components/RulePanel';
import TipCard from '@/components/TipCard';
import SaveButton from '@/components/SaveButton';
import { CATEGORY_LABELS } from '@/lib/constants';
import {
    formatObservedDate,
    getMealPeriodLabel,
    getSeatTypeLabel,
    getSoloAllowedLabel,
    getSoloOutcomeLabel,
    getStaffReactionLabel,
} from '@/lib/labels';
import { useTranslation } from '@/hooks/useTranslation';
import { useLanguageContext } from '@/contexts/LanguageContext';
import type {
    SoloOkLevel,
    SoloAllowed,
    SoloOutcome,
    SeatType,
    StaffReaction,
    MealPeriod,
} from '@/lib/types';
import styles from './PlaceDetail.module.css';

interface PlaceData {
    id: string;
    name_ko: string;
    name_ja: string | null;
    category: string;
    address: string;
    phone: string | null;
    opening_hours: string | null;
    lat: number;
    lng: number;
}

interface ProfileData {
    solo_ok_level: SoloOkLevel;
    solo_allowed: SoloAllowed;
    min_portions_required: number | null;
    counter_seat: string | null;
    best_time_note: string | null;
}

interface RuleData {
    id: string;
    rule_type: string;
    value_int: number | null;
    value_text: string | null;
    note_short: string | null;
}

interface TipData {
    id: string;
    tip_type: string;
    tip_text_ko: string;
    tip_text_ja: string | null;
    priority: number;
}

interface ObservationData {
    id: string;
    solo_outcome: SoloOutcome;
    seat_type: SeatType | null;
    staff_reaction: StaffReaction | null;
    meal_period: MealPeriod | null;
    memo_short: string | null;
    observed_at: string | null;
}

export default function PlaceDetailClient() {
    const t = useTranslation();
    const { lang } = useLanguageContext();
    const params = useParams();
    const router = useRouter();
    const placeId = params.id as string;

    const [place, setPlace] = useState<PlaceData | null>(null);
    const [profile, setProfile] = useState<ProfileData | null>(null);
    const [rules, setRules] = useState<RuleData[]>([]);
    const [tips, setTips] = useState<TipData[]>([]);
    const [observations, setObservations] = useState<ObservationData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!placeId) return;

        const fetchDetail = async () => {
            setLoading(true);

            // 병렬 조회
            const [placeRes, profileRes, rulesRes, tipsRes, observationsRes] = await Promise.all([
                supabase.from('places').select('*').eq('id', placeId).single(),
                supabase.from('solo_profile').select('*').eq('place_id', placeId).single(),
                supabase.from('solo_rules').select('*').eq('place_id', placeId).order('rule_type'),
                supabase.from('tips').select('*').eq('place_id', placeId).order('priority', { ascending: false }),
                supabase.from('observations').select('*').eq('place_id', placeId).order('recorded_at', { ascending: false }).limit(5),
            ]);

            if (placeRes.error || !placeRes.data) {
                console.error('[PlaceDetail] Place not found:', placeRes.error);
                setLoading(false);
                return;
            }

            setPlace(placeRes.data as PlaceData);
            setProfile(profileRes.data as ProfileData | null);
            setRules((rulesRes.data ?? []) as RuleData[]);
            setTips((tipsRes.data ?? []) as TipData[]);
            setObservations((observationsRes.data ?? []) as ObservationData[]);
            setLoading(false);
        };

        fetchDetail();
    }, [placeId]);

    if (loading) {
        return (
            <div className={styles.loading}>{t('common.loading')}</div>
        );
    }

    if (!place) {
        return (
            <div className={styles.notFound}>
                <p>{t('placeDetail.notFound')}</p>
                <button className={styles.backBtn} onClick={() => router.back()}>
                    {t('common.back')}
                </button>
            </div>
        );
    }

    const categoryLabel = CATEGORY_LABELS[place.category]?.[lang] ?? place.category;

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

            {/* 메인 헤더 */}
            <div className={styles.header}>
                <div className={styles.nameSection}>
                    <h1 className={styles.name}>{place.name_ko}</h1>
                    {place.name_ja && (
                        <p className={styles.nameJa}>{place.name_ja}</p>
                    )}
                </div>
                {profile && (
                    <ConfidenceBadge level={profile.solo_ok_level} size="md" />
                )}
            </div>

            {/* 기본 정보 */}
            <div className={styles.infoSection}>
                <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>{t('placeDetail.category')}</span>
                    <span>{categoryLabel}</span>
                </div>
                {profile && (
                    <div className={styles.infoRow}>
                        <span className={styles.infoLabel}>{t('placeDetail.soloOk')}</span>
                        <span className={styles.allowedValue} data-allowed={profile.solo_allowed}>
                            {getSoloAllowedLabel(profile.solo_allowed, lang)}
                        </span>
                    </div>
                )}
                {profile?.min_portions_required && profile.min_portions_required >= 2 && (
                    <div className={styles.infoRow}>
                        <span className={styles.infoLabel}>{t('placeDetail.minOrder')}</span>
                        <span>
                            {t('placeDetail.minOrderValue', {
                                count: profile.min_portions_required,
                            })}
                        </span>
                    </div>
                )}
                {profile?.counter_seat && (
                    <div className={styles.infoRow}>
                        <span className={styles.infoLabel}>{t('placeDetail.counterSeat')}</span>
                        <span>
                            {profile.counter_seat === 'Y'
                                ? t('placeDetail.counterSeatYes')
                                : profile.counter_seat === 'N'
                                    ? t('placeDetail.counterSeatNo')
                                    : t('placeDetail.counterSeatUnknown')}
                        </span>
                    </div>
                )}
                <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>{t('placeDetail.address')}</span>
                    <span className={styles.address}>{place.address}</span>
                </div>
                {place.phone && (
                    <div className={styles.infoRow}>
                        <span className={styles.infoLabel}>{t('placeDetail.phone')}</span>
                        <a href={`tel:${place.phone}`} className={styles.phone}>{place.phone}</a>
                    </div>
                )}
                {place.opening_hours && (
                    <div className={styles.infoRow}>
                        <span className={styles.infoLabel}>{t('placeDetail.openingHours')}</span>
                        <span>{place.opening_hours}</span>
                    </div>
                )}
                {profile?.best_time_note && (
                    <div className={styles.timeNote}>
                        {profile.best_time_note}
                    </div>
                )}
            </div>

            {/* 규칙 */}
            <div className={styles.section}>
                <RulePanel rules={rules} />
            </div>

            {/* 공략 팁 */}
            {tips.length > 0 && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>{t('placeDetail.tipsTitle')}</h2>
                    <div className={styles.tipList}>
                        {tips.map((tip) => (
                            <TipCard
                                key={tip.id}
                                tipType={tip.tip_type}
                                textKo={tip.tip_text_ko}
                                textJa={tip.tip_text_ja}
                                priority={tip.priority}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* 최근 리포트 */}
            {observations.length > 0 && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>{t('placeDetail.recentReports')}</h2>
                    <div className={styles.reportList}>
                        {observations.map((obs) => (
                            <div key={obs.id} className={styles.reportCard}>
                                <div className={styles.reportHeader}>
                                    <span className={styles.outcomeBadge} data-outcome={obs.solo_outcome}>
                                        {getSoloOutcomeLabel(obs.solo_outcome, lang)}
                                    </span>
                                    <span className={styles.reportDate}>{formatObservedDate(obs.observed_at, lang)}</span>
                                </div>
                                <div className={styles.reportTags}>
                                    {obs.seat_type && <span className={styles.reportTag}>{getSeatTypeLabel(obs.seat_type, lang)}</span>}
                                    {obs.staff_reaction && <span className={styles.reportTag}>{getStaffReactionLabel(obs.staff_reaction, lang)}</span>}
                                    {obs.meal_period && <span className={styles.reportTag}>{getMealPeriodLabel(obs.meal_period, lang)}</span>}
                                </div>
                                {obs.memo_short && <p className={styles.reportMemo}>{obs.memo_short}</p>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* 액션 바 (저장 + 리포트) */}
            <div className={styles.actionBar}>
                <SaveButton
                    place={{
                        id: place.id,
                        name_ko: place.name_ko,
                        name_ja: place.name_ja,
                        category: place.category,
                        address: place.address,
                        lat: place.lat,
                        lng: place.lng,
                        solo_ok_level: profile?.solo_ok_level,
                        solo_allowed: profile?.solo_allowed,
                    }}
                />
                <a href={`/report/${place.id}`} className={styles.reportLink}>
                    {t('placeDetail.reportExperience')}
                </a>
            </div>
        </div>
    );
}
