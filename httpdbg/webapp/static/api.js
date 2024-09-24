"use strict";

const global = {
    "k7": null,
    "requests": {},
    "connected": false,
    "initiator_collapse": []
}

function save_request(request_id, request) {
    request.loaded = false;
    request.to_refresh = true;
    if (request.pin == undefined) {
        request.pin = "";
    }
    global.requests[request_id] = request;
    if (global.requests[request_id].in_progress) {
        global.requests[request_id].status_code_view = '<img class="icon" src="static/icons/wait-sandclock-icon.svg-+-$**HTTPDBG_VERSION**$" alt="loading"/>';
    } else {
        switch (global.requests[request_id].status_code) {
            case 0:
                global.requests[request_id].status_code_view = '<img class="icon" src="static/icons/wait-sandclock-icon.svg-+-$**HTTPDBG_VERSION**$/" alt="loading"/>';
                break;
            case -1:
                global.requests[request_id].status_code_view = '<img class="icon" src="static/icons/math-multiplication-icon.svg-+-$**HTTPDBG_VERSION**$/" alt="load failed"/>';
                break;
            default:
                global.requests[request_id].status_code_view = global.requests[request_id].status_code;
                break;
        }
    }
    global.requests[request_id].request = global.requests[request_id].request || {
        "for_filter": ""
    }
    global.requests[request_id].response = global.requests[request_id].response || {
        "for_filter": ""
    }

    if (!request.pin) {
        get_request(request_id);
    }
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
                clean();
            };

            for (const [request_id, request] of Object.entries(data.requests)) {
                if (!(request_id in global.requests)) {
                    // this is a new request
                    save_request(request_id, request);
                } else {
                    if (global.requests[request_id].last_update < request.last_update) {
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

            global.requests[request_id].request = data.request;
            if (data.request.body && data.request.body.text) {
                global.requests[request_id].request.for_filter = prepare_for_filter(
                    parse_raw_text(
                        data.request.body.text,
                        data.request.body.content_type
                    ) || data.request.body.text
                );
            } else {
                global.requests[request_id].request.for_filter = "";
            }

            global.requests[request_id].response = data.response;
            if (data.response.body && data.response.body.text) {
                global.requests[request_id].response.for_filter = prepare_for_filter(
                    parse_raw_text(
                        data.response.body.text,
                        data.response.body.content_type
                    ) || data.response.body.text
                );
            } else {
                global.requests[request_id].response.for_filter = "";
            }

            // the full stack is not present in request summary
            global.requests[request_id].initiator = data.initiator;

            global.requests[request_id].to_refresh = true;

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

function pin_request(request_id, pin) {
    if (pin) {
        global.requests[request_id].pin = "checked";
    } else {
        global.requests[request_id].pin = "";
    }
}