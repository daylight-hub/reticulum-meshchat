class NotificationUtils {

    // Notifications are a nice-to-have. The API is unavailable or blocked in some
    // contexts (non-secure origins, self-signed certs, embedded webviews), where even
    // touching it throws. Everything here is guarded so a notification failure can
    // never break call handling - the ringtone and UI must always still work.
    static isSupported() {
        try {
            return typeof window !== "undefined"
                && typeof window.Notification !== "undefined"
                && typeof window.Notification.requestPermission === "function";
        } catch (e) {
            return false;
        }
    }

    static show(title, body, tag) {
        if (!NotificationUtils.isSupported()) {
            return;
        }
        try {
            const result = window.Notification.requestPermission();
            // older browsers use a callback instead of returning a promise
            if (result && typeof result.then === "function") {
                result.then((permission) => {
                    try {
                        if (permission === "granted") {
                            new window.Notification(title, { body: body, tag: tag });
                        }
                    } catch (e) {
                        console.debug("notification failed", e);
                    }
                }).catch((e) => console.debug("notification permission failed", e));
            }
        } catch (e) {
            console.debug("notification unavailable", e);
        }
    }

    static showIncomingCallNotification() {
        // only ever show one incoming call notification at a time
        NotificationUtils.show("Incoming Call", "Someone is calling you.", "new_audio_call");
    }

    static showNewMessageNotification() {
        // only ever show one new message notification at a time
        NotificationUtils.show("New Message", "Someone sent you a message.", "new_message");
    }

}

export default NotificationUtils;
