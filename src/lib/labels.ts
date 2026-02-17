import type {
    MealPeriod,
    SeatType,
    SoloAllowed,
    SoloOutcome,
    StaffReaction,
} from '@/lib/types';
import type { AppLanguage } from '@/locales';

export function getSoloAllowedLabel(
    allowed: SoloAllowed,
    lang: AppLanguage = 'ja',
): string {
    switch (allowed) {
        case 'YES':
            return lang === 'ko' ? '혼밥 가능' : 'ひとりOK';
        case 'NO':
            return lang === 'ko' ? '불가' : 'NG (1人不可)';
        case 'CONDITIONAL':
            return lang === 'ko' ? '조건부 가능' : '条件付きOK';
        default:
            return allowed;
    }
}

export function getSoloOutcomeLabel(
    outcome: SoloOutcome,
    lang: AppLanguage = 'ja',
): string {
    switch (outcome) {
        case 'ACCEPTED':
            return lang === 'ko' ? '가능' : 'ひとりOK';
        case 'REJECTED':
            return lang === 'ko' ? '거절' : 'NG';
        case 'ACCEPTED_IF_2PORTIONS':
            return lang === 'ko' ? '2인분 조건' : '2人前~';
        case 'UNKNOWN':
            return lang === 'ko' ? '불명' : '不明';
        default:
            return lang === 'ko' ? '불명' : '不明';
    }
}

export function getSeatTypeLabel(
    seatType: SeatType,
    lang: AppLanguage = 'ja',
): string {
    switch (seatType) {
        case 'COUNTER':
            return lang === 'ko' ? '카운터' : 'カウンター';
        case 'TABLE':
            return lang === 'ko' ? '테이블' : 'テーブル';
        case 'SINGLE_BOOTH':
            return lang === 'ko' ? '1인 부스' : '一人ブース';
        case 'UNKNOWN':
            return lang === 'ko' ? '불명' : '不明';
        default:
            return lang === 'ko' ? '불명' : '不明';
    }
}

export function getStaffReactionLabel(
    reaction: StaffReaction,
    lang: AppLanguage = 'ja',
): string {
    switch (reaction) {
        case 'FRIENDLY':
            return lang === 'ko' ? '친절' : '親切';
        case 'NEUTRAL':
            return lang === 'ko' ? '보통' : '普通';
        case 'UNFRIENDLY':
            return lang === 'ko' ? '불친절' : '不快';
        case 'UNKNOWN':
            return lang === 'ko' ? '불명' : '不明';
        default:
            return lang === 'ko' ? '불명' : '不明';
    }
}

export function getMealPeriodLabel(
    period: MealPeriod,
    lang: AppLanguage = 'ja',
): string {
    switch (period) {
        case 'BREAKFAST':
            return lang === 'ko' ? '아침' : '朝食';
        case 'LUNCH':
            return lang === 'ko' ? '점심' : 'ランチ';
        case 'DINNER':
            return lang === 'ko' ? '저녁' : 'ディナー';
        case 'LATE':
            return lang === 'ko' ? '야식' : '深夜';
        default:
            return period;
    }
}

export function formatObservedDate(
    date: string | null,
    lang: AppLanguage = 'ja',
): string {
    if (!date) return '-';

    const parsed = new Date(date);
    if (Number.isNaN(parsed.getTime())) return date;

    return new Intl.DateTimeFormat(lang === 'ko' ? 'ko-KR' : 'ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).format(parsed);
}
