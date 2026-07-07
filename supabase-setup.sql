-- ליגת הניחושים · מונדיאל 2026 — הקמת בסיס הנתונים המשותף
-- הרצה חד-פעמית: Supabase Dashboard → SQL Editor → הדביקו הכל → Run

create table if not exists participants (
  id text primary key,
  name text not null,
  picks jsonb not null default '{}'::jsonb,
  scores jsonb not null default '{}'::jsonb,
  submitted_at timestamptz not null default now()
);

create table if not exists results (
  id int primary key,
  results jsonb not null default '{}'::jsonb,
  adv jsonb not null default '{}'::jsonb,
  scores jsonb not null default '{}'::jsonb
);

insert into results (id) values (1) on conflict do nothing;

-- Open read/write for the public anon key. Fine for a friendly office game:
-- the admin screen is PIN-gated in the UI, and the stakes are a food truck.
alter table participants enable row level security;
alter table results enable row level security;

create policy "read participants"   on participants for select using (true);
create policy "insert participants" on participants for insert with check (true);
create policy "update participants" on participants for update using (true);
create policy "delete participants" on participants for delete using (true);

create policy "read results"   on results for select using (true);
create policy "insert results" on results for insert with check (true);
create policy "update results" on results for update using (true);
