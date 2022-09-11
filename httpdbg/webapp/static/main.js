"use strict";

let httpdbgApp = {
    "config": {
        "hide_status": {
            "checkbox": "cstatus",
            "param": "hs",
            "css": ".status {display: none;}",
            "value": true
        },
        "hide_method": {
            "checkbox": "cmethod",
            "param": "hm",
            "css": ".method {display: none;}",
            "value": true
        },
        "hide_initiator": {
            "checkbox": "cinitiator",
            "param": "hi",
            "css": ".initiator {display: none;}",
            "value": true
        }
    }
}

function wait_for(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}