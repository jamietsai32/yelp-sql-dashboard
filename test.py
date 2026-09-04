import sqlite3
import matplotlib.pyplot as plt

conn = sqlite3.connect("data/philly_yelp.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT stars, COUNT(*) AS num_businesses
    FROM business
    GROUP BY stars
    ORDER BY stars
""")

rows = cursor.fetchall()
conn.close()

# split the rows into two separate lists: one for x-axis, one for y-axis
star_values = [row[0] for row in rows]
counts = [row[1] for row in rows]

plt.bar(star_values, counts, width=0.4)
plt.xlabel("Star rating")
plt.ylabel("Number of businesses")
plt.title("Philly Businesses by Star Rating")
plt.show()