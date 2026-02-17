/**
 * HitoriOk 상수 정의
 * UI 라벨, 컬러, 카테고리 매핑 등
 */

/* ------------------------------------------------------------------ */
/* Confidence 컬러                                                     */
/* ------------------------------------------------------------------ */

export const CONFIDENCE_COLORS = {
    HIGH: '#22C55E',
    MID: '#EAB308',
    LOW: '#9CA3AF',
} as const;

export const CONFIDENCE_LABELS: Record<string, Record<string, string>> = {
    HIGH: { ja: 'ひとりOK', ko: '1인 가능', en: 'Solo OK' },
    MID: { ja: '条件付きOK', ko: '조건부 가능', en: 'Conditional' },
    LOW: { ja: '情報不足', ko: '정보 부족', en: 'Limited Info' },
};

/* ------------------------------------------------------------------ */
/* 카테고리 라벨                                                       */
/* ------------------------------------------------------------------ */

export const CATEGORY_LABELS: Record<string, Record<string, string>> = {
    bbq: { ja: '焼肉', ko: '고기/구이', en: 'BBQ' },
    stew: { ja: '鍋/チゲ', ko: '찌개/탕', en: 'Stew' },
    korean_set: { ja: '韓定食', ko: '한식 정식', en: 'Korean Set' },
    noodle: { ja: '麺', ko: '면류', en: 'Noodle' },
    cafe: { ja: 'カフェ', ko: '카페', en: 'Cafe' },
    izakaya: { ja: '居酒屋', ko: '술집/포차', en: 'Bar' },
    ramen: { ja: 'ラーメン', ko: '라멘/일식', en: 'Ramen' },
    chicken: { ja: 'チキン', ko: '치킨', en: 'Chicken' },
    convenience: { ja: 'コンビニ', ko: '편의점', en: 'Convenience' },
    other: { ja: 'その他', ko: '기타', en: 'Other' },
};

/* ------------------------------------------------------------------ */
/* 규칙 유형 라벨                                                      */
/* ------------------------------------------------------------------ */

export const RULE_LABELS: Record<string, Record<string, string>> = {
    MIN_PORTION: { ja: '最低注文', ko: '최소 주문', en: 'Min Order' },
    PEAK_TIME_RISK: { ja: 'ピーク時注意', ko: '피크타임 위험', en: 'Peak Risk' },
    COUNTER_SEAT_AVAILABLE: { ja: 'カウンター席', ko: '카운터석', en: 'Counter' },
    ORDER_TWO_PORTIONS_WORKAROUND: { ja: '2人前でOK', ko: '2인분 주문OK', en: '2 Portions OK' },
    RESERVATION_NEEDED: { ja: '予約必要', ko: '예약 필수', en: 'Reservation' },
    TAKEOUT_ALLOWED: { ja: 'テイクアウトOK', ko: '포장 가능', en: 'Takeout' },
    BREAKFAST_AVAILABLE: { ja: '朝食OK', ko: '아침 가능', en: 'Breakfast' },
    SOLO_DRINKING_OK: { ja: '一人飲みOK', ko: '혼술 가능', en: 'Solo Drink' },
    LATE_NIGHT: { ja: '深夜営業', ko: '심야 영업', en: 'Late Night' },
    TOURIST_FRIENDLY: { ja: '観光客歓迎', ko: '관광객 친화', en: 'Tourist OK' },
};

/* ------------------------------------------------------------------ */
/* 팁 유형 아이콘/라벨                                                  */
/* ------------------------------------------------------------------ */

export const TIP_LABELS: Record<string, Record<string, string>> = {
    ORDER_TWO_PORTIONS: { ja: '2人前作戦', ko: '2인분 전략', en: 'Order 2' },
    VISIT_OFFPEAK: { ja: 'オフピーク狙い', ko: '한가한 시간 공략', en: 'Off-peak' },
    ASK_WITH_PASS: { ja: 'パスカード活用', ko: '패스카드 활용', en: 'Use Pass' },
    COUNTER_SEAT_REQUEST: { ja: 'カウンター席指定', ko: '카운터석 요청', en: 'Counter Seat' },
    ARRIVE_BEFORE_OPEN: { ja: 'オープン前到着', ko: '오픈 전 도착', en: 'Early Arrival' },
};

