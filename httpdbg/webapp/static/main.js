"use strict";

let httpdbgApp = {
    config: {
        keep_previous_sessions: {
            id: "ckeepsession",
            type: "checkbox",
            param: "kp",
            value: false
        },
        group_by: {
            id: "groupby-select",
            type: "select",
            param: "gb",
            value: "default"
        },
        hide_group: {
            id: "cinitiator",
            type: "checkbox",
            param: "hi",
            css: ".group {display: none;}",
            value: false
        },
        hide_netloc: {
            id: "curl",
            type: "checkbox",
            param: "hn",
            css: ".netloc {display: none;}",
            value: false
        },
        hide_tag: {
            id: "ctag",
            type: "checkbox",
            param: "ht",
            css: ".tag {display: none;}",
            value: false
        },
        details_wrap_default: {
            id: "cwrap",
            type: "checkbox",
            param: "wl",
            elt_name: "ckwraptext",
            value: false
        },
        details_raw_default: {
            id: "craw",
            type: "checkbox",
            param: "rd",
            elt_name: "ckrawdata",
            value: false
        }
    }
}

function wait_for(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// use keys sequences as shortcut
var keys_history = "";
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

    if (keys_history.endsWith("oh")) {
        help();
    }

    if (keys_history.endsWith("lf")) {
        select_first_request();
    }

    if (keys_history.endsWith("ll")) {
        select_last_request();
    }

    if (keys_history.endsWith("ln")) {
        select_next_request();
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