/// <reference types="vitest/globals" />

import {
    formatObservedDate,
    getMealPeriodLabel,
    getSeatTypeLabel,
    getSoloAllowedLabel,
    getSoloOutcomeLabel,
    getStaffReactionLabel,
} from './labels';

describe('labels utils', () => {
    it('solo allowed 라벨을 반환한다', () => {
        expect(getSoloAllowedLabel('YES')).toBe('ひとりOK');
        expect(getSoloAllowedLabel('NO')).toBe('NG (1人不可)');
        expect(getSoloAllowedLabel('CONDITIONAL')).toBe('条件付きOK');
    });

    it('관측 결과/태그 라벨을 반환한다', () => {
        expect(getSoloOutcomeLabel('ACCEPTED')).toBe('ひとりOK');
        expect(getSeatTypeLabel('COUNTER')).toBe('カウンター');
        expect(getStaffReactionLabel('FRIENDLY')).toBe('親切');
        expect(getMealPeriodLabel('DINNER')).toBe('ディナー');
    });

    it('관측 날짜를 ja-JP 형식으로 포맷한다', () => {
        expect(formatObservedDate('2026-02-17')).toBe('2026/02/17');
    });

    it('잘못된 날짜/빈 값은 안전하게 처리한다', () => {
        expect(formatObservedDate(null)).toBe('-');
        expect(formatObservedDate('not-a-date')).toBe('not-a-date');
    });
});
