from collections import namedtuple
from typing import Any, Callable, NamedTuple

import altair as alt
import streamlit as st
from snowflake.snowpark.context import get_active_session

from .queries import (
    ACCOUNTADMIN_GRANTS,
    ACCOUNTADMIN_NO_MFA,
    AUTH_BY_METHOD,
    AUTH_BYPASSING,
    MOST_BLOATED_ROLES,
    MOST_DANGEROUS_PERSON,
    NETWORK_POLICY_CHANGES,
    NUM_FAILURES,
    PRIVILEGED_OBJECT_CHANGES_BY_USER,
    SCIM_TOKEN_LIFECYCLE,
    STALE_USERS,
    USERS_BY_OLDEST_PASSWORDS,
)

Tile = namedtuple("Tile", ["Name", "Query"])


class Tile(NamedTuple):
    name: str
    query: str
    render_f: Callable = (
        st.dataframe
    )  # NOTE: this might not work if pushed into a Streamlit container

    def render(self):
        session = get_active_session()
        with st.spinner("Fetching data..."):
            data = session.sql(self.query).to_pandas()
        self.render_f(data)


def render(tile: Tile) -> Any:
    st.subheader(tile.name)
    return tile.render()


AuthFailures = Tile(
    "Failures, by User and Reason",
    NUM_FAILURES,
    lambda data: st.altair_chart(
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("USER_NAME", type="nominal", sort="-y", title="User"),
            y=alt.Y("NUM_OF_FAILURES", aggregate="sum", title="Login failures"),
            color="ERROR_MESSAGE",
        ),
        use_container_width=True,
        theme="streamlit",
    ),
)

AuthByMethod = Tile(
    "Breakdown by Method",
    AUTH_BY_METHOD,
    lambda data: st.altair_chart(
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("COUNT(*)", type="quantitative", title="Event Count"),
            y=alt.Y("AUTHENTICATION_METHOD", type="nominal", title="Method", sort="-x"),
        ),
        use_container_width=True,
        theme="streamlit",
    ),
)

# TODO: maybe allow customizable filter?
AuthBypassing = Tile(
    "Service identities bypassing keypair authentication with a password",
    AUTH_BYPASSING,
)

AuthTiles = (AuthFailures, AuthByMethod, AuthBypassing)

PrivilegedAccessAccountAdminGrants = Tile("ACCOUNTADMIN Grants", ACCOUNTADMIN_GRANTS)

PrivilegedAccessNoMfa = Tile("ACCOUNTADMINs that do not use MFA", ACCOUNTADMIN_NO_MFA)

PrivilegedAccessTiles = (PrivilegedAccessAccountAdminGrants, PrivilegedAccessNoMfa)

IdentityUsersByOldestPasswords = Tile(
    "Users by oldest Passwords", USERS_BY_OLDEST_PASSWORDS
)

StaleUsers = Tile("Stale users", STALE_USERS)

SCIMTokenLifecycle = Tile("SCIM Token Lifecycle", SCIM_TOKEN_LIFECYCLE)

IdentityManagementTiles = (
    IdentityUsersByOldestPasswords,
    StaleUsers,
    SCIMTokenLifecycle,
)

MostDangerousPersonTile = Tile(
    "Most Dangerous Person",
    MOST_DANGEROUS_PERSON,
    lambda data: st.altair_chart(
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("NUM_OF_PRIVS", type="quantitative", title="Number of privileges"),
            y=alt.Y("USER", type="nominal", title="User", sort="-x"),
        )
    ),
    # TODO
    # grantee_name as user,
    #     count(a.role) num_of_roles,
    #     sum(num_of_privs) num_of_privs
)

MostBloatedRoles = Tile("Most Bloated Roles", MOST_BLOATED_ROLES)
LeastPrivilegedAccesTiles = (MostDangerousPersonTile, MostBloatedRoles)

PrivilegedObjectChangesByUser = Tile(
    "Privileged object changes by User",
    PRIVILEGED_OBJECT_CHANGES_BY_USER,
    lambda data: st.altair_chart(
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("USER_NAME", type="nominal", sort="-y", title="User"),
            y=alt.Y("QUERY_TEXT", aggregate="count", title="Number of Changes"),
        )
    ),
)
NetworkPolicyChanges = Tile("Network Policy Changes", NETWORK_POLICY_CHANGES)

ConfigurationManagementTiles = (PrivilegedObjectChangesByUser, NetworkPolicyChanges)
