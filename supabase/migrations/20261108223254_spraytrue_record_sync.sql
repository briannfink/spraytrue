-- Additive v2.14 sync: legacy user_data and tankmix_sync are deliberately untouched.
create table public.user_records (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  collection text not null check (collection in ('library','mixes','log','fields')),
  record_id text not null check (length(record_id) between 1 and 200),
  value jsonb not null check (jsonb_typeof(value)='object'),
  version uuid not null default gen_random_uuid(),
  updated_at timestamptz not null default now(),
  deleted boolean not null default false,
  primary key (user_id,collection,record_id)
);
-- Durable receipts make retrying after a lost network response idempotent.
create table public.user_record_ops (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  op_id text not null,
  conflict boolean not null default false,
  primary key (user_id,op_id)
);
alter table public.user_records enable row level security;
alter table public.user_record_ops enable row level security;
revoke all on public.user_records, public.user_record_ops from anon, public, authenticated;
grant select,insert,update,delete on public.user_records, public.user_record_ops to authenticated;
create policy records_owner on public.user_records for all to authenticated
  using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create policy record_ops_owner on public.user_record_ops for all to authenticated
  using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create function public.spraytrue_records_sync(p_changes jsonb default '[]'::jsonb)
returns jsonb language plpgsql security invoker set search_path=public,pg_temp as $$
declare
  owner_id uuid := auth.uid(); change jsonb; legacy record; item jsonb;
  cur public.user_records%rowtype; val jsonb; rid text; col text; op text;
  copy_id text; conflicts integer:=0; was_conflict boolean;
  ack jsonb:='[]'::jsonb; seeded boolean;
begin
  if owner_id is null then raise exception 'Sign in required'; end if;
  if jsonb_typeof(p_changes)<>'array' or jsonb_array_length(p_changes)>100 then raise exception 'Invalid record batch'; end if;
  -- Serialize bootstrap + writes per account. An optimistic version mismatch never overwrites another edit.
  perform pg_advisory_xact_lock(hashtextextended(owner_id::text,214));
  insert into public.user_record_ops(user_id,op_id) values(owner_id,'bootstrap') on conflict do nothing;
  seeded := found;
  if seeded then
    for legacy in select key,value from public.user_data where user_id=owner_id and not deleted
      and key in ('tm.library','tm.mixes','tm.log','tm.fields') and jsonb_typeof(value)='array'
    loop
      col:=substring(legacy.key from 4);
      for item in select x from jsonb_array_elements(legacy.value) x where jsonb_typeof(x)='object'
      loop
        rid:=coalesce(nullif(item->>'id',''),'legacy-'||md5(item::text));
        val:=jsonb_set(item,'{id}',to_jsonb(rid));
        if col='mixes' and jsonb_typeof(val->'mix')='object' then val:=jsonb_set(val,'{mix,id}',to_jsonb(rid)); end if;
        insert into public.user_records(user_id,collection,record_id,value)
          values(owner_id,col,rid,val) on conflict do nothing;
      end loop;
    end loop;
  end if;
  for change in select x from jsonb_array_elements(p_changes) x
  loop
    col:=change->>'collection'; rid:=change->>'record_id'; op:=(change->>'op_id')::uuid::text;
    if col is null or col not in ('library','mixes','log','fields') or rid is null or length(rid) not between 1 and 200 or op is null then raise exception 'Invalid record'; end if;
    select conflict into was_conflict from public.user_record_ops where user_id=owner_id and op_id=op;
    if found then
      ack:=ack||jsonb_build_array(op); if was_conflict then conflicts:=conflicts+1; end if; continue;
    end if;
    select * into cur from public.user_records where user_id=owner_id and collection=col and record_id=rid for update;
    val:=coalesce(nullif(change->'value','null'::jsonb),cur.value,'{}'::jsonb);
    if jsonb_typeof(val)<>'object' then raise exception 'Record must be an object'; end if;
    val:=jsonb_set(val,'{id}',to_jsonb(rid));
    was_conflict:=false;
    if not found then
      insert into public.user_records(user_id,collection,record_id,value,version,deleted)
        values(owner_id,col,rid,val,op::uuid,coalesce((change->>'deleted')::boolean,false));
    elsif cur.deleted=coalesce((change->>'deleted')::boolean,false) and (cur.value=val or cur.deleted) then
      null; -- identical edit/delete: acknowledge without a duplicate
    elsif cur.version=nullif(change->>'base_version','')::uuid then
      update public.user_records set value=val,deleted=coalesce((change->>'deleted')::boolean,false),version=op::uuid,updated_at=clock_timestamp()
        where user_id=owner_id and collection=col and record_id=rid;
    else
      -- Keep both sides, including edit-v-delete. Never resurrect/overwrite the original tombstone.
      was_conflict:=true; conflicts:=conflicts+1; copy_id:='conflict-'||op;
      val:=jsonb_set(val,'{id}',to_jsonb(copy_id))||jsonb_build_object('_syncConflict',jsonb_build_object('originalId',rid,'deleteRequested',coalesce((change->>'deleted')::boolean,false),'note','Conflicting edits kept. Review both versions before deleting either.'));
      if col='log' then val:=val||jsonb_build_object('notes',coalesce(val->>'notes','')||E'\n[Sync conflict copy — review both versions; a deletion may have been requested.]');
      else val:=val||jsonb_build_object('name',coalesce(val->>'name','Untitled')||' (conflict copy)'); end if;
      if col='mixes' and jsonb_typeof(val->'mix')='object' then
        val:=jsonb_set(jsonb_set(val,'{mix,id}',to_jsonb(copy_id)),'{mix,name}',val->'name');
      end if;
      insert into public.user_records(user_id,collection,record_id,value,version) values(owner_id,col,copy_id,val,op::uuid);
    end if;
    insert into public.user_record_ops(user_id,op_id,conflict) values(owner_id,op,was_conflict);
    ack:=ack||jsonb_build_array(op);
  end loop;
  return jsonb_build_object('applied',ack,'conflicts',conflicts);
end;
$$;
revoke all on function public.spraytrue_records_sync(jsonb) from public,anon;
grant execute on function public.spraytrue_records_sync(jsonb) to authenticated;
