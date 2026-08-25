```javascript
/* =========================================================
   YASHWAY PROVIDER NOTIFICATION SYSTEM
   ========================================================= */

let knownBookingIds = new Set();
let firstCheck = true;
let audioContext = null;


/* =========================================================
   AUDIO SETUP
   ========================================================= */

function prepareAudio() {

    try {

        if (!audioContext) {

            audioContext = new (
                window.AudioContext ||
                window.webkitAudioContext
            )();

        }

        if (audioContext.state === "suspended") {

            audioContext.resume();

        }

    } catch (error) {

        console.log("Audio context error:", error);

    }

}


/* =========================================================
   UPDATE NOTIFICATION STATUS
   ========================================================= */

function updateNotificationStatus() {

    const status =
        document.getElementById("notification-status");

    const button =
        document.getElementById("enable-notifications");


    if (!status || !button) {
        return;
    }


    if (!("Notification" in window)) {

        status.textContent =
            "❌ या browser मध्ये notifications support नाही.";

        button.style.display = "none";

        return;

    }


    if (Notification.permission === "granted") {

        status.textContent =
            "✅ Notifications चालू आहेत.";

        button.textContent =
            "✅ Notifications Enabled";

        button.disabled = true;

    }

    else if (Notification.permission === "denied") {

        status.textContent =
            "❌ Notifications Block आहेत. Browser settings मधून Allow करा.";

        button.disabled = false;

    }

    else {

        status.textContent =
            "⚠️ Notifications अजून Enable केलेले नाहीत.";

        button.disabled = false;

    }

}


/* =========================================================
   ENABLE NOTIFICATIONS
   ========================================================= */

async function enableNotifications() {

    const status =
        document.getElementById("notification-status");

    const button =
        document.getElementById("enable-notifications");


    prepareAudio();


    if (!("Notification" in window)) {

        if (status) {

            status.textContent =
                "❌ Browser notifications support करत नाही.";

        }

        return;

    }


    try {

        let permission =
            Notification.permission;


        if (permission !== "granted") {

            permission =
                await Notification.requestPermission();

        }


        if (permission === "granted") {

            updateNotificationStatus();


            /*
             Test notification
            */

            new Notification(
                "YASHWAY 🔔",
                {
                    body:
                        "Booking notifications चालू झाले आहेत."
                }
            );


            /*
             Test sound
            */

            playNotificationSound();


            /*
             Immediately check bookings
            */

            checkProviderBookings();

        }

        else if (permission === "denied") {

            if (status) {

                status.textContent =
                    "❌ Notifications blocked आहेत. Browser settings मधून Allow करा.";

            }

        }

        else {

            if (status) {

                status.textContent =
                    "⚠️ Notification permission दिलेली नाही.";

            }

        }

    }

    catch (error) {

        console.error(
            "Notification error:",
            error
        );


        if (status) {

            status.textContent =
                "❌ Notification enable करता आले नाही.";

        }

    }

}


/* =========================================================
   SHOW PROVIDER NOTIFICATION
   ========================================================= */

function showProviderNotification(
    title,
    message
) {

    if (!("Notification" in window)) {
        return;
    }


    if (Notification.permission !== "granted") {
        return;
    }


    try {

        const notification =
            new Notification(
                title,
                {
                    body: message,
                    icon: "/static/images/logo.png",
                    tag: "yashway-booking"
                }
            );


        /*
         Notification वर click केल्यावर
         provider dashboard focus करा.
        */

        notification.onclick = function () {

            window.focus();

            notification.close();

        };


    } catch (error) {

        console.log(
            "Notification error:",
            error
        );

    }


    /*
     🔊 Sound
    */

    playNotificationSound();

}


/* =========================================================
   NOTIFICATION SOUND
   ========================================================= */

function playNotificationSound() {

    try {

        prepareAudio();


        if (!audioContext) {
            return;
        }


        const oscillator =
            audioContext.createOscillator();


        const gainNode =
            audioContext.createGain();


        oscillator.connect(gainNode);

        gainNode.connect(
            audioContext.destination
        );


        oscillator.type = "sine";


        oscillator.frequency.setValueAtTime(
            880,
            audioContext.currentTime
        );


        gainNode.gain.setValueAtTime(
            0.25,
            audioContext.currentTime
        );


        oscillator.start();


        oscillator.stop(
            audioContext.currentTime + 0.35
        );


    } catch (error) {

        console.log(
            "Sound unavailable:",
            error
        );

    }

}


/* =========================================================
   ADD NEW BOOKING TO DASHBOARD
   ========================================================= */

function addNewBookingCard(booking) {

    const container =
        document.getElementById(
            "bookings-container"
        );


    if (!container) {
        return;
    }


    /*
     "No bookings yet" remove करा
    */

    const noBooking =
        container.querySelector(
            ".no-booking"
        );


    if (noBooking) {

        noBooking.remove();

    }


    /*
     Duplicate booking card तयार होऊ देऊ नका
    */

    if (
        container.querySelector(
            `[data-booking-id="${booking.id}"]`
        )
    ) {

        return;

    }


    const card =
        document.createElement("div");


    card.className =
        "admin-booking-card";


    card.dataset.bookingId =
        booking.id;


    card.innerHTML = `

        <div class="booking-header">

            <h3>
                Booking #YWS-${String(
                    booking.id
                ).padStart(4, "0")}
            </h3>

            <span class="status">
                ${booking.status || "Pending"}
            </span>

        </div>


        <div class="booking-details">

            <p>
                <strong>Customer:</strong>
                ${booking.name || ""}
            </p>

            <p>
                <strong>Mobile:</strong>
                ${booking.mobile || ""}
            </p>

            <p>
                <strong>Service:</strong>
                ${booking.service || ""}
            </p>

            <p>
                <strong>Location:</strong>
                ${booking.location || ""}
            </p>

            <p>
                <strong>Date:</strong>
                ${booking.date || ""}
            </p>

            <p>
                <strong>Time:</strong>
                ${booking.time || ""}
            </p>

            ${
                booking.cost
                ? `
                    <p>
                        <strong>Cost:</strong>
                        ₹${booking.cost}
                    </p>
                  `
                : ""
            }

        </div>


        <div class="provider-assign">

            <form
                method="POST"
                action="/provider/accept/${booking.id}"
                style="
                    display:inline-block;
                    margin-bottom:10px;
                "
            >

                <button
                    type="submit"
                    class="btn primary"
                    style="
                        background:#2563eb;
                        color:white;
                        padding:12px 24px;
                        border:none;
                        border-radius:8px;
                        cursor:pointer;
                    "
                >

                    ✅ Accept Booking

                </button>

            </form>


            <form
                method="POST"
                action="/provider/reject/${booking.id}"
                onsubmit="
                    return confirm(
                        'ही booking reject करायची आहे का?'
                    );
                "
                style="
                    display:inline-block;
                    margin-left:10px;
                    margin-bottom:10px;
                "
            >

                <button
                    type="submit"
                    style="
                        background:#dc2626;
                        color:white;
                        padding:12px 24px;
                        border:none;
                        border-radius:8px;
                        cursor:pointer;
                    "
                >

                    ❌ Reject Booking

                </button>

            </form>

        </div>

    `;


    /*
     नवीन booking वरती दाखवा
    */

    container.prepend(card);

}


/* =========================================================
   CHECK PROVIDER BOOKINGS
   ========================================================= */

async function checkProviderBookings() {

    try {

        const response =
            await fetch(
                "/provider/notifications",
                {
                    method: "GET",
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            console.log(
                "Notification API error:",
                response.status
            );

            return;

        }


        const data =
            await response.json();


        if (
            !data.success ||
            !Array.isArray(data.bookings)
        ) {

            return;

        }


        data.bookings.forEach(
            function (booking) {

                const bookingId =
                    String(booking.id);


                /*
                 पहिल्या check मध्ये
                 जुन्या booking साठी notification नको.
                */

                if (firstCheck) {

                    knownBookingIds.add(
                        bookingId
                    );

                    return;

                }


                /*
                 नवीन booking
                */

                if (
                    !knownBookingIds.has(
                        bookingId
                    )
                ) {

                    knownBookingIds.add(
                        bookingId
                    );


                    /*
                     🔔 Notification
                    */

                    showProviderNotification(

                        "🔔 YASHWAY - New Booking",

                        "Booking #YWS-" +
                        bookingId.padStart(
                            4,
                            "0"
                        ) +

                        "\nCustomer: " +
                        (booking.name || "") +

                        "\nService: " +
                        (booking.service || "") +

                        "\nLocation: " +
                        (booking.location || "") +

                        "\nDate: " +
                        (booking.date || "") +

                        "\nTime: " +
                        (booking.time || "")

                    );


                    /*
                     Dashboard वर booking दाखवा
                    */

                    addNewBookingCard(
                        booking
                    );

                }

            }
        );


        firstCheck = false;


    } catch (error) {

        console.log(
            "Booking check error:",
            error
        );

    }

}


/* =========================================================
   PAGE LOAD
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {


        /*
         Notification permission status
        */

        updateNotificationStatus();


        /*
         First booking check
        */

        checkProviderBookings();


        /*
         प्रत्येक 5 seconds ला check
        */

        setInterval(
            checkProviderBookings,
            5000
        );


        /*
         User ने page वर click केल्यावर
         audio तयार/enable करा.
        */

        document.addEventListener(
            "click",
            function () {

                prepareAudio();

            },
            {
                once: true
            }
        );

    }
);
```
