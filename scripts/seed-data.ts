// scripts/seed-data.ts
// 엑셀 3시트(places, rules, tips) -> Supabase 업로드 + place_id 매핑 + idempotent
// 실행: npx tsx scripts/seed-data.ts seed_places.xlsx
// 필요 패키지: xlsx, dotenv, @supabase/supabase-js
import 'dotenv/config';
import fs from 'node:fs';
import path from 'node:path';
import * as XLSX from 'xlsx';
import { createClient } from '@supabase/supabase-js';

// ---------- Type Definitions ----------

type SoloOkLevel = 'HIGH' | 'MID' | 'LOW';
type SoloAllowed = 'YES' | 'NO' | 'CONDITIONAL';
type CounterSeat = 'Y' | 'N' | '?';

type PlaceRow = {
    name_ko: string;
    name_ja?: string;
    category: string;
    address: string;
    lat: number;
    lng: number;
    phone?: string;
    opening_hours?: string;
    solo_ok_level: SoloOkLevel;
    solo_allowed: SoloAllowed;
    min_portions?: number;
    counter_seat?: CounterSeat;
    best_time_note?: string;
};

type RuleRow = {
    place_name_ko: string;
    rule_type: string;
    note_short?: string;
    value_int?: number;
    value_text?: string;
    dow?: number;
    start_time?: string;
    end_time?: string;
    window_kind?: 'RECOMMEND' | 'AVOID' | 'ONLY';
};

