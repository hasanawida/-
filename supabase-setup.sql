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

drop policy if exists "read participants"   on participants;
drop policy if exists "insert participants" on participants;
drop policy if exists "update participants" on participants;
drop policy if exists "delete participants" on participants;
drop policy if exists "read results"   on results;
drop policy if exists "insert results" on results;
drop policy if exists "update results" on results;

create policy "read participants"   on participants for select using (true);
create policy "insert participants" on participants for insert with check (true);
create policy "update participants" on participants for update using (true);
create policy "delete participants" on participants for delete using (true);

create policy "read results"   on results for select using (true);
create policy "insert results" on results for insert with check (true);
create policy "update results" on results for update using (true);

-- Server-side pick locking: once a match's kickoff time passes, its pick and
-- exact score can no longer be added or changed — not even by crafted REST
-- calls. Lock times mirror js/data.js (keep the two in sync if dates change).
create or replace function public.enforce_pick_locks() returns trigger
language plpgsql as $$
declare
  locks constant jsonb := '{
    "r16a": "2026-07-07T00:00:00+03:00",
    "r16b": "2026-07-07T00:00:00+03:00",
    "qf1":  "2026-07-09T23:00:00+03:00",
    "qf2":  "2026-07-10T22:00:00+03:00",
    "qf3":  "2026-07-12T00:00:00+03:00",
    "qf4":  "2026-07-12T04:00:00+03:00",
    "sf1":  "2026-07-14T22:00:00+03:00",
    "sf2":  "2026-07-15T22:00:00+03:00",
    "fin":  "2026-07-19T22:00:00+03:00"
  }';
  k text;
begin
  new.picks  := coalesce(new.picks,  '{}'::jsonb);
  new.scores := coalesce(new.scores, '{}'::jsonb);
  for k in select jsonb_object_keys(locks) loop
    if (locks->>k)::timestamptz <= now() then
      if tg_op = 'INSERT' then
        new.picks  := new.picks - k;
        new.scores := new.scores - k;
      else
        if coalesce(old.picks, '{}'::jsonb) ? k then
          new.picks := jsonb_set(new.picks, array[k], old.picks->k);
        else
          new.picks := new.picks - k;
        end if;
        if coalesce(old.scores, '{}'::jsonb) ? k then
          new.scores := jsonb_set(new.scores, array[k], old.scores->k);
        else
          new.scores := new.scores - k;
        end if;
      end if;
    end if;
  end loop;
  return new;
end $$;

drop trigger if exists trg_pick_locks on participants;
create trigger trg_pick_locks before insert or update on participants
for each row execute function public.enforce_pick_locks();
