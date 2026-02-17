-- =============================================================================
-- HitoriOk MVP Schema (Evidence 기반) + RLS + places 유니크키(name_ko,address)
-- 사용자 피드백 반영 v4 (Policy Name Conflict Fix & v0.2 Extension)
-- =============================================================================

create extension if not exists pgcrypto;

-- ========== helpers ==========
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- ========== 1. places ==========
create table if not exists public.places (
  id uuid primary key default gen_random_uuid(),
  parent_place_id uuid references public.places(id) on delete set null,

  name_ko text not null,
  name_ja text,
  name_en text,

  category text not null,
  address text not null,

  lat double precision not null,
  lng double precision not null,

  phone text,
  opening_hours text,

  created_at timestamptz not null default now(),

  -- seed 재실행/업서트 안정화용 유니크(오타/중복 방지)
  constraint places_name_ko_address_unique unique (name_ko, address)
);

create index if not exists places_category_idx on public.places(category);

-- ========== 2. solo_profile ==========
create table if not exists public.solo_profile (
  place_id uuid primary key references public.places(id) on delete cascade,

  solo_ok_level text not null check (solo_ok_level in ('HIGH','MID','LOW')),
  solo_allowed text not null check (solo_allowed in ('YES','NO','CONDITIONAL')),

  min_portions_required int,
  counter_seat text check (counter_seat in ('Y','N','?')),
  best_time_note text,
  last_verified_at timestamptz,

  updated_at timestamptz not null default now()
);

drop trigger if exists trg_solo_profile_updated_at on public.solo_profile;
create trigger trg_solo_profile_updated_at
before update on public.solo_profile
for each row execute procedure public.set_updated_at();

-- ========== 3. solo_rules ==========
create table if not exists public.solo_rules (
  id uuid primary key default gen_random_uuid(),
  place_id uuid not null references public.places(id) on delete cascade,

  rule_type text not null,
  value_int int,
  value_text text,
  note_short text,

  created_at timestamptz not null default now()
);

create index if not exists solo_rules_place_idx on public.solo_rules(place_id);
create index if not exists solo_rules_type_idx on public.solo_rules(rule_type);

-- ========== 4. solo_rule_time_windows ==========
create table if not exists public.solo_rule_time_windows (
  id uuid primary key default gen_random_uuid(),
  solo_rule_id uuid not null references public.solo_rules(id) on delete cascade,

  dow smallint, -- 0=Sun..6=Sat, null=everyday
  start_time time,
  end_time time,
  window_kind text not null check (window_kind in ('RECOMMEND','AVOID','ONLY'))
);

create index if not exists solo_rule_time_windows_rule_idx
on public.solo_rule_time_windows(solo_rule_id);

-- ========== 5. tips ==========
create table if not exists public.tips (
  id uuid primary key default gen_random_uuid(),
  place_id uuid not null references public.places(id) on delete cascade,

  tip_type text not null,
  tip_text_ko text not null,
  tip_text_ja text,
  tip_text_en text,

  priority int not null default 50,
  created_at timestamptz not null default now()
);

create index if not exists tips_place_idx on public.tips(place_id);

-- ========== 6. observations ==========
create table if not exists public.observations (
  id uuid primary key default gen_random_uuid(),
  place_id uuid not null references public.places(id) on delete cascade,

  user_id uuid references auth.users(id) on delete set null,

  source_type text not null default 'USER_VISIT',
  source_url text,

  observed_at date,
  recorded_at timestamptz not null default now(),

  solo_outcome text not null check (solo_outcome in ('ACCEPTED','REJECTED','ACCEPTED_IF_2PORTIONS','UNKNOWN')),
  min_portions int,
  seat_type text,
  staff_reaction text,
  meal_period text,

  memo_short text
);

create index if not exists observations_place_idx on public.observations(place_id);

-- ========== 7. bookmarks ==========
create table if not exists public.bookmarks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  place_id uuid not null references public.places(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (user_id, place_id)
);

