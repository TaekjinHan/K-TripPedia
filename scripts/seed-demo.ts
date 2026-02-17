/**
 * scripts/seed-demo.ts
 *
 * 엑셀 없이 하드코딩된 데모 데이터로 places + solo_profile + rules + tips 삽입
 * 실행: npx tsx scripts/seed-demo.ts
 */
import 'dotenv/config';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const serviceRole = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

if (!supabaseUrl || !serviceRole) {
    console.error('Missing env: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, serviceRole, {
    auth: { persistSession: false },
});

/* ------------------------------------------------------------------ */
/* Demo Data                                                           */
/* ------------------------------------------------------------------ */

const PLACES = [
    {
        name_ko: '명동교자',
        name_ja: 'ミョンドンギョザ',
        category: 'noodle',
        address: '서울 중구 명동10길 29',
        lat: 37.5636,
        lng: 126.9854,
        phone: '02-776-5348',
        opening_hours: '11:00-21:00',
        solo_ok_level: 'HIGH',
        solo_allowed: 'YES',
        counter_seat: '?',
        best_time_note: '14:00~17:00 한가한 시간대 추천',
    },
    {
        name_ko: '을지면옥',
        name_ja: 'ウルジミョノク',
        category: 'noodle',
        address: '서울 중구 을지로19길 6',
        lat: 37.5671,
        lng: 126.9901,
        phone: '02-2266-0735',
        opening_hours: '11:00-20:00',
        solo_ok_level: 'HIGH',
        solo_allowed: 'YES',
        counter_seat: 'N',
        best_time_note: '오후 2시 이후 한가',
    },
    {
        name_ko: '왕비집',
        name_ja: 'ワンビジプ',
        category: 'bbq',
        address: '서울 종로구 종로12길 15',
        lat: 37.5707,
        lng: 126.9886,
        phone: '02-732-2460',
        opening_hours: '16:00-22:00',
        solo_ok_level: 'LOW',
        solo_allowed: 'CONDITIONAL',
        min_portions: 2,
        counter_seat: 'N',
        best_time_note: '2인분 주문 필수, 오픈 직후가 좋음',
    },
    {
        name_ko: '진옥화포차',
        name_ja: 'ジノクファポチャ',
        category: 'izakaya',
        address: '서울 마포구 토정로 37-5',
        lat: 37.5520,
        lng: 126.9217,
        phone: '02-715-3759',
        opening_hours: '17:00-01:00',
        solo_ok_level: 'MID',
        solo_allowed: 'CONDITIONAL',
        counter_seat: 'Y',
        best_time_note: '평일 17~19시 추천',
    },
    {
        name_ko: '호랑이떡볶이',
        name_ja: 'ホランイトッポッキ',
        category: 'other',
        address: '서울 종로구 종로3길 17',
        lat: 37.5702,
        lng: 126.9893,
        opening_hours: '10:00-21:00',
        solo_ok_level: 'HIGH',
        solo_allowed: 'YES',
        counter_seat: 'Y',
    },
    {
        name_ko: '부산집',
        name_ja: 'プサンジプ',
        category: 'stew',
        address: '서울 중구 다산로 149',
        lat: 37.5588,
        lng: 127.0055,
        phone: '02-2234-4558',
        opening_hours: '11:00-21:00',
        solo_ok_level: 'HIGH',
        solo_allowed: 'YES',
        counter_seat: '?',
        best_time_note: '점심 비추, 14시 이후 OK',
    },
    {
        name_ko: '통인시장 도시락카페',
        name_ja: '通仁市場弁当カフェ',
        category: 'korean_set',
        address: '서울 종로구 자하문로15길 18',
        lat: 37.5797,
        lng: 126.9693,
        opening_hours: '11:00-17:00',
        solo_ok_level: 'HIGH',
        solo_allowed: 'YES',
        counter_seat: 'Y',
        best_time_note: '엽전으로 반찬 선택, 1인 최적',
    },
    {
        name_ko: '채선당 명동점',
        name_ja: 'チェソンダン明洞店',
        category: 'stew',
        address: '서울 중구 명동길 12',
        lat: 37.5641,
        lng: 126.9824,
        phone: '02-318-2828',
        opening_hours: '11:00-22:00',
        solo_ok_level: 'MID',
        solo_allowed: 'YES',
        counter_seat: 'N',
    },
    {
        name_ko: '이루야 라멘',
        name_ja: 'イルヤラーメン',
        category: 'ramen',
        address: '서울 중구 충무로9길 17',
        lat: 37.5610,
        lng: 126.9926,
        opening_hours: '11:00-21:00',
        solo_ok_level: 'HIGH',
        solo_allowed: 'YES',
        counter_seat: 'Y',
        best_time_note: '카운터석 최적! 평일 15시경 추천',
    },
    {
        name_ko: '네네치킨 종로점',
        name_ja: 'ネネチキン鍾路店',
        category: 'chicken',
        address: '서울 종로구 종로 53',
        lat: 37.5709,
        lng: 126.9900,
        phone: '02-741-0000',
        opening_hours: '15:00-02:00',
        solo_ok_level: 'HIGH',
        solo_allowed: 'YES',
        counter_seat: '?',
    },
];

