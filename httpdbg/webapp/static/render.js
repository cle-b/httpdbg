"use strict";

var k7_id = null;

async function refresh_resquests() {
    var table = document.getElementById("requests-list");
    var template_request = document.getElementById("template_request").innerHTML;
    var template_initiator = document.getElementById("template_initiator").innerHTML;

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
                var elt_initiator = document.getElementById("initiator-" + request.initiator.id);
                if (!elt_initiator) {
                    request.initiator.long_label = request.initiator.long_label || request.initiator.short_stack;
                    var rendered_initiator = Mustache.render(template_initiator, request);
                    table.insertAdjacentHTML("beforeend", rendered_initiator);
                    elt_initiator = document.getElementById("initiator-" + request.initiator.id);
                };
                elt_initiator.insertAdjacentHTML("beforeend", rendered);
            } else {
                elt.innerHTML = rendered;
            };
            request.to_refresh = false;
        }
    };
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

    var data = global.requests[request_id].data;

    update_with_template("template_title", document.querySelector("#title > div[name='" + name + "']"), data);

    update_with_template("template_headers", document.querySelector("#headers > div[name='" + name + "']"), data);

    update_with_template("template_cookies", document.querySelector("#cookies > div[name='" + name + "']"), data);

    var request = data.request ? data.request : {
        "body": null
    };

    if (request.body && request.body.text) {
        request.body.raw_text = "global.requests['" + request_id + "'].data.request.body.text";
        if (request.body.parsed) {
            request.body.parsed_text = "global.requests['" + request_id + "'].data.request.body.parsed";
        }
    };

    update_with_template("template_body", document.querySelector("#body_sent > div[name='" + name + "']"), request);

    var response = data.response ? data.response : {
        "body": null
    };

    if (response.body && response.body.text) {
        response.body.raw_text = "global.requests['" + request_id + "'].data.response.body.text";
        if (response.body.parsed) {
            response.body.parsed_text = "global.requests['" + request_id + "'].data.response.body.parsed";
        }
    };

    update_with_template("template_body", document.querySelector("#body_received > div[name='" + name + "']"), response);

    update_with_template("template_exception", document.querySelector("#exception > div[name='" + name + "']"), data);

    update_with_template("template_stack", document.querySelector("#stack > div[name='" + name + "']"), data);
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

        var initiators = document.getElementsByName("initiator");
        while (initiators.length > 0) {
            initiators[0].remove();
        }

        empty_content("[name='request']", "select a request to view details");

        empty_content("[name='compareto']", "");
        hide_elts(".comparison", true);

        var tmprequests = {};

        for (const [request_id, request] of Object.entries(global.requests)) {
            if (request.pin == "checked") {
                tmprequests[request_id] = request
            }
        };

        global.requests = {};

        for (const [request_id, request] of Object.entries(tmprequests)) {
            save_request(request_id, request);
        };
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