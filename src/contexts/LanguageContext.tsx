'use client';

import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react';
import {
    DEFAULT_APP_LANGUAGE,
    localeDictionary,
    type AppLanguage,
} from '@/locales';

const LANGUAGE_STORAGE_KEY = 'hitoriok:language:v1';

interface LanguageContextValue {
    lang: AppLanguage;
    setLang: (lang: AppLanguage) => void;
    toggleLang: () => void;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

function isAppLanguage(value: string): value is AppLanguage {
    return value in localeDictionary;
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
    const [lang, setLangState] = useState<AppLanguage>(DEFAULT_APP_LANGUAGE);

    useEffect(() => {
        if (typeof window === 'undefined') return;
        try {
            const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
            if (stored && isAppLanguage(stored)) {
                setLangState(stored);
            }
        } catch {
            // ignore
        }
    }, []);

    useEffect(() => {
        if (typeof document !== 'undefined') {
            document.documentElement.lang = lang;
        }
    }, [lang]);

    const setLang = useCallback((nextLang: AppLanguage) => {
        setLangState(nextLang);
        if (typeof window !== 'undefined') {
            try {
                window.localStorage.setItem(LANGUAGE_STORAGE_KEY, nextLang);
            } catch {
                // ignore
            }
        }
    }, []);

    const toggleLang = useCallback(() => {
        setLang(lang === 'ja' ? 'ko' : 'ja');
    }, [lang, setLang]);

    const value = useMemo(
        () => ({ lang, setLang, toggleLang }),
        [lang, setLang, toggleLang],
    );

    return (
        <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
    );
}

export function useLanguageContext() {
    const context = useContext(LanguageContext);
    if (!context) {
        return {
            lang: DEFAULT_APP_LANGUAGE,
            setLang: () => {
                // noop fallback
            },
            toggleLang: () => {
                // noop fallback
            },
        };
    }
    return context;
}
