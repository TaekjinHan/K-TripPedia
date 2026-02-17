/**
 * FilterModal -- 리스트 필터 풀스크린 모달
 * Day 3: 바텀시트 대신 모달(리스크 감소)
 */
'use client';

import { useState } from 'react';
import { CATEGORY_LABELS, CONFIDENCE_LABELS } from '@/lib/constants';
import styles from './FilterModal.module.css';

export interface FilterState {
    categories: string[];
    soloOkLevels: string[];
    counterSeatOnly: boolean;
}

export const INITIAL_FILTER: FilterState = {
    categories: [],
    soloOkLevels: [],
    counterSeatOnly: false,
};

interface FilterModalProps {
    isOpen: boolean;
    current: FilterState;
    onApply: (filter: FilterState) => void;
    onClose: () => void;
}

const CATEGORY_KEYS = Object.keys(CATEGORY_LABELS);
const LEVEL_KEYS = ['HIGH', 'MID', 'LOW'];

export default function FilterModal({
    isOpen,
    current,
    onApply,
    onClose,
}: FilterModalProps) {
    const [draft, setDraft] = useState<FilterState>(current);

    if (!isOpen) return null;

    const toggleCategory = (key: string) => {
        setDraft((prev) => ({
            ...prev,
            categories: prev.categories.includes(key)
                ? prev.categories.filter((c) => c !== key)
                : [...prev.categories, key],
        }));
    };

    const toggleLevel = (key: string) => {
        setDraft((prev) => ({
            ...prev,
            soloOkLevels: prev.soloOkLevels.includes(key)
                ? prev.soloOkLevels.filter((l) => l !== key)
                : [...prev.soloOkLevels, key],
        }));
    };

    const handleReset = () => {
        setDraft(INITIAL_FILTER);
    };

    const handleApply = () => {
        onApply(draft);
        onClose();
    };

    const activeCount =
        draft.categories.length +
        draft.soloOkLevels.length +
        (draft.counterSeatOnly ? 1 : 0);

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                {/* 헤더 */}
                <div className={styles.header}>
                    <button className={styles.closeBtn} onClick={onClose}>
                        <svg width={20} height={20} viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    </button>
                    <span className={styles.headerTitle}>フィルター</span>
                    <button className={styles.resetBtn} onClick={handleReset}>
                        リセット
                    </button>
                </div>

                {/* 카테고리 */}
                <div className={styles.section}>
                    <h3 className={styles.sectionTitle}>カテゴリー</h3>
                    <div className={styles.chipGroup}>
                        {CATEGORY_KEYS.map((key) => (
                            <button
                                key={key}
                                className={`${styles.chip} ${draft.categories.includes(key) ? styles.chipActive : ''
                                    }`}
                                onClick={() => toggleCategory(key)}
                            >
                                {CATEGORY_LABELS[key].ja}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Confidence 레벨 */}
                <div className={styles.section}>
                    <h3 className={styles.sectionTitle}>ひとりOK レベル</h3>
                    <div className={styles.chipGroup}>
                        {LEVEL_KEYS.map((key) => (
                            <button
                                key={key}
                                className={`${styles.chip} ${draft.soloOkLevels.includes(key) ? styles.chipActive : ''
                                    }`}
                                onClick={() => toggleLevel(key)}
                                data-level={key}
                            >
                                {CONFIDENCE_LABELS[key].ja}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 카운터석 필터 */}
                <div className={styles.section}>
                    <label className={styles.toggle}>
                        <span>カウンター席あり</span>
                        <input
                            type="checkbox"
                            checked={draft.counterSeatOnly}
                            onChange={(e) =>
                                setDraft((prev) => ({
                                    ...prev,
                                    counterSeatOnly: e.target.checked,
                                }))
                            }
                        />
                        <span className={styles.toggleSlider} />
                    </label>
                </div>

                {/* 적용 버튼 */}
                <div className={styles.footer}>
                    <button className={styles.applyBtn} onClick={handleApply}>
                        {activeCount > 0
                            ? `${activeCount}件のフィルターを適用`
                            : 'すべて表示'}
                    </button>
                </div>
            </div>
        </div>
    );
}
