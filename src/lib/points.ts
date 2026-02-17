export const POINT_VALUES = {
    report: 10,
    reportConditional: 12,
    confirm: 4,
    confirmed: 6,
    helpful: 2,
    spamPenalty: -20,
} as const;

export type PointTier = 'Bronze' | 'Silver' | 'Gold' | 'Platinum';

export function getPointTier(points: number): PointTier {
    if (points >= 3000) return 'Platinum';
    if (points >= 1200) return 'Gold';
    if (points >= 400) return 'Silver';
    return 'Bronze';
}

export function getSoloPassLevel(points: number): string {
    const tier = getPointTier(points);
    switch (tier) {
        case 'Platinum':
            return 'LEGEND SOLO EATER';
        case 'Gold':
            return 'PRO SOLO EATER';
        case 'Silver':
            return 'SOLO EXPLORER';
        case 'Bronze':
        default:
            return 'SOLO STARTER';
    }
}

export function formatPointNumber(points: number): string {
    return new Intl.NumberFormat('en-US').format(Math.max(0, points));
}

export function normalizeTotalPoints(value: number | null | undefined): number {
    if (typeof value !== 'number' || Number.isNaN(value)) return 0;
    return Math.max(0, Math.floor(value));
}

export function formatPointDisplay(points: number): string {
    return `${formatPointNumber(points)} P`;
}
