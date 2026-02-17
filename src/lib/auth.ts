/**
 * 익명 인증 자동 로그인 유틸
 *
 * 앱 첫 실행 시 signInAnonymously()로 세션 생성 ->
 * bookmarks/observations 쓰기에 auth.uid() 사용 가능
 */

import { supabase } from './supabase';

/**
 * 세션이 없으면 익명 로그인 시도.
 * 이미 세션이 있으면 아무것도 하지 않음.
 * 실패해도 앱이 터지지 않도록 try-catch 처리.
 */
export async function ensureAnonSession(): Promise<string | null> {
    try {
        const { data: sessionData } = await supabase.auth.getSession();
        if (sessionData.session) {
            return sessionData.session.user.id;
        }

        const { data, error } = await supabase.auth.signInAnonymously();
        if (error) {
            console.warn('[auth] Anonymous sign-in failed:', error.message);
            return null;
        }

        return data.session?.user.id ?? null;
    } catch (e) {
        console.warn('[auth] ensureAnonSession error:', e);
        return null;
    }
}

/** 현재 로그인한 사용자 ID (없으면 null) */
export async function getCurrentUserId(): Promise<string | null> {
    try {
        const { data } = await supabase.auth.getUser();
        return data.user?.id ?? null;
    } catch {
        return null;
    }
}
