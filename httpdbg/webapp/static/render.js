"use strict";

var k7_id = null;

async function refresh_resquests() {
    var table = document.getElementById("requests-list");
    var template_request = document.getElementById("template_request").innerHTML;
    var template_group = document.getElementById("template_group").innerHTML;

    if (global.k7 != k7_id) {
        clean();
    };
    k7_id = global.k7;

    for (const [request_id, request] of Object.entries(global.requests)) {
        if (request.to_refresh) {
            var elt = document.getElementById("request-" + request.id);

            request.title = request.url;
            if (request.initiator.short_stack) {
                request.title += "\n\n" + request.initiator.short_stack;
            }
            request.title += "\n\nclick to select -/- ctrl+click to compare to";

            var rendered = Mustache.render(template_request, request);
            if (!elt) {
                var elt_group = document.getElementById("group-" + request.group_id);
                if (!elt_group) {
                    var rendered_group = Mustache.render(template_group, global.groups[request.group_id]);
                    table.insertAdjacentHTML("beforeend", rendered_group);
                    elt_group = document.getElementById("group-" + request.group_id);
                };
                elt_group.insertAdjacentHTML("beforeend", rendered);
            } else {
                elt.innerHTML = rendered;
            };

            request.to_refresh = false;
        }
    };
    filter_requests_count();
}


function update_with_template(template_id, element, data) {
    var template = document.getElementById(template_id).innerHTML;
    var rendered = Mustache.render(template, data);
    element.innerHTML = rendered;
}

function select_request(event, request_id) {
    event.preventDefault();
    event.stopPropagation();

    if (!(event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) || (document.getElementsByClassName("active-row").length == 0)) {
        show_request(request_id);
    } else {
        compare_to_request(request_id);
    }
}

function unselect_request(request_id) {
    if (document.querySelector(".active-row") == document.querySelector("#request-" + request_id)) {
        document.querySelector(".active-row-compare").click();
    } else {
        document.querySelector(".active-row").click();
    }
}

function shortcut_request(event, request_id) {
    var key_pressed = event.key.toLowerCase()
    // select the request
    if ((key_pressed === "s") || (key_pressed === "enter")) {
        show_request(request_id);
    }
    // compare the request to the one already selected
    if (key_pressed === "c") {
        if ((document.getElementsByClassName("active-row").length > 0)) {
            compare_to_request(request_id);
        } else {
            // if no request is already selected, just select the new one
            show_request(request_id);
        }
    }
}

function remove_class(classname) {
    var elts = document.getElementsByClassName(classname);
    [].forEach.call(elts, function (el) {
        el.classList.remove(classname);
    });
}

function compare_to_request(request_id) {
    if (!document.getElementById("request-" + request_id).classList.contains("active-row")) {
        remove_class("active-row-compare");

        document.getElementById("request-" + request_id).classList.add("active-row-compare");

        fill_content(request_id, "compareto");
        hide_elts(".comparison", false);
    }
}

function show_request(request_id) {

    remove_class("active-row");
    remove_class("active-row-compare");
    empty_content("[name='compareto']", "");
    hide_elts(".comparison", true);

    document.getElementById("request-" + request_id).classList.add("active-row");

    fill_content(request_id, "request");
}

function fill_content(request_id, name) {

    var req = global.requests[request_id];

    update_with_template("template_title", document.querySelector("#title > div[name='" + name + "']"), req);

    update_with_template("template_headers", document.querySelector("#headers > div[name='" + name + "']"), req);

    update_with_template("template_cookies", document.querySelector("#cookies > div[name='" + name + "']"), req);

    var request = req.request ? req.request : {
        "body": null,
    };

    if (request.body && request.body.text) {
        request.body.raw_text = "global.requests['" + request_id + "'].request.body.text";

        const parsed_text = parse_raw_text(request.body.text, request.body.content_type);
        if (parsed_text) {
            request.body.parsed = parsed_text;
        }

        if (request.body.parsed) {
            request.body.parsed_text = "global.requests['" + request_id + "'].request.body.parsed";
        }
    };

    update_with_template("template_body", document.querySelector("#body_sent > div[name='" + name + "']"), request);

    var response = req.response ? req.response : {
        "body": null
    };

    if (response.body && response.body.text) {
        response.body.raw_text = "global.requests['" + request_id + "'].response.body.text";

        const parsed_text = parse_raw_text(response.body.text, response.body.content_type);
        if (parsed_text) {
            response.body.parsed = parsed_text;
        }

        if (response.body.parsed) {
            response.body.parsed_text = "global.requests['" + request_id + "'].response.body.parsed";
        }
    };

    update_with_template("template_body", document.querySelector("#body_received > div[name='" + name + "']"), response);

    update_with_template("template_exception", document.querySelector("#exception > div[name='" + name + "']"), req);

    update_with_template("template_stack", document.querySelector("#stack > div[name='" + name + "']"), req);

    apply_config();
}


function opentab(btn, tabname) {

    var i, tabcontent, tablinks;

    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    document.getElementById(tabname).style.display = "block";
    btn.className += " active";
}

