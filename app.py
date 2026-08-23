from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "database.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# CREATE DATABASE
# =========================================================

def init_db():

    conn = get_db_connection()

    # -------------------------
    # BOOKINGS TABLE
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            service TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            provider TEXT DEFAULT '',
            cost REAL DEFAULT 0,
            commission REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )
    """)

    # -------------------------
    # PROVIDERS TABLE
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            service TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT DEFAULT 'Available',
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# SERVICES
# =========================================================

@app.route("/services")
def services():

    return render_template("services.html")


# =========================================================
# CUSTOMER BOOKING
# =========================================================

@app.route("/booking", methods=["GET", "POST"])
def booking():

    if request.method == "POST":

        name = request.form.get("name")
        mobile = request.form.get("mobile")
        service = request.form.get("service")
        location = request.form.get("location")
        date = request.form.get("date")
        time = request.form.get("time")

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conn = get_db_connection()

        # -------------------------
        # SAVE BOOKING
        # -------------------------

        cursor = conn.execute("""
            INSERT INTO bookings
            (
                name,
                mobile,
                service,
                location,
                date,
                time,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            mobile,
            service,
            location,
            date,
            time,
            created_at
        ))

        # Get newly created booking ID
        booking_id = cursor.lastrowid

        conn.commit()
        conn.close()

        # -------------------------
        # CREATE YASHWAY BOOKING ID
        # -------------------------

        booking_code = f"YWS-{booking_id:04d}"

        # -------------------------
        # SUCCESS PAGE
        # -------------------------

        return render_template(
            "booking_success.html",
            booking_id=booking_id,
            booking_code=booking_code,
            name=name,
            service=service,
            location=location,
            date=date,
            time=time
        )

    return render_template("booking.html")


# =========================================================
# TRACK BOOKING
# =========================================================

@app.route("/track", methods=["GET", "POST"])
def track():

    booking = None
    searched = False

    if request.method == "POST":

        booking_code = request.form.get(
            "booking_code",
            ""
        ).strip().upper()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        searched = True

        # -------------------------
        # CHECK BOOKING ID
        # -------------------------

        if booking_code.startswith("YWS-"):

            try:

                booking_id = int(
                    booking_code.replace(
                        "YWS-",
                        ""
                    )
                )

                conn = get_db_connection()

                booking = conn.execute("""
                    SELECT *
                    FROM bookings
                    WHERE id = ?
                    AND mobile = ?
                """, (
                    booking_id,
                    mobile
                )).fetchone()

                conn.close()

            except ValueError:

                booking = None

    return render_template(
        "track.html",
        booking=booking,
        searched=searched
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    conn = get_db_connection()

    # -------------------------
    # ALL BOOKINGS
    # -------------------------

    bookings = conn.execute("""
        SELECT *
        FROM bookings
        ORDER BY id DESC
    """).fetchall()

    # -------------------------
    # ALL PROVIDERS
    # -------------------------

    providers = conn.execute("""
        SELECT *
        FROM providers
        ORDER BY name ASC
    """).fetchall()

    # -------------------------
    # TOTAL BOOKINGS
    # -------------------------

    total = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
    """).fetchone()[0]

    # -------------------------
    # PENDING
    # -------------------------

    pending = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status = 'Pending'
    """).fetchone()[0]

    # -------------------------
    # COMPLETED
    # -------------------------

    completed = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status = 'Completed'
    """).fetchone()[0]

    # -------------------------
    # CANCELLED
    # -------------------------

    cancelled = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status = 'Cancelled'
    """).fetchone()[0]

    # -------------------------
    # TOTAL COMMISSION
    # -------------------------

    total_commission = conn.execute("""
        SELECT COALESCE(SUM(commission), 0)
        FROM bookings
        WHERE status = 'Completed'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        bookings=bookings,
        providers=providers,
        total=total,
        pending=pending,
        completed=completed,
        cancelled=cancelled,
        total_commission=total_commission
    )


# =========================================================
# ASSIGN PROVIDER
# =========================================================

@app.route(
    "/admin/assign-provider/<int:booking_id>",
    methods=["POST"]
)
def assign_provider(booking_id):

    provider_id = request.form.get(
        "provider_id"
    )

    conn = get_db_connection()

    # -------------------------
    # FIND PROVIDER
    # -------------------------

    provider = conn.execute("""
        SELECT *
        FROM providers
        WHERE id = ?
    """, (
        provider_id,
    )).fetchone()

    # -------------------------
    # ASSIGN PROVIDER
    # -------------------------

    if provider:

        conn.execute("""
            UPDATE bookings
            SET provider = ?
            WHERE id = ?
        """, (
            provider["name"],
            booking_id
        ))

        conn.commit()

    conn.close()

    return redirect("/admin")


# =========================================================
# UPDATE BOOKING
# =========================================================

@app.route(
    "/admin/update-booking/<int:booking_id>",
    methods=["POST"]
)
def update_booking(booking_id):

    cost = request.form.get(
        "cost",
        "0"
    )

    commission = request.form.get(
        "commission",
        "0"
    )

    status = request.form.get(
        "status",
        "Pending"
    )

    # -------------------------
    # CONVERT COST
    # -------------------------

    try:

        cost = float(cost)

    except (ValueError, TypeError):

        cost = 0


    # -------------------------
    # CONVERT COMMISSION
    # -------------------------

    try:

        commission = float(commission)

    except (ValueError, TypeError):

        commission = 0


    conn = get_db_connection()

    conn.execute("""
        UPDATE bookings

        SET
            cost = ?,
            commission = ?,
            status = ?

        WHERE id = ?
    """, (
        cost,
        commission,
        status,
        booking_id
    ))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================================================
# PROVIDER MANAGEMENT
# =========================================================

@app.route(
    "/admin/providers",
    methods=["GET", "POST"]
)
def providers():

    conn = get_db_connection()

    # -------------------------
    # ADD PROVIDER
    # -------------------------

    if request.method == "POST":

        name = request.form.get(
            "name"
        )

        mobile = request.form.get(
            "mobile"
        )

        service = request.form.get(
            "service"
        )

        location = request.form.get(
            "location"
        )

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conn.execute("""
            INSERT INTO providers
            (
                name,
                mobile,
                service,
                location,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            mobile,
            service,
            location,
            created_at
        ))

        conn.commit()

    # -------------------------
    # GET ALL PROVIDERS
    # -------------------------

    providers = conn.execute("""
        SELECT *
        FROM providers
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "providers.html",
        providers=providers
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)