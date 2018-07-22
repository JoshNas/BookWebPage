import sqlite3
from sqlite3 import Error

# Connect to db
def create_connection(db):
    """Create a database connection to a SQLite database"""
    try:
        conn = sqlite3.connect(db)
        return conn
    except Error as e:
        print(e)
    return None


title = 'I, Robot'
isbn = '0553803700'

conn = create_connection('books.sqlite3')
cur = conn.cursor()
cur.execute("SELECT * from books WHERE isbn = :isbn", {"isbn": isbn})
# cur.execute("SELECT * from books WHERE title LIKE :title", {"title": '{}{}'.format(title, '%')})
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()
