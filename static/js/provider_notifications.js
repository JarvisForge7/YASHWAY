/* =========================================================
   YASHWAY PROVIDER NOTIFICATION SYSTEM
   ========================================================= */

"use strict";


let knownBookingIds = new Set();

let firstCheck = true;

let audioContext = null;

let checkingBookings = false;



/* =========================================================
   AUDIO
========================================================= */

function prepareAudio() {

    try {

        if (!audioContext) {

            const AudioContext =
                window.AudioContext ||
                window.webkitAudioContext;

            if (!AudioContext) {

                console.log(
                    "AudioContext not supported"
                );

                return;

            }

            audioContext =
                new AudioContext();

        }


        if (
            audioContext.state === "suspended"
        ) {

            audioContext.resume();

        }

    }

    catch (error) {

        console.error(
            "Audio context error:",
            error
        );

    }

}



/* =========================================================
   SOUND
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


        oscillator.connect(
            gainNode
        );


        gainNode.connect(
            audioContext.destination
        );


        oscillator.type =
            "sine";


        const now =
            audioContext.currentTime;


        oscillator.frequency.setValueAtTime(
            880,
            now
        );


        oscillator.frequency.setValueAtTime(
            660,
            now + 0.18
        );


        gainNode.gain.setValueAtTime(
            0.001,
            now
        );


        gainNode.gain.exponentialRampToValueAtTime(
            0.25,
            now + 0.03
        );


        gainNode.gain.exponentialRampToValueAtTime(
            0.001,
            now + 0.5
        );


        oscillator.start(now);


        oscillator.stop(
            now + 0.5
        );

    }

    catch (error) {

        console.error(
            "Sound error:",
            error
        );

    }

}



/* =========================================================
   STATUS
========================================================= */

function updateNotificationStatus() {

    const status =
        document.getElementById(
            "notification-status"
        );


    const button =
        document.getElementById(
            "enable-notifications"
        );


    if (!status || !button) {

        return;

    }


    if (
        !("Notification" in window)
    ) {

        status.textContent =
            "❌ या browser मध्ये notifications support नाही.";

        button.style.display =
            "none";

        return;

    }


    if (
        Notification.permission ===
        "granted"
    ) {

        status.textContent =
            "✅ Notifications चालू आहेत.";

        button.textContent =
            "✅ Notifications Enabled";

        button.disabled =
            true;

        button.style.opacity =
            "0.7";

    }

    else if (
        Notification.permission ===
        "denied"
    ) {

        status.textContent =
            "❌ Notifications Block आहेत. Browser settings मधून Allow करा.";

        button.textContent =
            "🔔 Enable Notifications";

        button.disabled =
            false;

    }

    else {

        status.textContent =
            "⚠️ Notifications अजून Enable केलेले नाहीत.";

        button.textContent =
            "🔔 Enable Notifications";

        button.disabled =
            false;

    }

}



/* =========================================================
   ENABLE NOTIFICATIONS
========================================================= */

