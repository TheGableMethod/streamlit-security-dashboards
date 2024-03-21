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

## Streamlit in local docker container

1. Clone this repository and change current directory to its root
2. Build and run the docker image:

    ```shell
    $ docker build . -t sentry:latest -f deployment_models/local-docker/Dockerfile
    ...
    naming to docker.io/library/sentry:latest
    $ docker run --rm --mount type=bind,source=$(pwd)/.streamlit,target=/app/.streamlit,readonly --publish-all sentry:latest
    ...
      You can now view your Streamlit app in your browser.
    ...
    ```

    Replace `$(pwd)/.streamlit` with a path to the directory containing
    [Streamlit secrets toml file][3].

    `--publish-all` will assign a random port to the container; you can use
    `docker ps` to determine which port is forwarded to `8501` inside the
    container.

3. (if needed) find out the port that Docker assigned to the container using
   `docker ps`:

   ```shell
   $ docker ps --format "{{.Image}}\t{{.Ports}}"
     sentry:latest	0.0.0.0:55000->8501/tcp
   ```

4. Open `http://localhost:55000`

[1]:
https://quickstarts.snowflake.com/guide/security_dashboards_for_snowflake/index.html

[2]:
./.github/workflows/deploy-streamlit-in-snowflake.yml

[3]:
https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
