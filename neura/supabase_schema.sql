-- Run this in Supabase SQL Editor.
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text,
  role text default 'student',
  created_at timestamptz default now()
);

create table if not exists public.mood_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  mood text not null,
  energy integer,
  context text,
  created_at timestamptz default now()
);

create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  priority text default 'Normal',
  done boolean default false,
  completed_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists public.focus_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  duration_minutes integer default 25,
  mood text,
  started_at timestamptz default now()
);

alter table public.profiles enable row level security;
alter table public.mood_entries enable row level security;
alter table public.tasks enable row level security;
alter table public.focus_sessions enable row level security;

create policy "profiles own" on public.profiles for all using (auth.uid() = id) with check (auth.uid() = id);
create policy "moods own" on public.mood_entries for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "tasks own" on public.tasks for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "focus own" on public.focus_sessions for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Optional profile auto-create after signup.
create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path = public as $$
begin insert into public.profiles(id,name) values(new.id,new.raw_user_meta_data->>'name'); return new; end; $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute procedure public.handle_new_user();