/* ------------------------------------------------------------------ */
/* 패스 카드 문구                                                      */
/* ------------------------------------------------------------------ */

export const PASS_MAIN_TEXT = {
    ko: '혼자 왔는데요.\n1인 식사 가능할까요?',
    ja: '一人で来ました。\n一人で食事できますか?',
    en: "I'm here alone.\nIs it OK to eat alone?",
    zh: '我一个人来的。\n可以一个人用餐吗?',
};

export const PASS_PRONUNCIATION = 'Honja wassneuneyo.\nIrin siksa ganeunghalkkayo?';

export const PASS_OPTIONS = [
    { id: 'bar_seat', labelJa: 'バー席OK', labelKo: '바 자리라도 괜찮아요', labelEn: 'A bar seat is fine' },
    { id: 'waiting', labelJa: 'ウェイティングOK', labelKo: '대기해도 괜찮아요', labelEn: 'I can wait' },
    { id: 'takeout', labelJa: 'テイクアウトOK', labelKo: '포장도 가능해요', labelEn: 'Takeout works too' },
    { id: 'two_portions', labelJa: '2人前OK', labelKo: '2인분 시킬게요', labelEn: "I'll order for two" },
    { id: 'menu', labelJa: 'メニュー見せて', labelKo: '메뉴판 보여주세요', labelEn: 'May I see the menu?' },
];

export const PASS_THANKS = {
    ko: '감사합니다',
    ja: 'ありがとうございます',
    en: 'Thank you',
    pronunciation: 'Gamsahamnida',
};

/* ------------------------------------------------------------------ */
/* 리포트 선택지                                                       */
/* ------------------------------------------------------------------ */

export const SOLO_OUTCOME_OPTIONS = [
    { value: 'ACCEPTED', labelJa: 'OK', labelKo: '가능', emoji: '' },
    { value: 'REJECTED', labelJa: 'NG', labelKo: '거절', emoji: '' },
    { value: 'ACCEPTED_IF_2PORTIONS', labelJa: '条件付き', labelKo: '조건부', emoji: '' },
    { value: 'UNKNOWN', labelJa: '不明', labelKo: '모름', emoji: '' },
];

export const SEAT_TYPE_OPTIONS = [
    { value: 'COUNTER', labelJa: 'カウンター', labelKo: '바/카운터' },
    { value: 'TABLE', labelJa: 'テーブル', labelKo: '테이블' },
    { value: 'SINGLE_BOOTH', labelJa: '一人ブース', labelKo: '1인 부스' },
];

export const STAFF_REACTION_OPTIONS = [
    { value: 'FRIENDLY', labelJa: '親切', labelKo: '친절' },
    { value: 'NEUTRAL', labelJa: '普通', labelKo: '보통' },
    { value: 'UNFRIENDLY', labelJa: '不快', labelKo: '불편' },
];

export const MEAL_PERIOD_OPTIONS = [
    { value: 'BREAKFAST', labelJa: '朝食', labelKo: '아침' },
    { value: 'LUNCH', labelJa: 'ランチ', labelKo: '점심' },
    { value: 'DINNER', labelJa: 'ディナー', labelKo: '저녁' },
    { value: 'LATE', labelJa: '深夜', labelKo: '야식' },
];




/* ------------------------------------------------------------------ */
/* 앱 기본값                                                           */
/* ------------------------------------------------------------------ */

export const DEFAULT_CENTER = { lat: 37.5596, lng: 126.9851 }; // 명동
export const DEFAULT_ZOOM = 4; // 카카오맵 level (작을수록 확대, 4 ≈ 동네 수준)
export const DEFAULT_LANGUAGE: 'ja' | 'ko' | 'en' | 'zh' = 'ja';