async function enableNotifications() {

    const status =
        document.getElementById(
            "notification-status"
        );


    const button =
        document.getElementById(
            "enable-notifications"
        );


    prepareAudio();


    if (
        !("Notification" in window)
    ) {

        if (status) {

            status.textContent =
                "❌ Browser notifications support करत नाही.";

        }

        return;

    }


    try {

        let permission =
            Notification.permission;


        if (
            permission !== "granted"
        ) {

            permission =
                await Notification.requestPermission();

        }


        if (
            permission === "granted"
        ) {

            updateNotificationStatus();


            /* TEST NOTIFICATION */

            const testNotification =
                new Notification(
                    "YASHWAY 🔔",
                    {
                        body:
                            "Booking notifications चालू झाले आहेत."
                    }
                );


            testNotification.onclick =
                function () {

                    window.focus();

                    testNotification.close();

                };


            /* TEST SOUND */

            playNotificationSound();


            /*
             IMPORTANT:
             Permission मिळाल्यानंतर
             current bookings पुन्हा check करू.
            */

            firstCheck = true;

            await checkProviderBookings();

        }

        else if (
            permission === "denied"
        ) {

            if (status) {

                status.textContent =
                    "❌ Notifications blocked आहेत. Chrome Site Settings मधून Allow करा.";

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
            "Notification permission error:",
            error
        );


        if (status) {

            status.textContent =
                "❌ Notification enable करता आले नाही.";

        }

    }

}



/* =========================================================
   SHOW NOTIFICATION
========================================================= */

function showProviderNotification(
    title,
    message
) {

    if (
        !("Notification" in window)
    ) {

        return;

    }


    if (
        Notification.permission !==
        "granted"
    ) {

        return;

    }


    try {

        const notification =
            new Notification(
                title,
                {
                    body: message,
                    tag:
                        "yashway-booking-" +
                        Date.now()
                }
            );


        notification.onclick =
            function () {

                window.focus();

                notification.close();

            };


    }

    catch (error) {

        console.error(
            "Notification error:",
            error
        );

    }


    playNotificationSound();

}



/* =========================================================
   ADD BOOKING CARD
========================================================= */

function addNewBookingCard(
    booking
) {

    const container =
        document.getElementById(
            "bookings-container"
        );


    if (!container) {

        return;

    }


    /* Remove no booking */

    const noBooking =
        container.querySelector(
            ".no-booking"
        );


    if (noBooking) {

        noBooking.remove();

    }


    /* Duplicate protection */

    const existing =
        container.querySelector(
            `[data-booking-id="${booking.id}"]`
        );


    if (existing) {

        return;

    }


    const card =
        document.createElement(
            "div"
        );


    card.className =
        "admin-booking-card";


    card.dataset.bookingId =
        booking.id;


    const bookingNumber =
        String(
            booking.id
        ).padStart(
            4,
            "0"
        );


    card.innerHTML = `

        <div class="booking-header">

            <h3>
                Booking #YWS-${bookingNumber}
            </h3>

            <span class="status">
                ${booking.status || "Pending"}
            </span>

        </div>


        <div class="booking-details">

            <p>
                <strong>Customer:</strong>
                ${escapeHtml(booking.name)}
            </p>

            <p>
                <strong>Mobile:</strong>
                ${escapeHtml(booking.mobile)}
            </p>

            <p>
                <strong>Service:</strong>
                ${escapeHtml(booking.service)}
            </p>

            <p>
                <strong>Location:</strong>
                ${escapeHtml(booking.location)}
            </p>

            <p>
                <strong>Date:</strong>
                ${escapeHtml(booking.date)}
            </p>

            <p>
                <strong>Time:</strong>
                ${escapeHtml(booking.time)}
            </p>

            ${
                booking.cost
                ? `
                    <p>
                        <strong>Cost:</strong>
                        ₹${escapeHtml(booking.cost)}
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
     नवीन booking वरती
    */

    container.prepend(
        card
    );

}



/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}



/* =========================================================
   CHECK PROVIDER BOOKINGS
========================================================= */

async function checkProviderBookings() {

    if (checkingBookings) {

        return;

    }


    checkingBookings = true;


    try {

        const response =
            await fetch(
                "/provider/notifications",
                {
                    method: "GET",
                    cache: "no-store",
                    credentials: "same-origin",
                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        if (
            !response.ok
        ) {

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
            !Array.isArray(
                data.bookings
            )
        ) {

            return;

        }


        data.bookings.forEach(
            function (booking) {

                const bookingId =
                    String(
                        booking.id
                    );


                /*
                 First check:
                 existing bookings save करा.
                */

                if (firstCheck) {

                    knownBookingIds.add(
                        bookingId
                    );

                    return;

                }


                /*
                 New booking
                */

                if (
                    !knownBookingIds.has(
                        bookingId
                    )
                ) {

                    knownBookingIds.add(
                        bookingId
                    );


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
                        (booking.location || "")

                    );


                    addNewBookingCard(
                        booking
                    );

                }

            }
        );


        firstCheck = false;

    }

    catch (error) {

        console.error(
            "Booking check error:",
            error
        );

    }

    finally {

        checkingBookings = false;

    }

}



/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "YASHWAY Provider Notification System Loaded"
        );


        /* Permission status */

        updateNotificationStatus();


        /* Button */

        const button =
            document.getElementById(
                "enable-notifications"
            );


        if (button) {

            button.addEventListener(
                "click",
                enableNotifications
            );

        }


        /*
         Browser मध्ये user interaction
         झाल्यावर audio unlock.
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


        /*
         First booking check
        */

        checkProviderBookings();


        /*
         प्रत्येक 5 seconds
        */

        setInterval(
            checkProviderBookings,
            5000
        );

    }
);