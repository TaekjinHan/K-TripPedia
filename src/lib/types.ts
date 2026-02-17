/**
 * HitoriOk TypeScript 타입 정의
 * schema.sql v3 (Evidence 기반 + auth.users) 동기화
 */

// ---------- Enum Types ----------

export type Category =
  | 'bbq'
  | 'stew'
  | 'korean_set'
  | 'noodle'
  | 'cafe'
  | 'izakaya'
  | 'ramen'
  | 'chicken'
  | 'convenience'
  | 'other';

export type SoloOkLevel = 'HIGH' | 'MID' | 'LOW';
export type SoloAllowed = 'YES' | 'NO' | 'CONDITIONAL';
export type CounterSeat = 'Y' | 'N' | '?';
export type WindowKind = 'RECOMMEND' | 'AVOID' | 'ONLY';

export type SoloOutcome =
  | 'ACCEPTED'
  | 'REJECTED'
  | 'ACCEPTED_IF_2PORTIONS'
  | 'UNKNOWN';

export type SourceType = 'USER_VISIT' | 'COMMUNITY' | 'STAFF_REPLY' | 'PHONE_CHECK' | 'CURATED';
export type SeatType = 'COUNTER' | 'TABLE' | 'SINGLE_BOOTH' | 'UNKNOWN';
export type StaffReaction = 'FRIENDLY' | 'NEUTRAL' | 'UNFRIENDLY' | 'UNKNOWN';
export type MealPeriod = 'BREAKFAST' | 'LUNCH' | 'DINNER' | 'LATE';

export type RuleType =
  | 'MIN_PORTION'
  | 'PEAK_TIME_RISK'
  | 'COUNTER_SEAT_AVAILABLE'
  | 'ORDER_TWO_PORTIONS_WORKAROUND'
  | 'RESERVATION_NEEDED'
  | 'TAKEOUT_ALLOWED'
  | 'BREAKFAST_AVAILABLE'
  | 'SOLO_DRINKING_OK'
  | 'LATE_NIGHT'
  | 'TOURIST_FRIENDLY';

export type TipType =
  | 'ORDER_TWO_PORTIONS'
  | 'VISIT_OFFPEAK'
  | 'ASK_WITH_PASS'
  | 'COUNTER_SEAT_REQUEST'
  | 'ARRIVE_BEFORE_OPEN';

// ---------- DB Entity Types ----------

export interface Place {
  id: string;
  parent_place_id: string | null;
  name_ko: string;
  name_ja: string | null;
  name_en: string | null;
  category: Category;
  address: string;
  lat: number;
  lng: number;
  phone: string | null;
  opening_hours: string | null;
  created_at: string;
}

export interface SoloProfile {
  place_id: string;
  solo_ok_level: SoloOkLevel;
  solo_allowed: SoloAllowed;
  min_portions_required: number | null;
  counter_seat: CounterSeat | null;
  best_time_note: string | null;
  last_verified_at: string | null;
  updated_at: string;
}

export interface SoloRule {
  id: string;
  place_id: string;
  rule_type: RuleType;
  value_int: number | null;
  value_text: string | null;
  note_short: string | null;
  created_at: string;
}

export interface SoloRuleTimeWindow {
  id: string;
  solo_rule_id: string;
  dow: number | null;
  start_time: string | null;
  end_time: string | null;
  window_kind: WindowKind;
}

export interface Observation {
  id: string;
  place_id: string;
  user_id: string | null;
  source_type: SourceType;
  source_url: string | null;
  observed_at: string | null;
  recorded_at: string;
  solo_outcome: SoloOutcome;
  min_portions: number | null;
  seat_type: SeatType | null;
  staff_reaction: StaffReaction | null;
  meal_period: MealPeriod | null;
  memo_short: string | null;
}

export interface Tip {
  id: string;
  place_id: string;
  tip_type: TipType;
  tip_text_ko: string;
  tip_text_ja: string | null;
  tip_text_en: string | null;
  priority: number;
  created_at: string;
}

export interface Bookmark {
  id: string;
  user_id: string;
  place_id: string;
  created_at: string;
}

// ---------- v0.2 확장용 (빈 테이블) ----------

export type PointEventType = 'report' | 'confirm' | 'confirmed' | 'helpful' | 'spam';

export interface PointEvent {
  id: string;
  user_id: string;
  event_type: PointEventType;
  entity_type: string | null;
  entity_id: string | null;
  points: number;
  created_at: string;
}

export interface UserStatsDaily {
  user_id: string;
  stat_date: string;
  points: number;
  reports_count: number;
  confirmed_count: number;
}

// ---------- Join / View Types ----------

/** Place + SoloProfile 조인 (화면에서 자주 사용) */
export interface PlaceWithProfile extends Place {
  solo_profile: SoloProfile | null;
}

/** Place 상세 (규칙 + 팁 + 최근 관측 포함) */
export interface PlaceDetail extends PlaceWithProfile {
  rules: SoloRule[];
  tips: Tip[];
  observations: Observation[];
}

/** 포인트 산식 (v0.2 확장용) */
export const LEGACY_POINT_VALUES = {
  report: 10,
  report_conditional: 12,
  confirm: 4,
  confirmed: 6,
  helpful: 2,
  spam_penalty: -20,
} as const;
