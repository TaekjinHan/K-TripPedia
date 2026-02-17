import { createClient } from '@supabase/supabase-js';

const supabaseUrl =
    process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL ?? '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? '';
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY ?? '';

if (!supabaseUrl || !supabaseAnonKey) {
    console.warn(
        '[supabaseServer] READ 전용 클라이언트 환경변수 미설정. 서버 측 Supabase 호출이 실패할 수 있습니다.'
    );
}

/**
 * 서버 READ 전용(anon key) 클라이언트
 * - 서버 컴포넌트 metadata 조회 등 public read 목적
 */
export function createServerAnonClient() {
    return createClient(
        supabaseUrl || 'https://placeholder.supabase.co',
        supabaseAnonKey || 'placeholder',
        {
            auth: { persistSession: false },
        },
    );
}

/**
 * 서버 privileged write 용(service role) 클라이언트
 * - RLS 우회가 필요한 서버 액션/백엔드 작업에서만 사용
 */
export function createServiceRoleClient() {
    if (!supabaseUrl || !supabaseServiceRoleKey) {
        throw new Error('Supabase service credentials are missing');
    }

    return createClient(supabaseUrl, supabaseServiceRoleKey, {
        auth: { persistSession: false },
    });
}

export const supabaseServer = createServerAnonClient();
