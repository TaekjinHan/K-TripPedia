'use client';

import { useMemo } from 'react';
import { localeDictionary } from '@/locales';
import { useLanguageContext } from '@/contexts/LanguageContext';

function resolvePath(target: unknown, path: string): unknown {
    return path.split('.').reduce<unknown>((acc, key) => {
        if (acc && typeof acc === 'object' && key in (acc as Record<string, unknown>)) {
            return (acc as Record<string, unknown>)[key];
        }
        return undefined;
    }, target);
}

export function useTranslation() {
    const { lang } = useLanguageContext();

    const dictionary = localeDictionary[lang];

    const t = useMemo(() => {
        return (key: string, params?: Record<string, string | number>): string => {
            const raw = resolvePath(dictionary, key);
            if (typeof raw !== 'string') return key;

            if (!params) return raw;

            return Object.entries(params).reduce((text, [paramKey, value]) => {
                return text.replaceAll(`{${paramKey}}`, String(value));
            }, raw);
        };
    }, [dictionary]);

    return t;
}
