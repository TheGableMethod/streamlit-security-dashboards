"""Module with queries to be run in the app."""

_SCHEMA = "SNOWFLAKE.ACCOUNT_USAGE"

NUM_FAILURES = f"""
select
    user_name,
    error_message,
    count(*) num_of_failures
from
    {_SCHEMA}.login_history
where
    is_success = 'NO'
group by
    user_name,
    error_message
order by
    num_of_failures desc;
"""

AUTH_BY_METHOD = f"""
select
   first_authentication_factor || ' ' ||nvl(second_authentication_factor, '') as authentication_method
   , count(*)
    from {_SCHEMA}.login_history
    where is_success = 'YES'
    and user_name != 'WORKSHEETS_APP_USER'
    group by authentication_method
    order by count(*) desc;
"""

AUTH_BYPASSING = f"""
SELECT
 l.user_name,
 first_authentication_factor,
 second_authentication_factor,
 count(*) as Num_of_events
FROM {_SCHEMA}.login_history as l
JOIN {_SCHEMA}.users u on l.user_name = u.name and l.user_name ilike '%svc' and has_rsa_public_key = 'true'
WHERE is_success = 'YES'
AND first_authentication_factor != 'RSA_KEYPAIR'
GROUP BY l.user_name, first_authentication_factor, second_authentication_factor
ORDER BY count(*) desc;
"""

ACCOUNTADMIN_GRANTS = f"""
select
    user_name || ' granted the ' || role_name || ' role on ' || end_time as Description, query_text as Statement
from
    {_SCHEMA}.query_history
where
    execution_status = 'SUCCESS'
    and query_type = 'GRANT'
    and query_text ilike '%grant%accountadmin%to%'
order by
    end_time desc;
"""

ACCOUNTADMIN_NO_MFA = f"""
select u.name,
timediff(days, last_success_login, current_timestamp()) || ' days ago' last_login ,
timediff(days, password_last_set_time,current_timestamp(6)) || ' days ago' password_age
from {_SCHEMA}.users u
join {_SCHEMA}.grants_to_users g on grantee_name = name and role = 'ACCOUNTADMIN' and g.deleted_on is null
where ext_authn_duo = false and u.deleted_on is null and has_password = true
order by last_success_login desc;
"""

USERS_BY_OLDEST_PASSWORDS = f"""
select name, datediff('day', password_last_set_time, current_timestamp()) || ' days ago' as password_last_changed from {_SCHEMA}.users
where deleted_on is null and
password_last_set_time is not null
order by password_last_set_time;
"""

STALE_USERS = f"""
select name, datediff("day", nvl(last_success_login, created_on), current_timestamp()) || ' days ago' Last_Login from {_SCHEMA}.users
where deleted_on is null
order by datediff("day", nvl(last_success_login, created_on), current_timestamp()) desc;
"""

SCIM_TOKEN_LIFECYCLE = f"""
select
    user_name as by_whom,
    datediff('day', start_time, current_timestamp()) || ' days ago' as created_on,
    ADD_MONTHS(start_time, 6) as expires_on,
    datediff(
        'day',
        current_timestamp(),
        ADD_MONTHS(end_time, 6)
    ) as expires_in_days
from
    {_SCHEMA}.query_history
where
    execution_status = 'SUCCESS'
    and query_text ilike 'select%SYSTEM$GENERATE_SCIM_ACCESS_TOKEN%'
    and query_text not ilike 'select%where%SYSTEM$GENERATE_SCIM_ACCESS_TOKEN%'
order by
    expires_in_days;
"""

