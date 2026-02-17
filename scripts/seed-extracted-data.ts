// scripts/seed-extracted-data.ts
// Gemini 추출 데이터(112개) -> Supabase 업로드
// 실행: npx tsx scripts/seed-extracted-data.ts C:\Users\Taekjin Hahn\.antigravity\HitoriOk(ひとりOK)\YouTube_SingleCh_Parsing\Extracted_Places_Data_Geocoded.xlsx
import dotenv from 'dotenv';
import fs from 'node:fs';
import path from 'node:path';

// .env.local 또는 .env 로드
if (fs.existsSync('.env.local')) {
    dotenv.config({ path: '.env.local' });
} else {
    dotenv.config();
}
import * as XLSX from 'xlsx';
import { createClient } from '@supabase/supabase-js';

// ---------- Type Definitions ----------
type SoloOkLevel = 'HIGH' | 'MID' | 'LOW';
type SoloAllowed = 'YES' | 'NO' | 'CONDITIONAL';
type CounterSeat = 'Y' | 'N' | '?';

type ExtractedRow = {
    name_ko: string;
    name_ja?: string;
    category: string;
    address_road: string;
    lat: number;
    lng: number;
    phone?: string;
    opening_hours?: string;
    solo_ok_level: string;
    solo_allowed: string;
    min_portions?: number;
    counter_seat?: string;
    best_time_note?: string;
    video_url?: string;
};

// ---------- Helpers ----------
function must<T>(v: T | undefined | null, msg: string): T {
    if (v === undefined || v === null || (typeof v === 'string' && v.trim() === '')) {
        throw new Error(msg);
    }
    return v;
}

function normStr(v: unknown): string {
    return String(v ?? '').trim();
}

function normUpper(v: unknown): string {
    return normStr(v).toUpperCase();
}

function toNumber(v: unknown, field: string): number | null {
    if (v === undefined || v === null || v === '') return null;
    const n = typeof v === 'number' ? v : Number(String(v).trim());
    if (Number.isNaN(n)) return null;
    return n;
}

async function main() {
    const fileArg = process.argv[2];
    if (!fileArg) {
        console.error('❌ 파일 경로를 입력해주세요.');
        console.log('Usage: npx tsx scripts/seed-extracted-data.ts <path_to_excel>');
        process.exit(1);
    }

    const filePath = path.resolve(fileArg);
    if (!fs.existsSync(filePath)) {
        throw new Error(`파일을 찾을 수 없습니다: ${filePath}`);
    }

    const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || '';
    const serviceRole = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

    must(supabaseUrl, 'Missing env: SUPABASE_URL');
    must(serviceRole, 'Missing env: SUPABASE_SERVICE_ROLE_KEY');

    const supabase = createClient(supabaseUrl, serviceRole, {
        auth: { persistSession: false },
    });

    console.log(`[OK] Loading: ${filePath}`);
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const rawData = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { defval: '' }) as ExtractedRow[];

    console.log(`[OK] Total rows found: ${rawData.length}`);

    const placesToInsert = [];
    const skippedRows = [];

    for (const [i, r] of rawData.entries()) {
        const name_ko = normStr(r.name_ko);
        const address = normStr(r.address_road);
        const lat = toNumber(r.lat, 'lat');
        const lng = toNumber(r.lng, 'lng');

        if (!name_ko || !address || lat === null || lng === null) {
            skippedRows.push({ index: i + 2, name: name_ko, reason: 'Missing name/address/coords' });
            continue;
        }

        // Validate Enums
        let solo_ok_level = normUpper(r.solo_ok_level);
        if (!['HIGH', 'MID', 'LOW'].includes(solo_ok_level)) solo_ok_level = 'MID';

        let solo_allowed = normUpper(r.solo_allowed);
        if (!['YES', 'NO', 'CONDITIONAL'].includes(solo_allowed)) solo_allowed = 'YES';

        let counter_seat = normUpper(r.counter_seat);
        if (!['Y', 'N', '?'].includes(counter_seat)) counter_seat = '?';

        placesToInsert.push({
            name_ko,
            name_ja: normStr(r.name_ja) || null,
            category: normStr(r.category) || 'etc',
            address,
            lat,
            lng,
            phone: normStr(r.phone) || null,
            opening_hours: normStr(r.opening_hours) || null,
            solo_profile: {
                solo_ok_level,
                solo_allowed,
                min_portions_required: toNumber(r.min_portions, 'min_portions'),
                counter_seat,
                best_time_note: normStr(r.best_time_note) || null,
                last_verified_at: new Date().toISOString()
            }
        });
    }

    if (skippedRows.length > 0) {
        console.log(`⚠️ Skipped ${skippedRows.length} rows (Missing coordinates or basic info).`);
    }

    console.log(`🚀 Upserting ${placesToInsert.length} places...`);

    let successCount = 0;
    for (const p of placesToInsert) {
        // 1. Upsert Place
        const { data: placeData, error: placeErr } = await supabase
            .from('places')
            .upsert({
                name_ko: p.name_ko,
                name_ja: p.name_ja,
                category: p.category,
                address: p.address,
                lat: p.lat,
                lng: p.lng,
                phone: p.phone,
                opening_hours: p.opening_hours
            }, { onConflict: 'name_ko,address' })
            .select('id')
            .single();

        if (placeErr) {
            console.error(`   ❌ Failed upserting place: ${p.name_ko}`, placeErr.message);
            continue;
        }

        // 2. Upsert Profile
        const { error: profileErr } = await supabase
            .from('solo_profile')
            .upsert({
                place_id: placeData.id,
                ...p.solo_profile
            }, { onConflict: 'place_id' });

        if (profileErr) {
            console.error(`   ❌ Failed upserting profile for: ${p.name_ko}`, profileErr.message);
            continue;
        }

        successCount++;
        if (successCount % 20 === 0) console.log(`   ... Progress: ${successCount}/${placesToInsert.length}`);
    }

    console.log(`\n✨ Finished!`);
    console.log(`- Successfully seeded: ${successCount} places`);
    console.log(`- Check your map at http://localhost:3000/map`);
}

main().catch((e) => {
    console.error('❌ Error during seeding:', e);
    process.exit(1);
});
