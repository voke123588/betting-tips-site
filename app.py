from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"   # change later

# ---------- ADMIN LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # your admin credentials
        if username == "admin" and password == "1234":
            session["admin"] = True
            return redirect("/admin")

    return render_template("login.html")

# ---------- ADMIN LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")

# ---------- HOMEPAGE ----------
@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    # show only Free tips
    tips = conn.execute("SELECT * FROM tips WHERE category='Free'").fetchall()
    conn.close()
    return render_template("index.html", tips=tips)

# ---------- ADD TIP ----------
@app.route("/add", methods=["POST"])
def add():
    if "admin" not in session:
        return redirect("/login")

    match = request.form["match"]
    prediction = request.form["prediction"]
    odds = request.form["odds"]
    category = request.form["category"]

    conn = sqlite3.connect("database.db")
    conn.execute(
        "INSERT INTO tips (match, prediction, odds, category) VALUES (?, ?, ?, ?)",
        (match, prediction, odds, category)
    )
    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------- EDIT TIP ----------
@app.route("/edit/<int:id>")
def edit(id):
    if "admin" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database.db")
    tip = conn.execute("SELECT * FROM tips WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("edit.html", tip=tip)

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    if "admin" not in session:
        return redirect("/login")
    match = request.form["match"]
    prediction = request.form["prediction"]
    odds = request.form["odds"]
    category = request.form["category"]

    conn = sqlite3.connect("database.db")
    conn.execute(
        "UPDATE tips SET match=?, prediction=?, odds=?, category=? WHERE id=?",
        (match, prediction, odds, category, id)
    )
    conn.commit()
    conn.close()
    return redirect("/admin")

# ---------- DELETE TIP ----------
@app.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    conn.execute("DELETE FROM tips WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------- VIP REGISTRATION ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        try:
            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
        except:
            conn.close()
            return "Email or Username already exists!"
        conn.close()
        return redirect("/vip_login")
    return render_template("register.html")

# ---------- VIP LOGIN ----------
@app.route("/vip_login", methods=["GET", "POST"])
def vip_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            return redirect("/vip")
        return "Invalid credentials or you are not paid!"

    return render_template("vip_login.html")

# ---------- VIP PAGE WITH EXPIRY CHECK ----------
@app.route("/vip")
def vip():
    if "user_id" not in session:
        return redirect("/vip_login")

    conn = sqlite3.connect("database.db")
    user = conn.execute("SELECT paid_status, vip_expiry FROM users WHERE id=?", (session["user_id"],)).fetchone()

    # Check if user is paid and VIP is not expired
    paid_status, vip_expiry = user
    if paid_status != "Yes":
        conn.close()
        return "You must pay to access VIP tips!"
    if vip_expiry:
        expiry_date = datetime.strptime(vip_expiry, "%Y-%m-%d")
        if expiry_date < datetime.now():
            conn.close()
            return "Your VIP subscription has expired!"

    vip_tips = conn.execute("SELECT * FROM tips WHERE category='VIP'").fetchall()
    conn.close()
    return render_template("vip.html", tips=vip_tips)

# ---------- VIP LOGOUT ----------
@app.route("/vip_logout")
def vip_logout():
    session.pop("user_id", None)
    return redirect("/vip_login")

# ---------- ADMIN PANEL (Tips + Users) ----------
@app.route("/admin")
def admin_panel():
    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    tips = conn.execute("SELECT * FROM tips").fetchall()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("admin.html", tips=tips, users=users)

# ---------- MARK USER AS PAID ----------
@app.route("/mark_paid/<int:id>")
def mark_paid(id):
    if "admin" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database.db")
    conn.execute("UPDATE users SET paid_status='Yes', vip_expiry=date('now','+30 day') WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ---------- REVOKE VIP ACCESS ----------
@app.route("/revoke/<int:id>")
def revoke(id):
    if "admin" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database.db")
    conn.execute("UPDATE users SET paid_status='No', vip_expiry=NULL WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ---------- RUN APP ----------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # use Render's assigned port
    app.run(host="0.0.0.0", port=port, debug=True)