MOST_DANGEROUS_PERSON = f"""
with role_hier as (
    --Extract all Roles
    select
        grantee_name,
        name
    from
        {_SCHEMA}.grants_to_roles
    where
        granted_on = 'ROLE'
        and privilege = 'USAGE'
        and deleted_on is null
    union all
        --Adding in dummy records for "root" roles
    select
        'root',
        r.name
    from
        {_SCHEMA}.roles r
    where
        deleted_on is null
        and not exists (
            select
                1
            from
                {_SCHEMA}.grants_to_roles gtr
            where
                gtr.granted_on = 'ROLE'
                and gtr.privilege = 'USAGE'
                and gtr.name = r.name
                and deleted_on is null
        )
) --CONNECT BY to create the polyarchy and SYS_CONNECT_BY_PATH to flatten it
,
role_path_pre as(
    select
        name,
        level,
        sys_connect_by_path(name, ' -> ') as path
    from
        role_hier connect by grantee_name = prior name start with grantee_name = 'root'
    order by
        path
) --Removing leading delimiter separately since there is some issue with how it interacted with sys_connect_by_path
,
role_path as (
    select
        name,
        level,
        substr(path, len(' -> ')) as path
    from
        role_path_pre
) --Joining in privileges from GRANT_TO_ROLES
,
role_path_privs as (
    select
        path,
        rp.name as role_name,
        privs.privilege,
        granted_on,
        privs.name as priv_name,
        'Role ' || path || ' has ' || privilege || ' on ' || granted_on || ' ' || privs.name as Description
    from
        role_path rp
        left join {_SCHEMA}.grants_to_roles privs on rp.name = privs.grantee_name
        and privs.granted_on != 'ROLE'
        and deleted_on is null
    order by
        path
) --Aggregate total number of priv's per role, including hierarchy
,
role_path_privs_agg as (
    select
        trim(split(path, ' -> ') [0]) role,
        count(*) num_of_privs
    from
        role_path_privs
    group by
        trim(split(path, ' -> ') [0])
    order by
        count(*) desc
) --Most Dangerous Man - final query
select
    grantee_name as user,
    count(a.role) num_of_roles,
    sum(num_of_privs) num_of_privs
from
    {_SCHEMA}.grants_to_users u
    join role_path_privs_agg a on a.role = u.role
where
    u.deleted_on is null
group by
    user
order by
    num_of_privs desc;
"""

MOST_BLOATED_ROLES = f"""
--Role Hierarchy
with role_hier as (
    --Extract all Roles
    select
        grantee_name,
        name
    from
        {_SCHEMA}.grants_to_roles
    where
        granted_on = 'ROLE'
        and privilege = 'USAGE'
        and deleted_on is null
    union all
        --Adding in dummy records for "root" roles
    select
        'root',
        r.name
    from
        {_SCHEMA}.roles r
    where
        deleted_on is null
        and not exists (
            select
                1
            from
                {_SCHEMA}.grants_to_roles gtr
            where
                gtr.granted_on = 'ROLE'
                and gtr.privilege = 'USAGE'
                and gtr.name = r.name
                and deleted_on is null
        )
) --CONNECT BY to create the polyarchy and SYS_CONNECT_BY_PATH to flatten it
,
role_path_pre as(
    select
        name,
        level,
        sys_connect_by_path(name, ' -> ') as path
    from
        role_hier connect by grantee_name = prior name start with grantee_name = 'root'
    order by
        path
) --Removing leading delimiter separately since there is some issue with how it interacted with sys_connect_by_path
,
role_path as (
    select
        name,
        level,
        substr(path, len(' -> ')) as path
    from
        role_path_pre
) --Joining in privileges from GRANT_TO_ROLES
,
role_path_privs as (
    select
        path,
        rp.name as role_name,
        privs.privilege,
        granted_on,
        privs.name as priv_name,
        'Role ' || path || ' has ' || privilege || ' on ' || granted_on || ' ' || privs.name as Description
    from
        role_path rp
        left join {_SCHEMA}.grants_to_roles privs on rp.name = privs.grantee_name
        and privs.granted_on != 'ROLE'
        and deleted_on is null
    order by
        path
) --Aggregate total number of priv's per role, including hierarchy
,
role_path_privs_agg as (
    select
        trim(split(path, ' -> ') [0]) role,
        count(*) num_of_privs
    from
        role_path_privs
    group by
        trim(split(path, ' -> ') [0])
    order by
        count(*) desc
)
select * from role_path_privs_agg order by num_of_privs desc
"""