const RULES = [
    { place_name: '왕비집', rule_type: 'MIN_PORTION', note_short: '1인 1인분 불가, 최소 2인분', value_int: 2 },
    { place_name: '왕비집', rule_type: 'PEAK_TIME_RISK', note_short: '저녁 18~20시 혼잡' },
    { place_name: '진옥화포차', rule_type: 'COUNTER_SEAT_AVAILABLE', note_short: '바 카운터석에서 혼술 가능' },
    { place_name: '진옥화포차', rule_type: 'SOLO_DRINKING_OK', note_short: '혼술 가능, 소주+안주 세트 추천' },
    { place_name: '명동교자', rule_type: 'TOURIST_FRIENDLY', note_short: '관광객 많음, 일본어 메뉴 있음' },
    { place_name: '부산집', rule_type: 'PEAK_TIME_RISK', note_short: '점심 12~13시 웨이팅 30분+' },
    { place_name: '이루야 라멘', rule_type: 'COUNTER_SEAT_AVAILABLE', note_short: '전석 카운터, 1인 최적' },
    { place_name: '네네치킨 종로점', rule_type: 'LATE_NIGHT', note_short: '새벽 2시까지 영업' },
    { place_name: '호랑이떡볶이', rule_type: 'TAKEOUT_ALLOWED', note_short: '포장 가능' },
    { place_name: '통인시장 도시락카페', rule_type: 'TOURIST_FRIENDLY', note_short: '엽전 구매 후 반찬 선택' },
];

const TIPS = [
    { place_name: '왕비집', tip_type: 'ORDER_TWO_PORTIONS', tip_text_ko: '삼겹살 2인분 주문하면 1인도 OK', tip_text_ja: 'サムギョプサル2人前を注文すれば1人でもOK', priority: 90 },
    { place_name: '왕비집', tip_type: 'VISIT_OFFPEAK', tip_text_ko: '오픈 직후(16시) 방문하면 거의 빈 좌석', tip_text_ja: 'オープン直後(16時)に行くとほぼ空席', priority: 80 },
    { place_name: '진옥화포차', tip_type: 'COUNTER_SEAT_REQUEST', tip_text_ko: '바 자리 괜찮다고 말하면 혼자도 OK', tip_text_ja: 'バー席OKと言えば一人でもOK', priority: 85 },
    { place_name: '명동교자', tip_type: 'VISIT_OFFPEAK', tip_text_ko: '14시~17시 한가한 시간에 방문 추천', tip_text_ja: '14時~17時の空いている時間がおすすめ', priority: 70 },
    { place_name: '부산집', tip_type: 'VISIT_OFFPEAK', tip_text_ko: '14시 이후에 가면 웨이팅 없음', tip_text_ja: '14時以降に行けば待ち時間なし', priority: 75 },
    { place_name: '이루야 라멘', tip_type: 'COUNTER_SEAT_REQUEST', tip_text_ko: '전석 카운터라 혼자 가기 최고', tip_text_ja: '全席カウンターなので一人で行くのに最高', priority: 90 },
    { place_name: '통인시장 도시락카페', tip_type: 'ARRIVE_BEFORE_OPEN', tip_text_ko: '11시 오픈 직후 가면 반찬 선택지 풍부', tip_text_ja: '11時オープン直後に行くとおかずの選択肢が豊富', priority: 80 },
];