create index if not exists bookmarks_user_idx on public.bookmarks(user_id);

-- ========== 8. point_events (v0.2 확장용) ==========
create table if not exists public.point_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  event_type text not null,         -- report, confirm, confirmed, helpful, spam
  entity_type text,                 -- observation, tip, etc.
  entity_id uuid,
  points int not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists point_events_user_idx on public.point_events(user_id);

-- ========== 9. user_stats_daily (v0.2 확장용) ==========
create table if not exists public.user_stats_daily (
  user_id uuid not null references auth.users(id) on delete cascade,
  stat_date date not null default current_date,
  points int not null default 0,
  reports_count int not null default 0,
  confirmed_count int not null default 0,
  primary key (user_id, stat_date)
);

-- ========== RLS ==========
alter table public.places enable row level security;
alter table public.solo_profile enable row level security;
alter table public.solo_rules enable row level security;
alter table public.solo_rule_time_windows enable row level security;
alter table public.tips enable row level security;
alter table public.observations enable row level security;
alter table public.bookmarks enable row level security;
alter table public.point_events enable row level security;
alter table public.user_stats_daily enable row level security;

-- Public read (anon OK)
drop policy if exists "public read places" on public.places;
create policy "public read places" on public.places
for select using (true);

drop policy if exists "public read solo_profile" on public.solo_profile;
create policy "public read solo_profile" on public.solo_profile
for select using (true);

drop policy if exists "public read solo_rules" on public.solo_rules;
create policy "public read solo_rules" on public.solo_rules
for select using (true);

drop policy if exists "public read solo_rule_time_windows" on public.solo_rule_time_windows;
create policy "public read solo_rule_time_windows" on public.solo_rule_time_windows
for select using (true);

drop policy if exists "public read tips" on public.tips;
create policy "public read tips" on public.tips
for select using (true);

-- observations: 읽기 public
drop policy if exists "public read observations" on public.observations;
create policy "public read observations" on public.observations
for select using (true);

-- 리포트 제출 허용 (익명 사용자 포함)
-- 기존에 존재할 수 있는 이름들 모두 삭제하여 충돌 방지
drop policy if exists "auth insert observations" on public.observations;
drop policy if exists "public insert observations" on public.observations;

create policy "public insert observations" on public.observations
for insert to public
with check (true);

-- bookmarks: authenticated 본인 것만
drop policy if exists "read own bookmarks" on public.bookmarks;
create policy "read own bookmarks" on public.bookmarks
for select to authenticated
using (auth.uid() = user_id);

drop policy if exists "insert own bookmarks" on public.bookmarks;
create policy "insert own bookmarks" on public.bookmarks
for insert to authenticated
with check (auth.uid() = user_id);

drop policy if exists "delete own bookmarks" on public.bookmarks;
create policy "delete own bookmarks" on public.bookmarks
for delete to authenticated
using (auth.uid() = user_id);

-- point_events / user_stats_daily: authenticated 본인만
drop policy if exists "read own point_events" on public.point_events;
create policy "read own point_events" on public.point_events
for select to authenticated using (auth.uid() = user_id);

drop policy if exists "read own user_stats_daily" on public.user_stats_daily;
create policy "read own user_stats_daily" on public.user_stats_daily
for select to authenticated using (auth.uid() = user_id);

-- ========== v0.2 Extensions (Unique Index & RPC) ==========

-- 1. 중복 리포트 방지 인덱스
create unique index if not exists observations_user_place_observed_unique
on public.observations(user_id, place_id, observed_at)
where source_type = 'USER_VISIT';

-- 2. 포인트 집계 함수
create or replace function public.get_user_total_points(target_user_id uuid)
returns int language sql stable security invoker as $$
  select coalesce(sum(pe.points), 0)::int
  from public.point_events pe where pe.user_id = target_user_id;
$$;

grant execute on function public.get_user_total_points(uuid)
to anon, authenticated, service_role;