PRIVILEGED_OBJECT_CHANGES_BY_USER = f"""
SELECT
    query_text,
    user_name,
    role_name,
    end_time
  FROM {_SCHEMA}.query_history
    WHERE execution_status = 'SUCCESS'
      AND query_type NOT in ('SELECT')
      AND (query_text ILIKE '%create role%'
          OR query_text ILIKE '%manage grants%'
          OR query_text ILIKE '%create integration%'
          OR query_text ILIKE '%create share%'
          OR query_text ILIKE '%create account%'
          OR query_text ILIKE '%monitor usage%'
          OR query_text ILIKE '%ownership%'
          OR query_text ILIKE '%drop table%'
          OR query_text ILIKE '%drop database%'
          OR query_text ILIKE '%create stage%'
          OR query_text ILIKE '%drop stage%'
          OR query_text ILIKE '%alter stage%'
          )
  ORDER BY end_time desc;
"""

NETWORK_POLICY_CHANGES = f"""
select user_name || ' made the following Network Policy change on ' || end_time || ' [' ||  query_text || ']' as Events
   from {_SCHEMA}.query_history where execution_status = 'SUCCESS'
   and query_type in ('CREATE_NETWORK_POLICY', 'ALTER_NETWORK_POLICY', 'DROP_NETWORK_POLICY')
   or (query_text ilike '% set network_policy%' or
       query_text ilike '% unset network_policy%')
       and query_type != 'SELECT' and query_type != 'UNKNOWN'
   order by end_time desc;
"""

DEFAULT_ROLE_CHECK = f"""
select role, grantee_name, default_role
from {_SCHEMA}."GRANTS_TO_USERS" join "SNOWFLAKE"."ACCOUNT_USAGE"."USERS"
on users.name = grants_to_users.grantee_name
where role = 'ACCOUNTADMIN'
and grants_to_users.deleted_on is null
and users.deleted_on is null
order by grantee_name;
"""

GRANTS_TO_PUBLIC = f"""
select user_name, role_name, query_text, end_time
from {_SCHEMA}.query_history where execution_status = 'SUCCESS'
and query_type = 'GRANT' and
query_text ilike '%to%public%'
order by end_time desc
"""

GRANTS_TO_UNMANAGED_SCHEMAS_OUTSIDE_SCHEMA_OWNER = f"""
select table_catalog,  
        table_schema,  
        schema_owner,        
        privilege,  
        granted_by,  
        granted_on,  
        name,  
        granted_to,  
        grantee_name,  
        grant_option 
   from {_SCHEMA}.grants_to_roles gtr 
   join {_SCHEMA}.schemata s 
     on s.catalog_name = gtr.table_catalog 
    and s.schema_name = gtr.table_schema 
  where deleted_on is null 
    and deleted is null 
    and granted_by not in ('ACCOUNTADMIN', 'SECURITYADMIN') //add other roles with MANAGE GRANTS if applicable 
    and is_managed_access = 'NO' 
    and schema_owner <> granted_by 
  order by  
        table_catalog,  
        table_schema;
"""

USER_ROLE_RATIO = f"""
select 
round(count(*) / (select count(*) from {_SCHEMA}.roles),1)
from {_SCHEMA}.users;
"""

AVG_NUMBER_OF_ROLE_GRANTS_PER_USER = f"""
with role_grants_per_user (user, role_count) as (
select grantee_name as user, count(*) role_count from {_SCHEMA}.grants_to_users where deleted_on is null group by grantee_name order by role_count desc)
select round(avg(role_count),1) from role_grants_per_user;
"""


LEAST_USED_ROLE_GRANTS = f"""
with least_used_roles (user_name, role_name, last_used, times_used) as
(select user_name, role_name, max(end_time), count(*) from {_SCHEMA}.query_history group by user_name, role_name order by user_name, role_name)
select grantee_name, role, nvl(last_used, (select min(start_time) from {_SCHEMA}.query_history)) last_used, nvl(times_used, 0) times_used, datediff(day, created_on, current_timestamp()) || ' days ago' age
from {_SCHEMA}.grants_to_users
left join least_used_roles on user_name = grantee_name and role = role_name
where deleted_on is null order by last_used, times_used, age desc;
"""
