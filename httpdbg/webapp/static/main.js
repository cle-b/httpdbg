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