function opentab_headers() {
    opentab(document.getElementById("btn-tab-headers"), "tabHeaders");
}

function opentab_cookies() {
    opentab(document.getElementById("btn-tab-cookies"), "tabCookies");
}

function opentab_request() {
    opentab(document.getElementById("btn-tab-request"), "tabRequest");
}

function opentab_response() {
    opentab(document.getElementById("btn-tab-response"), "tabResponse");
}

function opentab_exception() {
    opentab(document.getElementById("btn-tab-exception"), "tabException");
}

function opentab_stack() {
    opentab(document.getElementById("btn-tab-stack"), "tabStack");
}


async function disable_link_if_server_disconnected() {
    var sheet = document.getElementById("serverstatuscss").sheet;

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0);
    }

    if (global.connected) {
        sheet.insertRule(".need-server {}");
        sheet.insertRule(".need-server-info {display: none;}");
    } else {
        sheet.insertRule(".need-server {\
            color: var(--link-server-disconnected);\
            pointer-events: none;\
            opacity: 0.5;\
            text-decoration: none;\
        }");
        sheet.insertRule(".need-server-info {\
             display: inline;\
             color: var(--link-server-disconnected);\
             opacity: 0.5;\
         }");
    }
}

async function enable_refresh() {

    while (true) {
        await Promise.all([
            disable_link_if_server_disconnected(),
            refresh_resquests(),
            wait_for(500),
        ]);
    }
}

function show_wrap_lines(elt) {
    elt.classList.toggle("prewrap");
}

function show_raw_data(elt, show_raw_text, raw_text, parsed_text) {
    var preview;

    if (show_raw_text) {
        preview = raw_text;
    } else {
        preview = parsed_text;
    }

    elt.textContent = preview;
}

function clean(force_clean = false) {
    var onlynew = document.getElementById("onlynew");
    if (onlynew.checked || force_clean) {

        var initiators = document.getElementsByName("group");
        while (initiators.length > 0) {
            initiators[0].remove();
        }

        empty_content("[name='request']", "select a request to view details");

        empty_content("[name='compareto']", "");
        hide_elts(".comparison", true);

        var tmprequests = {};
        var tmpinitiators = {};
        var tmpgroups = {};

        for (const [request_id, request] of Object.entries(global.requests)) {
            if (request.pin == "checked") {
                tmprequests[request_id] = request
                tmpinitiators[request.initiator_id] = global.initiators[request.initiator_id];
                tmpgroups[request.group_id] = global.groups[request.group_id];
            }
        };

        global.initiators = tmpinitiators;
        global.groups = tmpgroups;

        global.requests = {};

        for (const [request_id, request] of Object.entries(tmprequests)) {
            save_request(request_id, request);
        };

        global.group_collapse = [];

        update_collapse_group();
    }
}

function empty_content(selector, value) {
    var elts = document.querySelectorAll(selector);
    [].forEach.call(elts, function (el) {
        el.innerHTML = value;
    });
}

function hide_elts(selector, value) {
    var elts = document.querySelectorAll(selector);
    [].forEach.call(elts, function (el) {
        el.hidden = value;
    });
}

function select_first_request() {
    var requests = document.getElementsByClassName("request");

    if (requests.length > 0) {
        requests[0].click();
    }
}

function select_last_request() {
    var requests = document.getElementsByClassName("request");

    if (requests.length > 0) {
        requests[requests.length - 1].click();
        requests[requests.length - 1].scrollIntoView();
    }
}

function select_next_request() {
    var request = document.querySelector(".active-row ~ .request");

    if (request == undefined) {
        // maybe there are some requests under another initiator
        var next_initiator = document.querySelector(".active-row").parentElement.nextElementSibling;

        if (next_initiator != undefined) {
            request = next_initiator.querySelector(".request");
        }
    }

    if (request != undefined) {
        request.click();
    }
}

function parse_raw_text(raw_text, content_type) {
    var parsed_text = "";

    if (content_type.toLowerCase().includes("json")) {
        try {
            parsed_text = JSON.stringify(JSON.parse(raw_text), null, "    ");
        } catch {
            return;
        }
    } else if (content_type.toLowerCase().includes("x-www-form-urlencoded")) {
        try {
            var params = new URLSearchParams(raw_text);

            for (const key of params.keys()) {
                params.getAll(key).forEach((value) => {
                    try {
                        parsed_text += key + ": " + JSON.stringify(JSON.parse(value), null, "    ") + "\n";
                    } catch {
                        parsed_text += key + ": " + value + "\n";
                    }
                });
            }
        } catch {
            return;
        }
    } else {
        // we try to parse the content using the JSON format because it happens the content type is JSON
        // but the header doesn't contain "json"
        try {
            parsed_text = JSON.stringify(JSON.parse(raw_text), null, "    ");
        } catch {
            return;
        }
    }

    return parsed_text;
}

function prepare_for_filter(txt) {
    return encodeURI(txt.replace(/\s+/g, '').toLowerCase());
}