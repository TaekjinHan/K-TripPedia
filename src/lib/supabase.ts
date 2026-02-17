/**
 * Supabase 클라이언트 (브라우저 싱글톤)
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
        'Supabase 환경변수가 설정되지 않았습니다. .env.local 파일을 확인하세요.'
    );
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
