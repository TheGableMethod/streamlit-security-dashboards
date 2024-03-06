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

    - `SIS_GRANT_TO_ROLE` – which role should have access to the Streamlit\
(e.g. `ACCOUNTADMIN`)
    - `SIS_QUERY_WAREHOUSE` – warehouse for running Streamlit
    - `SNOWFLAKE_ACCOUNT` – which Snowflake account to deploy Streamlit in
    - `SNOWFLAKE_DATABASE` – which Snowflake database to deploy Streamlit in
    - `SNOWFLAKE_SCHEMA` – which Snowflake schema to deploy Streamlit in
    - `SNOWFLAKE_USER` – user to authenticate
    - `SNOWFLAKE_PASSWORD` – password to authenticate
    - `SNOWFLAKE_ROLE` – authentication role
    - `SNOWFLAKE_WAREHOUSE` – warehouse to execute deployment queries

4. Run the "Deploy Streamlit in Snowflake" action

[1]:
https://quickstarts.snowflake.com/guide/security_dashboards_for_snowflake/index.html

[2]:
./.github/workflows/deploy-streamlit-in-snowflake.yml
