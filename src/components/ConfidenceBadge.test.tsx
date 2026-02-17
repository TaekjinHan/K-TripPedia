/// <reference types="vitest/globals" />

import { render, screen } from '@testing-library/react';
import ConfidenceBadge from './ConfidenceBadge';

describe('ConfidenceBadge', () => {
    it('기본(ja) 라벨을 렌더한다', () => {
        render(<ConfidenceBadge level="HIGH" />);

        const badge = screen.getByText('ひとりOK');
        expect(badge).toBeTruthy();
        expect(badge.getAttribute('data-level')).toBe('HIGH');
    });

    it('lang prop에 따라 라벨을 바꾼다', () => {
        render(<ConfidenceBadge level="MID" lang="ko" />);

        expect(screen.getByText('조건부 가능')).toBeTruthy();
    });
});
