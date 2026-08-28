from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# =========================================================
# APP CONFIG
# =========================================================
app.secret_key = os.environ.get("SECRET_KEY", "YASHWAY_CHANGE_THIS_SECRET_KEY")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "YASHWAY@123")
DATABASE_URL = os.environ.get("DATABASE_URL")

# =========================================================
# PWA FILES
# =========================================================
@app.route("/manifest.json")
def pwa_manifest():
    return send_from_directory(
        os.path.join(app.root_path, "static", "pwa"),
        "manifest.json",
        mimetype="application/manifest+json",
    )

@app.route("/service-worker.js")
def service_worker():
    response = send_from_directory(
        os.path.join(app.root_path, "static", "pwa"),
        "service-worker.js",
        mimetype="application/javascript",
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# Supports your existing static/js/sw.js too.
@app.route("/sw.js")
def sw_js():
    response = send_from_directory(
        os.path.join(app.root_path, "static", "js"),
        "sw.js",
        mimetype="application/javascript",
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# =========================================================
# DATABASE
# =========================================================
def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is missing.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                service TEXT NOT NULL,
                location TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                provider TEXT DEFAULT '',
                cost DOUBLE PRECISION DEFAULT 0,
                commission DOUBLE PRECISION DEFAULT 0,
                status TEXT DEFAULT 'Pending',
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                service TEXT NOT NULL,
                location TEXT NOT NULL,
                username TEXT,
                password TEXT,
                status TEXT DEFAULT 'Available',
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("ALTER TABLE providers ADD COLUMN IF NOT EXISTS username TEXT")
        cursor.execute("ALTER TABLE providers ADD COLUMN IF NOT EXISTS password TEXT")
        cursor.execute("ALTER TABLE providers ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Available'")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

try:
    init_db()
    print("DATABASE INITIALIZED SUCCESSFULLY")
except Exception as e:
    print("DATABASE INITIALIZATION ERROR:", e)

# =========================================================
# PUBLIC PAGES
# =========================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/services")
def services():
    return render_template("services.html")

# =========================================================
# CUSTOMER BOOKING
# =========================================================
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        service = request.form.get("service", "").strip()
        location = request.form.get("location", "").strip()
        date = request.form.get("date", "").strip()
        time = request.form.get("time", "").strip()

        if not all([name, mobile, service, location, date, time]):
            return render_template("booking.html", error="कृपया सर्व माहिती भरा.")

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO bookings
                (name, mobile, service, location, date, time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (name, mobile, service, location, date, time, created_at))
            booking_id = cursor.fetchone()["id"]
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

        booking_code = f"YWS-{booking_id:04d}"
        return render_template(
            "booking_success.html",
            booking_id=booking_id,
            booking_code=booking_code,
            name=name,
            service=service,
            location=location,
            date=date,
            time=time,
        )

    return render_template("booking.html")

# =========================================================
# CUSTOMER TRACKING
# =========================================================
@app.route("/track", methods=["GET", "POST"])
def track():
    booking = None
    searched = False

    if request.method == "POST":
        booking_code = request.form.get("booking_code", "").strip().upper()
        mobile = request.form.get("mobile", "").strip()
        searched = True

        if booking_code.startswith("YWS-"):
            try:
                booking_id = int(booking_code.replace("YWS-", ""))
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        SELECT * FROM bookings
                        WHERE id = %s AND mobile = %s
                    """, (booking_id, mobile))
                    booking = cursor.fetchone()
                finally:
                    cursor.close()
                    conn.close()
            except ValueError:
                booking = None

    return render_template("track.html", booking=booking, searched=searched)

# =========================================================
# ADMIN LOGIN / LOGOUT
# =========================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect("/admin")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin")

        return render_template(
            "admin_login.html",
            error="Username किंवा Password चुकीचा आहे.",
        )

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")

# =========================================================
# ADMIN DASHBOARD
# =========================================================
@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
        bookings = cursor.fetchall()

        cursor.execute("SELECT * FROM providers ORDER BY name ASC")
        providers = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total FROM bookings")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS pending FROM bookings WHERE status = 'Pending'")
        pending = cursor.fetchone()["pending"]

        cursor.execute("SELECT COUNT(*) AS completed FROM bookings WHERE status = 'Completed'")
        completed = cursor.fetchone()["completed"]

        cursor.execute("SELECT COUNT(*) AS cancelled FROM bookings WHERE status = 'Cancelled'")
        cancelled = cursor.fetchone()["cancelled"]

        cursor.execute("""
            SELECT COALESCE(SUM(commission), 0) AS total_commission
            FROM bookings WHERE status = 'Completed'
        """)
        total_commission = cursor.fetchone()["total_commission"]
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "admin.html",
        bookings=bookings,
        providers=providers,
        total=total,
        pending=pending,
        completed=completed,
        cancelled=cancelled,
        total_commission=total_commission,
    )

# =========================================================
# ADMIN ASSIGN PROVIDER
# =========================================================
@app.route("/admin/assign-provider/<int:booking_id>", methods=["POST"])
def assign_provider(booking_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    provider_id = request.form.get("provider_id")
    if not provider_id:
        return redirect("/admin")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM providers WHERE id = %s", (provider_id,))
        provider = cursor.fetchone()
        if provider:
            cursor.execute("""
                UPDATE bookings
                SET provider = %s, status = 'Pending'
                WHERE id = %s
            """, (provider["name"], booking_id))
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect("/admin")

# =========================================================
# ADMIN UPDATE BOOKING
# =========================================================
@app.route("/admin/update-booking/<int:booking_id>", methods=["POST"])
def update_booking(booking_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    try:
        cost = float(request.form.get("cost", "0"))
    except (ValueError, TypeError):
        cost = 0

    try:
        commission = float(request.form.get("commission", "0"))
    except (ValueError, TypeError):
        commission = 0

    status = request.form.get("status", "Pending")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE bookings
            SET cost = %s, commission = %s, status = %s
            WHERE id = %s
        """, (cost, commission, status, booking_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect("/admin")

# =========================================================
# PROVIDER MANAGEMENT
# =========================================================
@app.route("/admin/providers", methods=["GET", "POST"])
def providers():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            mobile = request.form.get("mobile", "").strip()
            service = request.form.get("service", "").strip()
            location = request.form.get("location", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if all([name, mobile, service, location]):
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO providers
                    (name, mobile, service, location, username, password, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, mobile, service, location,
                    username, password, "Available", created_at
                ))
                conn.commit()

        cursor.execute("SELECT * FROM providers ORDER BY id DESC")
        providers_list = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template("providers.html", providers=providers_list)

@app.route("/admin/delete-provider/<int:provider_id>", methods=["POST"])
def delete_provider(provider_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM providers WHERE id = %s", (provider_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect("/admin/providers")

# =========================================================
# PROVIDER LOGIN
# =========================================================
@app.route("/provider/login", methods=["GET", "POST"])
def provider_login():
    if session.get("provider_logged_in"):
        return redirect("/provider/dashboard")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template(
                "provider_login.html",
                error="Username आणि Password भरा.",
            )

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM providers
                WHERE username = %s AND password = %s
            """, (username, password))
            provider = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if provider:
            session["provider_logged_in"] = True
            session["provider_id"] = provider["id"]
            session["provider_name"] = provider["name"]
            return redirect("/provider/dashboard")

        return render_template(
            "provider_login.html",
            error="Username किंवा Password चुकीचा आहे.",
        )

    return render_template("provider_login.html")

# =========================================================
# PROVIDER NOTIFICATIONS
# =========================================================
@app.route("/provider/notifications", methods=["GET"])
def provider_notifications():
    if not session.get("provider_logged_in"):
        return {"success": False, "error": "Unauthorized"}, 401

    provider_id = session.get("provider_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, name, mobile, service, location, status
            FROM providers WHERE id = %s
        """, (provider_id,))
        provider = cursor.fetchone()

        if not provider:
            return {"success": False, "error": "Provider not found"}, 404

        cursor.execute("""
            SELECT id, name, mobile, service, location, date, time,
                   provider, cost, status, created_at
            FROM bookings
            WHERE provider = %s AND status = 'Pending'
            ORDER BY id DESC
        """, (provider["name"],))
        bookings = cursor.fetchall()

        return {
            "success": True,
            "provider": {"id": provider["id"], "name": provider["name"]},
            "bookings": bookings,
        }
    except Exception as e:
        print("PROVIDER NOTIFICATION ERROR:", e)
        return {"success": False, "error": "Notification server error"}, 500
    finally:
        cursor.close()
        conn.close()

# =========================================================
# PROVIDER DASHBOARD
# =========================================================
@app.route("/provider/dashboard")
def provider_dashboard():
    if not session.get("provider_logged_in"):
        return redirect("/provider/login")

    provider_id = session.get("provider_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM providers WHERE id = %s", (provider_id,))
        provider = cursor.fetchone()

        if not provider:
            session.clear()
            return redirect("/provider/login")

        cursor.execute("""
            SELECT * FROM bookings
            WHERE provider = %s
            ORDER BY id DESC
        """, (provider["name"],))
        bookings = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "provider_dashboard.html",
        provider=provider,
        bookings=bookings,
    )

# =========================================================
# PROVIDER ACCEPT
# =========================================================
@app.route("/provider/accept/<int:booking_id>", methods=["POST"])
def provider_accept_booking(booking_id):
    if not session.get("provider_logged_in"):
        return redirect("/provider/login")

    provider_id = session.get("provider_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM providers WHERE id = %s", (provider_id,))
        provider = cursor.fetchone()
        if provider:
            cursor.execute("""
                UPDATE bookings SET status = 'Accepted'
                WHERE id = %s AND provider = %s AND status = 'Pending'
            """, (booking_id, provider["name"]))
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect("/provider/dashboard")

# =========================================================
# PROVIDER REJECT
# =========================================================
@app.route("/provider/reject/<int:booking_id>", methods=["POST"])
def provider_reject_booking(booking_id):
    if not session.get("provider_logged_in"):
        return redirect("/provider/login")

    provider_id = session.get("provider_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM providers WHERE id = %s", (provider_id,))
        provider = cursor.fetchone()
        if provider:
            cursor.execute("""
                UPDATE bookings SET status = 'Rejected'
                WHERE id = %s AND provider = %s AND status = 'Pending'
            """, (booking_id, provider["name"]))
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect("/provider/dashboard")

# =========================================================
# PROVIDER COMPLETE
# =========================================================
@app.route("/provider/complete/<int:booking_id>", methods=["POST"])
def provider_complete_booking(booking_id):
    if not session.get("provider_logged_in"):
        return redirect("/provider/login")

    provider_id = session.get("provider_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM providers WHERE id = %s", (provider_id,))
        provider = cursor.fetchone()
        if provider:
            cursor.execute("""
                UPDATE bookings SET status = 'Completed'
                WHERE id = %s AND provider = %s AND status = 'Accepted'
            """, (booking_id, provider["name"]))
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect("/provider/dashboard")

# =========================================================
# PROVIDER LOGOUT
# =========================================================
@app.route("/provider/logout")
def provider_logout():
    session.pop("provider_logged_in", None)
    session.pop("provider_id", None)
    session.pop("provider_name", None)
    return redirect("/provider/login")

# =========================================================
# START SERVER
# =========================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )
