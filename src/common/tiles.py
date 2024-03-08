"""Contains implementation and definitions of Tiles -- the main helper object of this app.

Tiles are self-contained objects that combine the query to fetch the data with the method of rendering a tile on the page.
"""
from collections import namedtuple
from functools import partial
from typing import Any, Callable, Iterable, NamedTuple

import altair as alt
import streamlit as st
from snowflake.snowpark.context import get_active_session

from .queries import (
    ACCOUNTADMIN_GRANTS,
    ACCOUNTADMIN_NO_MFA,
    AUTH_BY_METHOD,
    AUTH_BYPASSING,
    AVG_NUMBER_OF_ROLE_GRANTS_PER_USER,
    DEFAULT_ROLE_CHECK,
    GRANTS_TO_PUBLIC,
    GRANTS_TO_UNMANAGED_SCHEMAS_OUTSIDE_SCHEMA_OWNER,
    LEAST_USED_ROLE_GRANTS,
    MOST_BLOATED_ROLES,
    MOST_DANGEROUS_PERSON,
    NETWORK_POLICY_CHANGES,
    NUM_FAILURES,
    PRIVILEGED_OBJECT_CHANGES_BY_USER,
    SCIM_TOKEN_LIFECYCLE,
    STALE_USERS,
    USER_ROLE_RATIO,
    USERS_BY_OLDEST_PASSWORDS,
)

Tile = namedtuple("Tile", ["Name", "Query"])


class Tile(NamedTuple):
    """Composable object to retrieve data from Snowflake and render it on a page."""

    name: str
    query: str
    # NOTE: this might not work if pushed into a Streamlit container
    render_f: Callable = partial(st.dataframe, use_container_width=True)
    # NOTE: This field should be last; otherwise the _mk_tiles function will need to handle the empty blurb
    blurb: str = ""

    def render(self):
        """Produce a Tile's representation on the page."""
        st.subheader(self.name)
        session = get_active_session()
        with st.spinner("Fetching data..."):
            data = session.sql(self.query).to_pandas()
        self.render_f(data)

        with st.expander(label="More details"):
            st.markdown(self.blurb)

            st.markdown("**Query:**")

            st.code(self.query)


def render(tile: Tile) -> Any:
    """Call Tile.render in a functional way."""
    return tile.render()


def _mk_tiles(*tiles) -> tuple:
    """Generate Tile instances by unpacking the provided iterable."""
    return (Tile(**i) for i in tiles)


altair_chart = partial(
    st.altair_chart, use_container_width=True
)  # NOTE: theme="streamlit" is default


AuthTiles = _mk_tiles(
    {
        "name": "Failures, by User and Reason",
        "query": NUM_FAILURES,
        "render_f": lambda data: altair_chart(
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("USER_NAME", type="nominal", sort="-y", title="User"),
                y=alt.Y("NUM_OF_FAILURES", aggregate="sum", title="Login failures"),
                color="ERROR_MESSAGE",
            ),
        ),
    },
    {
        "name": "Breakdown by Method",
        "query": AUTH_BY_METHOD,
        "render_f": lambda data: altair_chart(
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("COUNT(*)", type="quantitative", title="Event Count"),
                y=alt.Y(
                    "AUTHENTICATION_METHOD", type="nominal", title="Method", sort="-x"
                ),
            ),
        ),
    },
    {
        "name": "Service identities bypassing keypair authentication with a password",
        "query": AUTH_BYPASSING,
        "blurb": "**Note:** this query would need to be adjusted to reflect the service user naming convention.",
    },
)

PrivilegedAccessTiles = _mk_tiles(
    {"name": "ACCOUNTADMIN Grants", "query": ACCOUNTADMIN_GRANTS},
    {"name": "ACCOUNTADMINs that do not use MFA", "query": ACCOUNTADMIN_NO_MFA},
    {"name": "No Default Role or Default is ACCOUNTADMIN", "query": DEFAULT_ROLE_CHECK},
)

IdentityManagementTiles = _mk_tiles(
    {"name": "Users by oldest Passwords", "query": USERS_BY_OLDEST_PASSWORDS},
    {"name": "Stale users", "query": STALE_USERS},
    {"name": "SCIM Token Lifecycle", "query": SCIM_TOKEN_LIFECYCLE},
)

LeastPrivilegedAccesTiles = _mk_tiles(
    {
        "name": "Most Dangerous Person",
        "query": MOST_DANGEROUS_PERSON,
        "render_f": lambda data: altair_chart(
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X(
                    "NUM_OF_PRIVS", type="quantitative", title="Number of privileges"
                ),
                y=alt.Y("USER", type="nominal", title="User", sort="-x"),
            ),
        ),
    },
    {"name": "Most Bloated Roles", "query": MOST_BLOATED_ROLES},
    {"name": "Grants to Public", "query": GRANTS_TO_PUBLIC},
    {
        "name": "Grants to unmanaged schemas outside schema owner",
        "query": GRANTS_TO_UNMANAGED_SCHEMAS_OUTSIDE_SCHEMA_OWNER,
    },
    {"name": "User to Role Ratio (larger is better)", "query": USER_ROLE_RATIO},
    {
        "name": "Average Number of Role Grants per User (~5-10)",
        "query": AVG_NUMBER_OF_ROLE_GRANTS_PER_USER,
    },
    {"name": "Least Used Role Grants", "query": LEAST_USED_ROLE_GRANTS},
)

ConfigurationManagementTiles = _mk_tiles(
    {
        "name": "Privileged object changes by User",
        "query": PRIVILEGED_OBJECT_CHANGES_BY_USER,
        "render_f": lambda data: altair_chart(
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("USER_NAME", type="nominal", sort="-y", title="User"),
                y=alt.Y("QUERY_TEXT", aggregate="count", title="Number of Changes"),
            )
        ),
    },
    {"name": "Network Policy Changes", "query": NETWORK_POLICY_CHANGES},
)
