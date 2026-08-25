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

        console.log(
            "Audio context error:",
            error
        );

    }

}


/* =========================================================
   UPDATE NOTIFICATION STATUS
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


    if (!("Notification" in window)) {

        status.textContent =
            "❌ या browser मध्ये notifications support नाही.";

        button.style.display = "none";

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

        button.disabled = true;

    }

    else if (
        Notification.permission ===
        "denied"
    ) {

        status.textContent =
            "❌ Notifications Block आहेत. Browser settings मधून Allow करा.";

        button.textContent =
            "🔔 Enable Notifications";

        button.disabled = false;

    }

    else {

        status.textContent =
            "⚠️ Notifications अजून Enable केलेले नाहीत.";

        button.textContent =
            "🔔 Enable Notifications";

        button.disabled = false;

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


        /*
         Browser ने आधी permission दिलेली नसेल
         तर permission मागा.
        */

        if (
            permission !==
            "granted"
        ) {

            permission =
                await Notification.requestPermission();

        }


        /*
         Permission GRANTED
        */

        if (
            permission ===
            "granted"
        ) {

            updateNotificationStatus();


            /*
             Test notification
            */

            try {

                const notification =
                    new Notification(
                        "YASHWAY 🔔",
                        {
                            body:
                                "Booking notifications चालू झाले आहेत.",
                            tag:
                                "yashway-test-notification"
                        }
                    );


                notification.onclick =
                    function () {

                        window.focus();

                        notification.close();

                    };

            } catch (error) {

                console.log(
                    "Test notification error:",
                    error
                );

            }


            /*
             Test sound
            */

            playNotificationSound();


            /*
             Immediately check bookings
            */

            await checkProviderBookings();

        }


        /*
         Permission DENIED
        */

        else if (
            permission ===
            "denied"
        ) {

            if (status) {

                status.textContent =
                    "❌ Notifications blocked आहेत. Browser settings मधून Allow करा.";

            }

        }


        /*
         Permission DEFAULT
        */

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

                    /*
                     Logo file नसेल तरी
                     notification बंद होणार नाही.
                    */

                    tag:
                        "yashway-booking-" +
                        Date.now()
                }
            );


        /*
         Notification click
        */

        notification.onclick =
            function () {

                window.focus();

                notification.close();

            };


    }

    catch (error) {

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


        /*
         AudioContext resume
        */

        if (
            audioContext.state ===
            "suspended"
        ) {

            audioContext.resume();

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
            audioContext.currentTime +
            0.35
        );


    }

    catch (error) {

        console.log(
            "Sound unavailable:",
            error
        );

    }

}


/* =========================================================
   ADD NEW BOOKING TO DASHBOARD
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
        document.createElement(
            "div"
        );


    card.className =
        "admin-booking-card";


    card.dataset.bookingId =
        booking.id;


    /*
     Booking HTML
    */

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


            <!-- ACCEPT -->

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


            <!-- REJECT -->

            <form
                method="POST"
                action="/provider/reject/${booking.id}"
                style="
                    display:inline-block;
                    margin-left:10px;
                    margin-bottom:10px;
                "
                onsubmit="
                    return confirm(
                        'ही booking reject करायची आहे का?'
                    );
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
     नवीन booking वरच्या बाजूला दाखवा
    */

    container.prepend(
        card
    );

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

                    credentials:
                        "same-origin",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        /*
         Server response check
        */

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


        /*
         API data validation
        */

        if (
            !data.success ||
            !Array.isArray(
                data.bookings
            )
        ) {

            return;

        }


        /*
         प्रत्येक booking तपासा
        */

        data.bookings.forEach(
            function (booking) {

                const bookingId =
                    String(
                        booking.id
                    );


                /*
                 First page check

                 आधीपासून dashboard वर असलेल्या
                 booking साठी notification नको.
                */

                if (
                    firstCheck
                ) {

                    knownBookingIds.add(
                        bookingId
                    );

                    return;

                }


                /*
                 नवीन booking आहे का?
                */

                if (
                    !knownBookingIds.has(
                        bookingId
                    )
                ) {

                    /*
                     ID save करा
                    */

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

                        "\nService: " +
                        (
                            booking.service ||
                            ""
                        ) +

                        "\nLocation: " +
                        (
                            booking.location ||
                            ""
                        )

                    );


                    /*
                     Dashboard वर
                     नवीन booking दाखवा
                    */

                    addNewBookingCard(
                        booking
                    );

                }

            }
        );


        /*
         First check complete
        */

        firstCheck = false;


    }

    catch (error) {

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
         Enable Notifications button
         JS मधून connect करा.
        */

        const notificationButton =
            document.getElementById(
                "enable-notifications"
            );


        if (
            notificationButton
        ) {

            notificationButton.addEventListener(
                "click",
                enableNotifications
            );

        }


        /*
         First booking check
        */

        checkProviderBookings();


        /*
         प्रत्येक 5 seconds ला
         नवीन booking check
        */

        setInterval(
            checkProviderBookings,
            5000
        );


        /*
         User page वर click केल्यावर
         AudioContext तयार करा.
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
