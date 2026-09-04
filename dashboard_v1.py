import sqlite3
import streamlit as st
import matplotlib.pyplot as plt

conn = sqlite3.connect("data/philly_yelp.db")
cursor = conn.cursor()

min_stars = st.slider("Minimum star rating", 1.0, 5.0, 1.0, step=0.5)

cursor.execute("""
    SELECT stars, COUNT(*) AS num_businesses
    FROM business
    WHERE stars >= ?
    GROUP BY stars
    ORDER BY stars
""", (min_stars,))

rows = cursor.fetchall()
conn.close()

star_values = [row[0] for row in rows]
counts = [row[1] for row in rows]

fig, ax = plt.subplots()
ax.bar(star_values, counts, width=0.4)
ax.set_xlabel("Star rating")
ax.set_ylabel("Number of businesses")
ax.set_title("Philly Businesses by Star Rating")

st.pyplot(fig)