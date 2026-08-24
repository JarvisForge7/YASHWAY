from flask import Flask, render_template, request, redirect, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# =========================================================
# APP CONFIG
# =========================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "YASHWAY_CHANGE_THIS_SECRET_KEY"
)

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "YASHWAY@123"
)

DATABASE_URL = os.environ.get("DATABASE_URL")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is missing."
        )

    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )

    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db_connection()

    cursor = conn.cursor()

    # =====================================================
    # BOOKINGS TABLE
    # =====================================================

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

    # =====================================================
    # PROVIDERS TABLE
    # =====================================================

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

    # =====================================================
    # PROVIDER MIGRATION
    # =====================================================

    cursor.execute("""
        ALTER TABLE providers
        ADD COLUMN IF NOT EXISTS username TEXT
    """)

    cursor.execute("""
        ALTER TABLE providers
        ADD COLUMN IF NOT EXISTS password TEXT
    """)

    conn.commit()

    cursor.close()
    conn.close()


# =========================================================
# INITIALIZE DATABASE ON START
# =========================================================

try:

    init_db()

except Exception as e:

    print("DATABASE INITIALIZATION ERROR:", e)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# SERVICES
# =========================================================

@app.route("/services")
def services():

    return render_template(
        "services.html"
    )


# =========================================================
# CUSTOMER BOOKING
# =========================================================

@app.route(
    "/booking",
    methods=["GET", "POST"]
)
def booking():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        service = request.form.get(
            "service",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        date = request.form.get(
            "date",
            ""
        ).strip()

        time = request.form.get(
            "time",
            ""
        ).strip()

        # =================================================
        # VALIDATION
        # =================================================

        if not all([
            name,
            mobile,
            service,
            location,
            date,
            time
        ]):

            return render_template(
                "booking.html",
                error="कृपया सर्व माहिती भरा."
            )

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conn = get_db_connection()

        cursor = conn.cursor()

        # =================================================
        # SAVE BOOKING
        # =================================================

        cursor.execute("""
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

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )

            RETURNING id
        """, (
            name,
            mobile,
            service,
            location,
            date,
            time,
            created_at
        ))

        booking_id = cursor.fetchone()["id"]

        conn.commit()

        cursor.close()
        conn.close()

        # =================================================
        # YASHWAY BOOKING ID
        # =================================================

        booking_code = f"YWS-{booking_id:04d}"

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

    return render_template(
        "booking.html"
    )


# =========================================================
# TRACK BOOKING
# =========================================================

@app.route(
    "/track",
    methods=["GET", "POST"]
)
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

        if booking_code.startswith("YWS-"):

            try:

                booking_id = int(
                    booking_code.replace(
                        "YWS-",
                        ""
                    )
                )

                conn = get_db_connection()

                cursor = conn.cursor()

                cursor.execute("""
                    SELECT *
                    FROM bookings
                    WHERE id = %s
                    AND mobile = %s
                """, (
                    booking_id,
                    mobile
                ))

                booking = cursor.fetchone()

                cursor.close()
                conn.close()

            except ValueError:

                booking = None

    return render_template(
        "track.html",
        booking=booking,
        searched=searched
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if session.get(
        "admin_logged_in"
    ):

        return redirect(
            "/admin"
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session[
                "admin_logged_in"
            ] = True

            return redirect(
                "/admin"
            )

        return render_template(
            "admin_login.html",
            error="Username किंवा Password चुकीचा आहे."
        )

    return render_template(
        "admin_login.html"
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect(
        "/admin/login"
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            "/admin/login"
        )

    conn = get_db_connection()

    cursor = conn.cursor()

    # =====================================================
    # ALL BOOKINGS
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM bookings
        ORDER BY id DESC
    """)

    bookings = cursor.fetchall()

    # =====================================================
    # ALL PROVIDERS
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM providers
        ORDER BY name ASC
    """)

    providers = cursor.fetchall()

    # =====================================================
    # TOTAL
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM bookings
    """)

    total = cursor.fetchone()["count"]

    # =====================================================
    # PENDING
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status = 'Pending'
    """)

    pending = cursor.fetchone()["count"]

    # =====================================================
    # COMPLETED
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status = 'Completed'
    """)

    completed = cursor.fetchone()["count"]

    # =====================================================
    # CANCELLED
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status = 'Cancelled'
    """)

    cancelled = cursor.fetchone()["count"]

    # =====================================================
    # COMMISSION
    # =====================================================

    cursor.execute("""
        SELECT COALESCE(
            SUM(commission),
            0
        ) AS total_commission

        FROM bookings

        WHERE status = 'Completed'
    """)

    total_commission = cursor.fetchone()[
        "total_commission"
    ]

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
        total_commission=total_commission
    )


# =========================================================
# ASSIGN PROVIDER
# =========================================================

@app.route(
    "/admin/assign-provider/<int:booking_id>",
    methods=["POST"]
)
def assign_provider(
    booking_id
):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            "/admin/login"
        )

    provider_id = request.form.get(
        "provider_id"
    )

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM providers
        WHERE id = %s
    """, (
        provider_id,
    ))

    provider = cursor.fetchone()

    if provider:

        cursor.execute("""
            UPDATE bookings
            SET provider = %s
            WHERE id = %s
        """, (
            provider["name"],
            booking_id
        ))

        conn.commit()

    cursor.close()
    conn.close()

    return redirect(
        "/admin"
    )


# =========================================================
# UPDATE BOOKING
# =========================================================

@app.route(
    "/admin/update-booking/<int:booking_id>",
    methods=["POST"]
)
def update_booking(
    booking_id
):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            "/admin/login"
        )

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

    try:

        cost = float(cost)

    except (
        ValueError,
        TypeError
    ):

        cost = 0

    try:

        commission = float(
            commission
        )

    except (
        ValueError,
        TypeError
    ):

        commission = 0

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bookings

        SET
            cost = %s,
            commission = %s,
            status = %s

        WHERE id = %s
    """, (
        cost,
        commission,
        status,
        booking_id
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(
        "/admin"
    )


# =========================================================
# PROVIDER MANAGEMENT
# =========================================================

@app.route(
    "/admin/providers",
    methods=["GET", "POST"]
)
def providers():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            "/admin/login"
        )

    conn = get_db_connection()

    cursor = conn.cursor()

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        service = request.form.get(
            "service",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO providers
            (
                name,
                mobile,
                service,
                location,
                username,
                password,
                created_at
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            name,
            mobile,
            service,
            location,
            username,
            password,
            created_at
        ))

        conn.commit()

    cursor.execute("""
        SELECT *
        FROM providers
        ORDER BY id DESC
    """)

    providers_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "providers.html",
        providers=providers_list
    )
```python
# =========================================================
# DELETE PROVIDER
# =========================================================

@app.route(
    "/admin/delete-provider/<int:provider_id>",
    methods=["POST"]
)
def delete_provider(provider_id):

    # Login protection
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()

    # Delete provider
    conn.execute("""
        DELETE FROM providers
        WHERE id = ?
    """, (
        provider_id,
    ))

    conn.commit()
    conn.close()

    return redirect("/admin/providers")
```



# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )