import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).parent / "data" / "philly_yelp.db"

st.set_page_config(page_title="Philly Yelp Dashboard", layout="wide")


@st.cache_resource
def get_connection():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


@st.cache_data
def load_all_categories():
    # categories are stored as one comma separated string per business,
    # so we have to split them ourselves before we can count them
    conn = get_connection()
    df = pd.read_sql("SELECT categories FROM business WHERE categories IS NOT NULL", conn)
    cats = df["categories"].str.split(",").explode().str.strip().value_counts()
    return cats


def run_query(sql, params=()):
    conn = get_connection()
    return pd.read_sql(sql, conn, params=params)


st.sidebar.header("Filters")

star_range = st.sidebar.slider("Business star rating", 1.0, 5.0, (1.0, 5.0), step=0.5)
min_reviews = st.sidebar.slider("Minimum review count", 0, 200, 0, step=5)
open_status = st.sidebar.radio("Status", ["All", "Open only", "Closed only"])

top_categories = load_all_categories().head(30).index.tolist()
selected_categories = st.sidebar.multiselect("Category (optional)", top_categories)


def build_where(alias=""):
    # builds the WHERE clause + params for whatever filters are currently
    # selected in the sidebar. alias lets us reuse this for the trends
    # query below, which joins business to review and needs "b.stars"
    # instead of just "stars"
    p = alias + "." if alias else ""
    clauses = [p + "stars BETWEEN ? AND ?", p + "review_count >= ?"]
    vals = [star_range[0], star_range[1], min_reviews]

    if open_status == "Open only":
        clauses.append(p + "is_open = 1")
    elif open_status == "Closed only":
        clauses.append(p + "is_open = 0")

    if selected_categories:
        or_clause = " OR ".join(p + "categories LIKE ?" for _ in selected_categories)
        clauses.append("(" + or_clause + ")")
        for c in selected_categories:
            vals.append("%" + c + "%")

    return " AND ".join(clauses), vals


where_sql, params = build_where()

st.title("Philadelphia Yelp Dashboard")
st.caption("Exploring Philly businesses, reviews, and rating trends from the Yelp Academic Dataset")

kpi_df = run_query(
    f"""
    SELECT COUNT(*) AS total_businesses,
           AVG(stars) AS avg_rating,
           SUM(review_count) AS total_reviews,
           AVG(is_open) * 100 AS pct_open
    FROM business
    WHERE {where_sql}
    """,
    params,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Businesses", f"{int(kpi_df['total_businesses'][0]):,}")
if kpi_df["total_businesses"][0]:
    col2.metric("Avg Rating", f"{kpi_df['avg_rating'][0]:.2f}")
    col4.metric("% Open", f"{kpi_df['pct_open'][0]:.0f}%")
else:
    col2.metric("Avg Rating", "-")
    col4.metric("% Open", "-")
col3.metric("Total Reviews", f"{int(kpi_df['total_reviews'][0] or 0):,}")

st.divider()

tab_overview, tab_categories, tab_trends, tab_map, tab_top = st.tabs(
    ["Overview", "Categories", "Trends", "Map", "Top Businesses"]
)

with tab_overview:
    st.subheader("Rating distribution")
    dist_df = run_query(
        f"SELECT stars, COUNT(*) AS count FROM business WHERE {where_sql} GROUP BY stars ORDER BY stars",
        params,
    )
    if dist_df.empty:
        st.info("No businesses match the current filters.")
    else:
        fig = px.bar(dist_df, x="stars", y="count", labels={"stars": "Star rating", "count": "# Businesses"})
        st.plotly_chart(fig, use_container_width=True)

with tab_categories:
    st.subheader("Top categories among filtered businesses")
    cat_df = run_query(f"SELECT categories FROM business WHERE {where_sql} AND categories IS NOT NULL", params)

    if len(cat_df) == 0:
        st.info("No businesses match the current filters.")
    else:
        all_cats = []
        for row in cat_df["categories"]:
            for c in row.split(","):
                all_cats.append(c.strip())

        counts = pd.Series(all_cats).value_counts().head(15).reset_index()
        counts.columns = ["category", "count"]
        counts = counts.sort_values("count")

        fig = px.bar(counts, x="count", y="category", orientation="h", labels={"count": "# Businesses", "category": ""})
        st.plotly_chart(fig, use_container_width=True)

with tab_trends:
    st.subheader("Review volume & average rating over time")
    trend_where, trend_params = build_where(alias="b")
    trend_df = run_query(
        f"""
        SELECT strftime('%Y-%m', r.date) AS month,
               COUNT(*) AS review_count,
               AVG(r.stars) AS avg_stars
        FROM review r
        JOIN business b ON b.business_id = r.business_id
        WHERE {trend_where}
        GROUP BY month
        ORDER BY month
        """,
        trend_params,
    )
    if trend_df.empty:
        st.info("No reviews match the current filters.")
    else:
        st.plotly_chart(px.line(trend_df, x="month", y="review_count", labels={"month": "", "review_count": "Reviews / month"}), use_container_width=True)
        st.plotly_chart(px.line(trend_df, x="month", y="avg_stars", labels={"month": "", "avg_stars": "Avg star rating"}), use_container_width=True)

with tab_map:
    st.subheader("Business locations")
    map_df = run_query(
        f"SELECT name, latitude, longitude, stars, review_count FROM business WHERE {where_sql} AND latitude IS NOT NULL AND longitude IS NOT NULL",
        params,
    )
    if map_df.empty:
        st.info("No businesses match the current filters.")
    else:
        fig = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="stars",
            size="review_count",
            hover_name="name",
            hover_data={"stars": True, "review_count": True, "latitude": False, "longitude": False},
            color_continuous_scale="RdYlGn",
            zoom=10,
            height=600,
        )
        fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)

with tab_top:
    st.subheader("Top-rated businesses")
    search = st.text_input("Search by business name")

    search_sql = ""
    search_params = list(params)
    if search:
        search_sql = " AND name LIKE ?"
        search_params.append(f"%{search}%")

    top_df = run_query(
        f"""
        SELECT name, categories, stars, review_count, address
        FROM business
        WHERE {where_sql}{search_sql}
        ORDER BY stars DESC, review_count DESC
        LIMIT 25
        """,
        search_params,
    )
    st.dataframe(top_df, use_container_width=True, hide_index=True)