type TipRow = {
    place_name_ko: string;
    tip_type: string;
    tip_text_ko: string;
    tip_text_ja?: string;
    tip_text_en?: string;
    priority?: number;
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

function toNumber(v: unknown, field: string): number {
    const n = typeof v === 'number' ? v : Number(String(v ?? '').trim());
    if (Number.isNaN(n)) throw new Error(`Invalid number for ${field}: "${v}"`);
    return n;
}

function placeKey(name_ko: string, address: string) {
    return `${name_ko}|||${address}`;
}

function readSheet<T = Record<string, unknown>>(
    workbook: XLSX.WorkBook,
    sheetName: string,
): T[] {
    const ws = workbook.Sheets[sheetName];
    if (!ws) throw new Error(`Missing sheet: "${sheetName}" (expected: places, rules, tips)`);
    return XLSX.utils.sheet_to_json(ws, { defval: '' }) as T[];
}

// ---------- Main ----------

async function main() {
    const fileArg = process.argv[2] || 'seed_places.xlsx';
    const filePath = path.resolve(process.cwd(), fileArg);

    if (!fs.existsSync(filePath)) {
        throw new Error(`Seed file not found: ${filePath}`);
    }

    const supabaseUrl =
        process.env.SUPABASE_URL ||
        process.env.NEXT_PUBLIC_SUPABASE_URL ||
        '';

    const serviceRole =
        process.env.SUPABASE_SERVICE_ROLE_KEY ||
        '';

    must(supabaseUrl, 'Missing env: SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL)');
    must(serviceRole, 'Missing env: SUPABASE_SERVICE_ROLE_KEY');

    const supabase = createClient(supabaseUrl, serviceRole, {
        auth: { persistSession: false },
    });

    console.log(`[OK] Reading: ${filePath}`);
    const workbook = XLSX.readFile(filePath);

    const rawPlaces = readSheet(workbook, 'places');
    const rawRules = readSheet(workbook, 'rules');
    const rawTips = readSheet(workbook, 'tips');

    // ---- parse places ----
    const places: PlaceRow[] = rawPlaces.map((r: Record<string, unknown>, i: number) => {
        const name_ko = must(normStr(r.name_ko), `[places row ${i + 2}] name_ko required`);
        const address = must(normStr(r.address), `[places row ${i + 2}] address required`);

        const solo_ok_level = must(
            normUpper(r.solo_ok_level) as SoloOkLevel,
            `[places row ${i + 2}] solo_ok_level required`,
        );
        const solo_allowed = must(
            normUpper(r.solo_allowed) as SoloAllowed,
            `[places row ${i + 2}] solo_allowed required`,
        );

        if (!['HIGH', 'MID', 'LOW'].includes(solo_ok_level)) {
            throw new Error(`[places row ${i + 2}] invalid solo_ok_level: ${solo_ok_level}`);
        }
        if (!['YES', 'NO', 'CONDITIONAL'].includes(solo_allowed)) {
            throw new Error(`[places row ${i + 2}] invalid solo_allowed: ${solo_allowed}`);
        }

        const counterSeatRaw = normUpper(r.counter_seat);
        const counter_seat: CounterSeat | undefined =
            counterSeatRaw === ''
                ? undefined
                : counterSeatRaw === 'Y' || counterSeatRaw === 'N' || counterSeatRaw === '?'
                    ? (counterSeatRaw as CounterSeat)
                    : undefined;

        if (counterSeatRaw && !counter_seat) {
            throw new Error(`[places row ${i + 2}] invalid counter_seat: ${counterSeatRaw} (use Y/N/?)`);
        }

        const lat = toNumber(r.lat, `[places row ${i + 2}] lat`);
        const lng = toNumber(r.lng, `[places row ${i + 2}] lng`);

        const minPortionsRaw = normStr(r.min_portions);
        const min_portions = minPortionsRaw
            ? toNumber(minPortionsRaw, `[places row ${i + 2}] min_portions`)
            : undefined;

        return {
            name_ko,
            name_ja: normStr(r.name_ja) || undefined,
            category: must(normStr(r.category), `[places row ${i + 2}] category required`),
            address,
            lat,
            lng,
            phone: normStr(r.phone) || undefined,
            opening_hours: normStr(r.opening_hours) || undefined,
            solo_ok_level,
            solo_allowed,
            min_portions,
            counter_seat,
            best_time_note: normStr(r.best_time_note) || undefined,
        };
    });

    // name_ko 중복 감지(rules/tips join 안정성)
    const nameCounts = new Map<string, number>();
    for (const p of places) nameCounts.set(p.name_ko, (nameCounts.get(p.name_ko) ?? 0) + 1);
    const dupNames = [...nameCounts.entries()].filter(([, c]) => c > 1).map(([n]) => n);
    if (dupNames.length) {
        throw new Error(
            `Duplicate name_ko in places (rules/tips join will be ambiguous). Fix these:\n- ${dupNames.join('\n- ')}`,
        );
    }

    // ---- upsert places ----
    console.log(`[UP] Upserting places: ${places.length}`);
    const placeUpsertPayload = places.map((p) => ({
        name_ko: p.name_ko,
        name_ja: p.name_ja ?? null,
        category: p.category,
        address: p.address,
        lat: p.lat,
        lng: p.lng,
        phone: p.phone ?? null,
        opening_hours: p.opening_hours ?? null,
    }));

    const { data: upsertedPlaces, error: placesErr } = await supabase
        .from('places')
        .upsert(placeUpsertPayload, { onConflict: 'name_ko,address' })
        .select('id,name_ko,address');

    if (placesErr) throw placesErr;
    if (!upsertedPlaces) throw new Error('Upsert places returned no data');

    // build mapping
    const placeIdByName = new Map<string, string>();
    const placeIdByKey = new Map<string, string>();

    for (const row of upsertedPlaces) {
        placeIdByName.set(row.name_ko, row.id);
        placeIdByKey.set(placeKey(row.name_ko, row.address), row.id);
    }

    // ---- upsert solo_profile ----
    console.log(`[UP] Upserting solo_profile: ${places.length}`);
    const profilesPayload = places.map((p) => {
        const place_id = must(
            placeIdByKey.get(placeKey(p.name_ko, p.address)),
            `Missing place_id for ${p.name_ko}`,
        );
        return {
            place_id,
            solo_ok_level: p.solo_ok_level,
            solo_allowed: p.solo_allowed,
            min_portions_required: p.min_portions ?? null,
            counter_seat: p.counter_seat ?? null,
            best_time_note: p.best_time_note ?? null,
            last_verified_at: new Date().toISOString(),
        };
    });

    const { error: profileErr } = await supabase
        .from('solo_profile')
        .upsert(profilesPayload, { onConflict: 'place_id' });

    if (profileErr) throw profileErr;

    // ---- delete + insert rules/tips (idempotent) ----
    const allPlaceIds = upsertedPlaces.map((p) => p.id);

    console.log(`[CLEAN] Cleaning rules/tips for seeded places`);

    // time_windows 먼저 삭제(FK 참조)
    const { data: existingRules } = await supabase
        .from('solo_rules')
        .select('id')
        .in('place_id', allPlaceIds);

    if (existingRules && existingRules.length > 0) {
        const ruleIds = existingRules.map((r) => r.id);
        await supabase.from('solo_rule_time_windows').delete().in('solo_rule_id', ruleIds);
    }

    await supabase.from('solo_rules').delete().in('place_id', allPlaceIds);
    await supabase.from('tips').delete().in('place_id', allPlaceIds);

    // ---- parse + insert rules ----
    const rules: RuleRow[] = rawRules
        .filter((r: Record<string, unknown>) => normStr(r.place_name_ko) !== '' && normStr(r.rule_type) !== '')
        .map((r: Record<string, unknown>, i: number) => ({
            place_name_ko: must(normStr(r.place_name_ko), `[rules row ${i + 2}] place_name_ko required`),
            rule_type: must(normUpper(r.rule_type), `[rules row ${i + 2}] rule_type required`),
            note_short: normStr(r.note_short) || undefined,
            value_int: normStr(r.value_int) ? toNumber(r.value_int, `[rules row ${i + 2}] value_int`) : undefined,
            value_text: normStr(r.value_text) || undefined,
            dow: normStr(r.dow) ? toNumber(r.dow, `[rules row ${i + 2}] dow`) : undefined,
            start_time: normStr(r.start_time) || undefined,
            end_time: normStr(r.end_time) || undefined,
            window_kind: (normUpper(r.window_kind) as RuleRow['window_kind']) || undefined,
        }));

    console.log(`[UP] Inserting rules: ${rules.length}`);
    for (const rr of rules) {
        const place_id = must(
            placeIdByName.get(rr.place_name_ko),
            `rules: unknown place_name_ko "${rr.place_name_ko}"`,
        );
        const { data: insertedRule, error: insErr } = await supabase
            .from('solo_rules')
            .insert({
                place_id,
                rule_type: rr.rule_type,
                note_short: rr.note_short ?? null,
                value_int: rr.value_int ?? null,
                value_text: rr.value_text ?? null,
            })
            .select('id')
            .single();

        if (insErr) throw insErr;

        const hasWindow = rr.window_kind && rr.start_time && rr.end_time;
        if (hasWindow) {
            const { error: winErr } = await supabase.from('solo_rule_time_windows').insert({
                solo_rule_id: insertedRule.id,
                dow: rr.dow ?? null,
                start_time: rr.start_time,
                end_time: rr.end_time,
                window_kind: rr.window_kind,
            });
            if (winErr) throw winErr;
        }
    }

    // ---- parse + insert tips ----
    const tips: TipRow[] = rawTips
        .filter(
            (r: Record<string, unknown>) =>
                normStr(r.place_name_ko) !== '' &&
                normStr(r.tip_type) !== '' &&
                normStr(r.tip_text_ko) !== '',
        )
        .map((r: Record<string, unknown>, i: number) => ({
            place_name_ko: must(normStr(r.place_name_ko), `[tips row ${i + 2}] place_name_ko required`),
            tip_type: must(normUpper(r.tip_type), `[tips row ${i + 2}] tip_type required`),
            tip_text_ko: must(normStr(r.tip_text_ko), `[tips row ${i + 2}] tip_text_ko required`),
            tip_text_ja: normStr(r.tip_text_ja) || undefined,
            tip_text_en: normStr(r.tip_text_en) || undefined,
            priority: normStr(r.priority)
                ? toNumber(r.priority, `[tips row ${i + 2}] priority`)
                : undefined,
        }));

    console.log(`[UP] Inserting tips: ${tips.length}`);
    if (tips.length) {
        const tipsPayload = tips.map((t) => {
            const place_id = must(
                placeIdByName.get(t.place_name_ko),
                `tips: unknown place_name_ko "${t.place_name_ko}"`,
            );
            return {
                place_id,
                tip_type: t.tip_type,
                tip_text_ko: t.tip_text_ko,
                tip_text_ja: t.tip_text_ja ?? null,
                tip_text_en: t.tip_text_en ?? null,
                priority: t.priority ?? 50,
            };
        });

        const { error: tipsErr } = await supabase.from('tips').insert(tipsPayload);
        if (tipsErr) throw tipsErr;
    }

    console.log('[OK] Seed done!');
    console.log(`- places: ${upsertedPlaces.length}`);
    console.log(`- solo_profile: ${profilesPayload.length}`);
    console.log(`- rules: ${rules.length}`);
    console.log(`- tips: ${tips.length}`);
}

main().catch((e) => {
    console.error('[FAIL] Seed failed:', e);
    process.exit(1);
});
