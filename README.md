# Philadelphia Yelp Dashboard

A little SQL + Streamlit project I built to poke around Yelp's business/review data for Philadelphia. Started as a way to practice SQL beyond basic SELECTs (joins, group bys, parameterized filters) and turned into an actual interactive dashboard.

Live: https://yelp-sql-dashboard-hgktwcakpzdwpwa9vuagzm.streamlit.app/

## What it does

You can filter businesses by star rating, minimum number of reviews, open/closed status, and category, and everything on the page updates based on that — a KPI row up top, a rating distribution chart, the most common categories, review volume/rating trends by month, a map of where everything is, and a searchable table of the top-rated spots.

All of it is backed by real SQL running against a SQLite database, not just pandas filtering after the fact. The filters get turned into a `WHERE` clause with `?` placeholders, and the trends tab does an actual `JOIN` between the business and review tables.

## How it's built

Python, SQLite, pandas to move query results around, Streamlit for the UI, Plotly for the charts/map.

## About the data

This comes from the [Yelp Academic Dataset](https://www.yelp.com/dataset) — I filtered it down to just businesses in Philadelphia (see `01_eda.ipynb` for how). The raw dataset isn't in this repo since Yelp's terms don't allow redistributing it, and it's also just way too big for GitHub (the review file alone is a few GB). What's included instead is a much smaller SQLite file with only the columns the dashboard actually needs — dropping review text and the user table cut it from 1.3GB down to about 80MB.

## Running it yourself

```bash
git clone https://github.com/jamietsai32/yelp-sql-dashboard.git
cd yelp-sql-dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Files

- `app.py` — the dashboard itself
- `01_eda.ipynb` — notebook where I pulled the Philly subset out of the full Yelp dataset and built the SQLite db
- `data/philly_yelp_deploy.db` — the slimmed-down database the app actually reads from
- `requirements.txt` — dependencies
