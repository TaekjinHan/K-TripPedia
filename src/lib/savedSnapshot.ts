/**
 * Saved 로컬 스냅샷 (오프라인 대응)
 *
 * 온라인: Supabase bookmarks + place summary를 localStorage에도 저장
 * 오프라인: localStorage 스냅샷으로 Saved 렌더
 *
 * SW는 Pass/정적 자원만 캐시하고, 데이터 오프라인은 이 모듈로 처리
 */

export type PlaceSummary = {
    id: string;
    name_ko: string;
    name_ja?: string | null;
    category: string;
    address: string;
    lat: number;
    lng: number;
    solo_ok_level?: 'HIGH' | 'MID' | 'LOW';
    solo_allowed?: 'YES' | 'NO' | 'CONDITIONAL';
};

type SavedItem = { place: PlaceSummary; savedAt: number };
type SavedState = { version: 1; items: SavedItem[]; updatedAt: number };

const STORAGE_KEY = 'hitoriok:saved:v1';

function isClient(): boolean {
    return typeof window !== 'undefined';
}

export function loadSavedState(): SavedState {
    if (!isClient()) return { version: 1, items: [], updatedAt: Date.now() };
    try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        if (!raw) return { version: 1, items: [], updatedAt: Date.now() };
        const parsed = JSON.parse(raw) as SavedState;
        if (parsed?.version !== 1 || !Array.isArray(parsed.items)) {
            return { version: 1, items: [], updatedAt: Date.now() };
        }
        return parsed;
    } catch {
        return { version: 1, items: [], updatedAt: Date.now() };
    }
}

export function saveSavedState(state: SavedState): void {
    if (!isClient()) return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function isSaved(placeId: string): boolean {
    const s = loadSavedState();
    return s.items.some((it) => it.place.id === placeId);
}

export function toggleSaved(place: PlaceSummary): SavedState {
    const s = loadSavedState();
    const exists = s.items.some((it) => it.place.id === place.id);
    const nextItems = exists
        ? s.items.filter((it) => it.place.id !== place.id)
        : [{ place, savedAt: Date.now() }, ...s.items];

    const next: SavedState = { version: 1, items: nextItems, updatedAt: Date.now() };
    saveSavedState(next);
    return next;
}

/** 서버에서 가져온 bookmarks로 로컬 스냅샷을 전체 교체 */
export function replaceSavedWithPlaces(places: PlaceSummary[]): SavedState {
    const next: SavedState = {
        version: 1,
        items: places.map((p) => ({ place: p, savedAt: Date.now() })),
        updatedAt: Date.now(),
    };
    saveSavedState(next);
    return next;
}

export function getSavedPlaces(): PlaceSummary[] {
    return loadSavedState().items.map((it) => it.place);
}
