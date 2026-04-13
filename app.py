from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

DATABASE_URL = os.environ.get("DATABASE_URL")


# ---------- DB CONNECTION ----------
def get_db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL not set in Render")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    return conn, cursor


# ---------- INIT DATABASE (MANUAL USE ONLY) ----------
def init_db():
    conn, cursor = get_db()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dictionary (
        word TEXT PRIMARY KEY,
        meaning TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id SERIAL PRIMARY KEY,
        username TEXT,
        word TEXT,
        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# ---------- RUN THIS ONCE IN BROWSER ----------
@app.route("/init")
def initialize():
    try:
        init_db()
        return "Database initialized ✅"
    except Exception as e:
        return f"Error: {e}"


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- REGISTER ----------

         @app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]

            conn, cursor = get_db()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
            conn.close()

            return "REGISTER SUCCESS ✅"

        except Exception as e:
            return f"REGISTER ERROR: {e}"

    return render_template("register.html")


# ---------- USER LOGIN ----------
@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn, cursor = get_db()

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/user_dashboard")

        return render_template("user_login.html", error="Invalid Credentials ❌")

    return render_template("user_login.html")


# ---------- USER DASHBOARD ----------
@app.route("/user_dashboard", methods=["GET", "POST"])
def user_dashboard():
    if "user" not in session:
        return redirect("/user_login")

    meaning = None
    conn, cursor = get_db()

    if request.method == "POST":
        word = request.form["word"].lower()

        cursor.execute(
            "SELECT meaning FROM dictionary WHERE word=%s",
            (word,)
        )
        result = cursor.fetchone()

        meaning = result[0] if result else "Word not found ❌"

        cursor.execute(
            "INSERT INTO history (username, word) VALUES (%s, %s)",
            (session["user"], word)
        )
        conn.commit()

    cursor.execute("""
        SELECT word, searched_at
        FROM history
        WHERE username=%s
        ORDER BY id DESC
        LIMIT 5
    """, (session["user"],))

    history = cursor.fetchall()
    conn.close()

    return render_template("user_dashboard.html", meaning=meaning, history=history)


# ---------- ADMIN LOGIN ----------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin_dashboard")

        return render_template("admin_login.html", error="Access Denied ❌")

    return render_template("admin_login.html")


# ---------- ADMIN DASHBOARD ----------
@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin_login")

    conn, cursor = get_db()

    if request.method == "POST":
        word = request.form["word"].lower()
        meaning = request.form["meaning"]

        try:
            cursor.execute(
                "INSERT INTO dictionary (word, meaning) VALUES (%s, %s)",
                (word, meaning)
            )
            conn.commit()
        except:
            pass

    cursor.execute("SELECT COUNT(*) FROM dictionary")
    total_words = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM history")
    total_searches = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM dictionary")
    words = cursor.fetchall()

    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()

    cursor.execute("""
        SELECT username, word, searched_at
        FROM history
        ORDER BY id DESC
    """)
    history = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        words=words,
        users=users,
        history=history,
        total_words=total_words,
        total_users=total_users,
        total_searches=total_searches
    )


# ---------- DELETE ----------
@app.route("/delete/<word>")
def delete_word(word):
    if "admin" not in session:
        return redirect("/admin_login")

    conn, cursor = get_db()
    cursor.execute("DELETE FROM dictionary WHERE word=%s", (word,))
    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")


# ---------- EDIT ----------
@app.route("/edit/<word>", methods=["GET", "POST"])
def edit_word(word):
    if "admin" not in session:
        return redirect("/admin_login")

    conn, cursor = get_db()

    if request.method == "POST":
        meaning = request.form["meaning"]

        cursor.execute(
            "UPDATE dictionary SET meaning=%s WHERE word=%s",
            (meaning, word)
        )
        conn.commit()
        conn.close()
        return redirect("/admin_dashboard")

    cursor.execute("SELECT * FROM dictionary WHERE word=%s", (word,))
    data = cursor.fetchone()
    conn.close()

    return render_template("edit.html", data=data)


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
