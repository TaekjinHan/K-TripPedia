import ja from './ja';
import ko from './ko';

export const localeDictionary = {
    ja,
    ko,
} as const;

export type AppLanguage = keyof typeof localeDictionary;
export type LocaleSchema = (typeof localeDictionary)[AppLanguage];

export const DEFAULT_APP_LANGUAGE: AppLanguage = 'ja';
