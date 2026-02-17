/**
 * 익명 인증 자동 로그인 유틸
 *
 * 앱 첫 실행 시 signInAnonymously()로 세션 생성 ->
 * bookmarks/observations 쓰기에 auth.uid() 사용 가능
 */

import { supabase } from './supabase';

export const HITORI_USER_ID_KEY = 'hitori_user_id';
const HITORI_MEMBER_SINCE_KEY = 'hitori_member_since';

function persistUserIdentity(userId: string): void {
    if (typeof window === 'undefined') return;
    try {
        window.localStorage.setItem(HITORI_USER_ID_KEY, userId);

        const existingSince = window.localStorage.getItem(HITORI_MEMBER_SINCE_KEY);
        if (!existingSince) {
            window.localStorage.setItem(
                HITORI_MEMBER_SINCE_KEY,
                new Date().toISOString().slice(0, 10),
            );
        }
    } catch {
        // ignore
    }
}

export function getStoredHitoriUserId(): string | null {
    if (typeof window === 'undefined') return null;
    try {
        return window.localStorage.getItem(HITORI_USER_ID_KEY);
    } catch {
        return null;
    }
}

export function getStoredMemberSince(): string | null {
    if (typeof window === 'undefined') return null;
    try {
        return window.localStorage.getItem(HITORI_MEMBER_SINCE_KEY);
    } catch {
        return null;
    }
}

/**
 * 세션이 없으면 익명 로그인 시도.
 * 이미 세션이 있으면 아무것도 하지 않음.
 * 실패해도 앱이 터지지 않도록 try-catch 처리.
 */
export async function ensureAnonSession(): Promise<string | null> {
    try {
        const { data: sessionData } = await supabase.auth.getSession();
        if (sessionData.session) {
            const userId = sessionData.session.user.id;
            persistUserIdentity(userId);
            return userId;
        }

        const { data, error } = await supabase.auth.signInAnonymously();
        if (error) {
            console.warn('[auth] Anonymous sign-in failed:', error.message);
            return null;
        }

        const userId = data.session?.user.id ?? null;
        if (userId) {
            persistUserIdentity(userId);
        }

        return userId;
    } catch (e) {
        console.warn('[auth] ensureAnonSession error:', e);
        return null;
    }
}

/** 현재 로그인한 사용자 ID (없으면 null) */
export async function getCurrentUserId(): Promise<string | null> {
    try {
        const { data } = await supabase.auth.getUser();
        const userId = data.user?.id ?? null;
        if (userId) {
            persistUserIdentity(userId);
        }
        return userId;
    } catch {
        return null;
    }
}
