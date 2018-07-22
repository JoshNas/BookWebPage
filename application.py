import os
import requests
from flask import Flask, session, render_template, request, url_for, redirect, flash
from flask_session import Session
import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Connect to db
def create_connection(database):
    """Create a database connection to a SQLite database"""
    try:
        db = sqlite3.connect(database)
        return db
    except Error as e:
        print(e)
    return None


@app.route("/", methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = create_connection('login.sqlite3')
        cur = db.cursor()
        user = cur.execute('SELECT * FROM login WHERE username = :username', {'username': username}).fetchone()

        if user is None:
            error = 'That user does not exist'
        elif not check_password_hash(user[1], password):
            error = 'Incorrect password'

        if error is None:
            session.clear()
            session['user'] = user[0]
            return redirect(url_for('search'))

    return render_template('index.html', error=error)


@app.route("/create", methods=['GET', 'POST'])
def create():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        db = create_connection('login.sqlite3')
        cur = db.cursor()
        error = None

        if not username:
            error = 'Please enter a valid username'
        elif not password:
            error = 'Please enter a valid password'
        elif cur.execute(
            'SELECT username FROM login WHERE username = :username', {'username': username}
        ).fetchone() is not None:
            error = f'User {username} is already registered'

        if error is None:
            cur.execute('INSERT INTO login (username, password, email) VALUES (:username, :password, :email)',
                        {'username': username, 'password': generate_password_hash(password), 'email': email})
            db.commit()
            db.close()
            return redirect(url_for('index'))
        # look in to how to properly use flash
        flash(error)

    return render_template('create.html', error=error)


@app.route("/search", methods=['GET', 'POST'])
def search():
    if session["user"] is None:
        redirect("/")
    result = None
    title = request.form.get("title")
    author = request.form.get("author")
    isbn = request.form.get("isbn")

    conn = create_connection('books.sqlite3')
    cur = conn.cursor()

    # create book list if not already exists
    if session.get("books") is None:
        session["books"] = []

    if author is not None:
        if len(author) > 0:
            cur.execute("SELECT * from books WHERE author LIKE :author",
                        {"author": f'%{author}%'})
        result = cur.fetchall()

    if title is not None:
        if len(title) > 0 and len(author) > 0:
            cur.execute("SELECT * from books WHERE title LIKE :title and author LIKE :author",
                        {"title": f'%{title}%', "author": f'%{author}%'})
            result = cur.fetchall()
        elif len(title) > 0:
            cur.execute("SELECT * from books WHERE title LIKE :title",
                        {"title": f'%{title}%'})
            result = cur.fetchall()

    if isbn is not None:
        if (len(isbn)) > 0:
            cur.execute("SELECT * from books WHERE isbn = :isbn", {"isbn": isbn})
            result = cur.fetchall()

    ids = []
    if result is not None:
        for b in result:
            ids.append(b[0])

    if result is not None:
        # cnt is used to index out title and author from result
        cnt = 0
        for i in ids:
            info = requests.get("https://www.goodreads.com/book/review_counts.json",
                                params={"key": "DegAVuZjeOhQmAcwEr33w", "isbns": i})

            info = info.json()
            rating = info['books'][0]['average_rating']

            session["books"].append({'title': result[cnt][1], 'author': result[cnt][2], 'rating': rating})
            cnt += 1

    conn.close()
    return render_template('search.html', books=session["books"], name=session["user"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route("/book/<author>/<title>", methods=['GET', 'POST'])
def books_page(title, author):
    if title is not None:
        conn = create_connection('books.sqlite3')
        cur = conn.cursor()
        cur.execute("SELECT * from books WHERE title LIKE :title", {"title": f'%{title}%', })
        info = cur.fetchall()
        isbn = info[0][0]
        year = info[0][3]
        info = requests.get("https://www.goodreads.com/book/review_counts.json",
                            params={"key": "DegAVuZjeOhQmAcwEr33w", "isbns": isbn})

        info = info.json()
        rating = info['books'][0]['average_rating']
        session["book"] = [isbn, title]
        conn.close()

        conn = create_connection('reviews.sqlite3')
        cur = conn.cursor()
        cur.execute("SELECT * from reviews WHERE isbn = :isbn", {'isbn': isbn})
        result = cur.fetchall()
        reviews = []
        for r in result:
            reviews.append(r[3:])

        return render_template('book.html', title=title, author=author, year=year, rating=rating, isbn=isbn, reviews=reviews)


@app.route("/submit", methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        review = request.form['review']
        isbn = session["book"][0]
        title = session["book"][1]
        user = session["user"]
        rating = 5
        conn = create_connection('reviews.sqlite3')
        cur = conn.cursor()
        cur.execute("INSERT INTO reviews (isbn, title, user, review, rating) "
                    "VALUES (:isbn, :title, :user, :review, :rating)",
                    {'isbn': isbn, 'title': title, 'user': user, 'review': review, 'rating': rating})
        conn.commit()
        conn.close()

        return render_template('submit.html', review=review)
    else:
        return render_template('submit.html')


if __name__ == '__main__':
    app.run(use_reloader=True, debug=True)
