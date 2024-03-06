This is a a repository containing the Streamlit version of the [Snowflake
security dashboards][1].

# Deployment

## Streamlit in Snowflake

The repository includes an [action][2] that deploys the application in an account
configured through Github action secrets.

To use this:

1. Run the [SQL setup](./deployment_models/Streamlit-in-Snowflake.sql)
2. Fork this repo
3. Fill in the action secrets:

    - `SIS_GRANT_TO_ROLE`
    - `SIS_QUERY_WAREHOUSE`
    - `SNOWFLAKE_ACCOUNT`
    - `SNOWFLAKE_DATABASE`
    - `SNOWFLAKE_PASSWORD`
    - `SNOWFLAKE_ROLE`
    - `SNOWFLAKE_SCHEMA`
    - `SNOWFLAKE_USER`
    - `SNOWFLAKE_WAREHOUSE`

4. Run the "Deploy Streamlit in Snowflake" action

[1]:
https://quickstarts.snowflake.com/guide/security_dashboards_for_snowflake/index.html

[2]:
./.github/workflows/deploy-streamlit-in-snowflake.yml