/* ------------------------------------------------------------------ */
/* Main                                                                */
/* ------------------------------------------------------------------ */

async function main() {
    console.log('[SEED] Upserting places...');

    const placesPayload = PLACES.map((p) => ({
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
        .upsert(placesPayload, { onConflict: 'name_ko,address' })
        .select('id,name_ko,address');

    if (placesErr) throw placesErr;
    if (!upsertedPlaces) throw new Error('Upsert returned no data');

    console.log(`[OK] Places: ${upsertedPlaces.length}`);

    // Build mapping
    const idByName = new Map<string, string>();
    for (const p of upsertedPlaces) idByName.set(p.name_ko, p.id);

    // solo_profile
    console.log('[SEED] Upserting solo_profile...');
    const profilePayload = PLACES.map((p) => {
        const place_id = idByName.get(p.name_ko);
        if (!place_id) throw new Error(`No place_id for ${p.name_ko}`);
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
        .upsert(profilePayload, { onConflict: 'place_id' });
    if (profileErr) throw profileErr;
    console.log(`[OK] Profiles: ${profilePayload.length}`);

    // Clean existing rules + tips
    const allIds = upsertedPlaces.map((p) => p.id);
    const { data: existingRules } = await supabase
        .from('solo_rules')
        .select('id')
        .in('place_id', allIds);

    if (existingRules && existingRules.length > 0) {
        await supabase.from('solo_rule_time_windows').delete().in('solo_rule_id', existingRules.map((r) => r.id));
    }
    await supabase.from('solo_rules').delete().in('place_id', allIds);
    await supabase.from('tips').delete().in('place_id', allIds);

    // Insert rules
    console.log('[SEED] Inserting rules...');
    for (const r of RULES) {
        const place_id = idByName.get(r.place_name);
        if (!place_id) { console.warn(`Skip rule: unknown place ${r.place_name}`); continue; }

        const { error } = await supabase.from('solo_rules').insert({
            place_id,
            rule_type: r.rule_type,
            note_short: r.note_short ?? null,
            value_int: r.value_int ?? null,
            value_text: null,
        });
        if (error) throw error;
    }
    console.log(`[OK] Rules: ${RULES.length}`);

    // Insert tips
    console.log('[SEED] Inserting tips...');
    const tipsPayload = TIPS.map((t) => {
        const place_id = idByName.get(t.place_name);
        if (!place_id) throw new Error(`No place_id for tip: ${t.place_name}`);
        return {
            place_id,
            tip_type: t.tip_type,
            tip_text_ko: t.tip_text_ko,
            tip_text_ja: t.tip_text_ja ?? null,
            tip_text_en: null,
            priority: t.priority ?? 50,
        };
    });

    const { error: tipsErr } = await supabase.from('tips').insert(tipsPayload);
    if (tipsErr) throw tipsErr;
    console.log(`[OK] Tips: ${tipsPayload.length}`);

    console.log('\n[DONE] Demo seed complete!');
    console.log(`  Places: ${upsertedPlaces.length}`);
    console.log(`  Profiles: ${profilePayload.length}`);
    console.log(`  Rules: ${RULES.length}`);
    console.log(`  Tips: ${tipsPayload.length}`);
}

main().catch((e) => {
    console.error('[FAIL]', e);
    process.exit(1);
});
