"use strict";

var refresh = null;
var k7_id = null;

async function refresh_resquests() {
    var table = document.getElementById("requests-list");
    var template_request = document.getElementById("template_request").innerHTML;

    if (global.k7 != k7_id) {
        table.getElementsByTagName("tbody")[0].innerHTML = '';
        document.getElementById("headers").innerHTML = 'select a request to view details';
        document.getElementById("cookies").innerHTML = 'select a request to view details';
        document.getElementById("body_sent").innerHTML = 'select a request to view details';
        document.getElementById("body_received").innerHTML = 'select a request to view details';
        document.getElementById("exception").innerHTML = 'select a request to view details';
        document.getElementById("initiator").innerHTML = 'select a request to view details';
    };
    k7_id = global.k7;

    var tbody = table.getElementsByTagName("tbody")[0];

    for (const [request_id, request] of Object.entries(global.requests)) {
        if (request.to_refresh) {
            var elt = document.getElementById("request-" + request.id);
            var rendered = Mustache.render(template_request, request);
            if (!elt) {
                tbody.insertAdjacentHTML("beforeend", rendered);
            } else {
                elt.innerHTML = rendered;
            };
            request.to_refresh = false;
        }
    };
}


function update_with_template(template_id, target_id, data) {
    var template = document.getElementById(template_id).innerHTML;
    var rendered = Mustache.render(template, data);
    document.getElementById(target_id).innerHTML = rendered;
}


function show_request(request_id) {

    var active_rows = document.getElementsByClassName("active-row");
    [].forEach.call(active_rows, function (el) {
        el.classList.remove("active-row");
    });

    document.getElementById("request-" + request_id).classList.add("active-row");

    var data = global.requests[request_id].data;

    update_with_template("template_headers", "headers", data);

    update_with_template("template_cookies", "cookies", data);

    var request = data.request ? data.request : {
        "body": null
    };
    update_with_template("template_body", "body_sent", request);

    var response = data.response ? data.response : {
        "body": null
    };
    update_with_template("template_body", "body_received", response);

    update_with_template("template_exception", "exception", data);

    update_with_template("template_initiator", "initiator", data);
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

async function enable_refresh() {

    while (true) {
        await Promise.all([
            refresh_resquests(),
            wait_for(500)
        ]);
    }
}