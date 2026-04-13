from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"


# ---------- DB CONNECTION ----------
def get_db():
    conn = sqlite3.connect("database.db")
    return conn, conn.cursor()


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn, cursor = get_db()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect("/user_login")
        except:
            conn.close()
            return render_template("register.html", error="User already exists ❌")

    return render_template("register.html")


# ---------- USER LOGIN ----------
@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn, cursor = get_db()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/user_dashboard")
        else:
            return render_template("user_login.html", error="Invalid Credentials ❌")

    return render_template("user_login.html")


# ---------- USER DASHBOARD ----------
@app.route("/user_dashboard", methods=["GET", "POST"])
def user_dashboard():
    if "user" not in session:
        return redirect("/user_login")

    meaning = None

    conn, cursor = get_db()

    # SEARCH + SAVE HISTORY
    if request.method == "POST":
        word = request.form["word"].lower()

        cursor.execute("SELECT meaning FROM dictionary WHERE word=?", (word,))
        result = cursor.fetchone()

        if result:
            meaning = result[0]
        else:
            meaning = "Word not found ❌"

        # 🔥 FIXED HISTORY SAVE
        cursor.execute(
            "INSERT INTO history (username, word) VALUES (?, ?)",
            (session["user"], word)
        )
        conn.commit()

    # 🔥 FETCH USER HISTORY
    cursor.execute(
        "SELECT word, searched_at FROM history WHERE username=? ORDER BY searched_at DESC LIMIT 5",
        (session["user"],)
    )
    history = cursor.fetchall()

    conn.close()

    return render_template(
        "user_dashboard.html",
        meaning=meaning,
        history=history
    )


# ---------- ADMIN LOGIN ----------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = "admin"
            return redirect("/admin_dashboard")
        else:
            return render_template("admin_login.html", error="Access Denied ❌")

    return render_template("admin_login.html")


# ---------- ADMIN DASHBOARD ----------
@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin_login")

    conn, cursor = get_db()

    # ADD WORD
    if request.method == "POST":
        word = request.form["word"].lower()
        meaning = request.form["meaning"]

        cursor.execute(
            "INSERT OR IGNORE INTO dictionary (word, meaning) VALUES (?, ?)",
            (word, meaning)
        )
        conn.commit()

    # ---------- STATS ----------
    cursor.execute("SELECT COUNT(*) FROM dictionary")
    total_words = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM history")
    total_searches = cursor.fetchone()[0]

    # ---------- DATA ----------
    cursor.execute("SELECT * FROM dictionary")
    words = cursor.fetchall()

    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()

    # 🔥 FIXED HISTORY FETCH
    cursor.execute(
        "SELECT username, word, searched_at FROM history ORDER BY searched_at DESC"
    )
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


# ---------- DELETE WORD ----------
@app.route("/delete/<word>")
def delete_word(word):
    if "admin" not in session:
        return redirect("/admin_login")

    conn, cursor = get_db()
    cursor.execute("DELETE FROM dictionary WHERE word=?", (word,))
    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")


# ---------- EDIT WORD ----------
@app.route("/edit/<word>", methods=["GET", "POST"])
def edit_word(word):
    if "admin" not in session:
        return redirect("/admin_login")

    conn, cursor = get_db()

    if request.method == "POST":
        new_meaning = request.form["meaning"]

        cursor.execute(
            "UPDATE dictionary SET meaning=? WHERE word=?",
            (new_meaning, word)
        )
        conn.commit()
        conn.close()

        return redirect("/admin_dashboard")

    cursor.execute("SELECT * FROM dictionary WHERE word=?", (word,))
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
    app.run(debug=True)