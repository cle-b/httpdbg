"use strict";

let global = {
    "k7": null,
    "requests": {},
    "connected": false
}

function save_request(request_id, request) {
    request.loaded = false;
    request.to_refresh = true;
    global.requests[request_id] = request;
    switch (global.requests[request_id].status_code) {
        case 0:
            global.requests[request_id].status_code_view = "&#9203";
            break;
        case -1:
            global.requests[request_id].status_code_view = "&#10060";
            break;
        default:
            global.requests[request_id].status_code_view = global.requests[request_id].status_code;
            break;
    }

    get_request(request_id);
}

async function get_all_requests() {

    var requests_already_loaded = 0
    for (const [request_id, request] of Object.entries(global.requests)) {
        if (request.loaded) {
            requests_already_loaded += 1;
        }
    }
    var url = "/requests?" + new URLSearchParams({
        "id": global.k7,
        "requests_already_loaded": requests_already_loaded,
    })

    await fetch(url)
        .then(res => res.json())
        .then(data => {
            global.connected = true;

            if (data.id != global.k7) {
                global.k7 = data.id;
                global.requests = {};
            };

            for (const [request_id, request] of Object.entries(data.requests)) {
                if (!(request_id in global.requests)) {
                    // this is a new request
                    save_request(request_id, request);
                } else {
                    if (global.requests[request_id].status_code != request.status_code) {
                        // this request has been updated (probably a "big" file) 
                        save_request(request_id, request);
                    }
                };
            };
        })
        .catch((error) => {
            global.connected = false;
        });

}

async function get_request(request_id) {

    await fetch("/request/" + request_id)
        .then(res => res.json())
        .then(data => {
            global.connected = true;

            global.requests[request_id]["data"] = data;

            global.requests[request_id].loaded = true;
        })
        .catch((error) => {
            global.connected = false;
        });

}

async function pol_new_data() {

    while (true) {
        await Promise.all([
            get_all_requests(),
            wait_for(1000)
        ]);
    }
}