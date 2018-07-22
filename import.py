import sqlite3
from sqlite3 import Error
import csv


# Connect to db
def create_connection(db):
    """Create a database connection to a SQLite database"""
    try:
        conn = sqlite3.connect(db)
        return conn
    except Error as e:
        print(e)
    return None


# Create book table
def create_books():
    conn = create_connection('books.sqlite3')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS books "
                "(isbn TEXT, "
                "title TEXT, "
                "author TEXT,"
                "year TEXT)")

    with open('books.csv') as csvfile:
        books = csv.reader(csvfile)
        for row in books:
            cur.execute("INSERT INTO books (isbn, title, author, year) VALUES (?,?,?,?)", (row[0], row[1], row[2], row[3]))

    conn.commit()
    conn.close()


# Create log in table
def create_login_table():
    conn = create_connection('login.sqlite3')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS login "
                "(username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, email TEXT NOT NULL)")
    conn.commit()
    conn.close()


def create_review_table():
    conn = create_connection('reviews.sqlite3')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS reviews "
                "(isbn TEXT NOT NULL, title TEXT NOT NULL, user TEXT NOT NULL, review TEXT NOT NULL,"
                "rating INT NOT NULL)")


if __name__ == "__main__":
    # create_books()
    create_login_table()
    # create_review_table()