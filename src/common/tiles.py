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

    def render(self):
        """Produce a Tile's representation on the page."""
        st.subheader(self.name)
        session = get_active_session()
        with st.spinner("Fetching data..."):
            data = session.sql(self.query).to_pandas()
        self.render_f(data)


def render(tile: Tile) -> Any:
    """Call Tile.render in a functional way."""
    return tile.render()


def _mk_tiles(*tiles) -> tuple:
    """Generate Tile instances by unpacking the provided iterable."""
    return (Tile(*i) for i in tiles)


altair_chart = partial(
    st.altair_chart, use_container_width=True
)  # NOTE: theme="streamlit" is default


AuthTiles = _mk_tiles(
    (
        "Failures, by User and Reason",
        NUM_FAILURES,
        lambda data: altair_chart(
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("USER_NAME", type="nominal", sort="-y", title="User"),
                y=alt.Y("NUM_OF_FAILURES", aggregate="sum", title="Login failures"),
                color="ERROR_MESSAGE",
            ),
        ),
    ),
    (
        "Breakdown by Method",
        AUTH_BY_METHOD,
        lambda data: altair_chart(
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("COUNT(*)", type="quantitative", title="Event Count"),
                y=alt.Y(
                    "AUTHENTICATION_METHOD", type="nominal", title="Method", sort="-x"
                ),
            ),
        ),
    ),
    (
        "Service identities bypassing keypair authentication with a password",
        AUTH_BYPASSING,
    ),
)

PrivilegedAccessTiles = _mk_tiles(
    ("ACCOUNTADMIN Grants", ACCOUNTADMIN_GRANTS),
    ("ACCOUNTADMINs that do not use MFA", ACCOUNTADMIN_NO_MFA),
    ("No Default Role or Default is ACCOUNTADMIN", DEFAULT_ROLE_CHECK),
)

IdentityManagementTiles = _mk_tiles(
    ("Users by oldest Passwords", USERS_BY_OLDEST_PASSWORDS),
    ("Stale users", STALE_USERS),
    ("SCIM Token Lifecycle", SCIM_TOKEN_LIFECYCLE),
)

LeastPrivilegedAccesTiles = _mk_tiles(
    (
        "Most Dangerous Person",
        MOST_DANGEROUS_PERSON,
        lambda data: altair_chart(
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X(
                    "NUM_OF_PRIVS", type="quantitative", title="Number of privileges"
                ),
                y=alt.Y("USER", type="nominal", title="User", sort="-x"),
            ),
        ),
    ),
    ("Most Bloated Roles", MOST_BLOATED_ROLES),
    ("Grants to Public", GRANTS_TO_PUBLIC),
    (
        "Grants to unmanaged schemas outside schema owner",
        GRANTS_TO_UNMANAGED_SCHEMAS_OUTSIDE_SCHEMA_OWNER,
    ),
    ("User to Role Ratio (larger is better)", USER_ROLE_RATIO),
    (
        "Average Number of Role Grants per User (~5-10)",
        AVG_NUMBER_OF_ROLE_GRANTS_PER_USER,
    ),
    ("Least Used Role Grants", LEAST_USED_ROLE_GRANTS),
)

ConfigurationManagementTiles = _mk_tiles(
    (
        "Privileged object changes by User",
        PRIVILEGED_OBJECT_CHANGES_BY_USER,
        lambda data: altair_chart(
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("USER_NAME", type="nominal", sort="-y", title="User"),
                y=alt.Y("QUERY_TEXT", aggregate="count", title="Number of Changes"),
            )
        ),
    ),
    ("Network Policy Changes", NETWORK_POLICY_CHANGES),
)
