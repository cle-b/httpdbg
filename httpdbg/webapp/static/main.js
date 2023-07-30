"use strict";

let httpdbgApp = {
    "config": {
        "hide_initiator": {
            "checkbox": "cinitiator",
            "param": "hi",
            "css": ".initiator {display: none;}",
            "value": false
        },
        "hide_netloc": {
            "checkbox": "curl",
            "param": "hn",
            "css": ".netloc {display: none;}",
            "value": false
        }
    }
}

function wait_for(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// use keys sequences as shortcut
var keys_history= "";
window.addEventListener('keydown', (event) => {

    if (document.activeElement) {
        if (document.activeElement.tagName.toLowerCase() === "input") {
            if (document.activeElement.getAttribute("type").toLowerCase() === "text") {
                return;
            }
        }
    }

    keys_history += event.key.toLowerCase();

    if (keys_history.endsWith("rh")) {
        opentab_headers();
    }

    if (keys_history.endsWith("rc")) {
        opentab_cookies();
    }

    if (keys_history.endsWith("rp")) {
        opentab_request();
    }

    if (keys_history.endsWith("rt")) {
        opentab_response();
    }

    if (keys_history.endsWith("re")) {
        opentab_exception();
    }

    if (keys_history.endsWith("rs")) {
        opentab_stack();
    }

    if (keys_history.endsWith("oc")) {
        config();
    }

    if (keys_history.endsWith("oh")) {
        help();
    }

    keys_history = keys_history.substr(-8, 8)
});

function help() {
    if (document.getElementById("help").style.display == "block") {
        document.getElementById("help").style.display = "none";
    } else {
        document.getElementById("help").style.display = "block";
    }
}