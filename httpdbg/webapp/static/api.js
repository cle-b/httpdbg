"use strict";

// the requests and initiators are in the same list, and ordered by the creation date (tbegin)
function save_order(httpdbg, elt_id, tbegin) {

    if (httpdbg.order.length == 0) {
        httpdbg.order[0] = {
            "elt_id": elt_id,
            "tbegin": tbegin
        };
    } else {
        // most of the time the last elt will be the most recent one
        var i = httpdbg.order.length;
        while (i > 0) {
            if (tbegin > httpdbg.order[i - 1].tbegin) {
                break;
            }
            i = i - 1;
        }

        httpdbg.order.splice(i, 0, {
            "elt_id": elt_id,
            "tbegin": tbegin
        });
    }
}

function get_previous_elt(httpdbg, elt_id) {

    var i = httpdbg.order.length - 1;

    while (i > 0) {
        if (httpdbg.order[i].elt_id == elt_id) {
            return httpdbg.order[i - 1].elt_id;
        }
        i = i - 1;
    }

    return;
}

function save_initiator(httpdbg, initiator_id, initiator) {
    initiator.to_refresh = true;

    save_order(httpdbg, "initiator-" + initiator_id, initiator.tbegin);

    httpdbg.initiators[initiator_id] = initiator;
}

function save_request(httpdbg, request_id, request) {
    request.loaded = false;
    request.to_refresh = true;
    if (request.pin == undefined) {
        request.pin = "";
    }

    save_order(httpdbg, "request-" + request_id, request.tbegin);

    httpdbg.requests[request_id] = request;
    if (httpdbg.requests[request_id].in_progress) {
        httpdbg.requests[request_id].status_code_view = '<img class="icon" src="static/icons/wait-sandclock-icon.svg-+-$**HTTPDBG_VERSION**$" alt="loading"/>';
    } else {
        switch (httpdbg.requests[request_id].status_code) {
            case 0:
                httpdbg.requests[request_id].status_code_view = '<img class="icon" src="static/icons/wait-sandclock-icon.svg-+-$**HTTPDBG_VERSION**$/" alt="loading"/>';
                break;
            case -1:
                httpdbg.requests[request_id].status_code_view = '<img class="icon" src="static/icons/math-multiplication-icon.svg-+-$**HTTPDBG_VERSION**$/" alt="load failed"/>';
                break;
            default:
                httpdbg.requests[request_id].status_code_view = httpdbg.requests[request_id].status_code;
                break;
        }
    }
    httpdbg.requests[request_id].request = httpdbg.requests[request_id].request || {
        "for_filter": ""
    }
    httpdbg.requests[request_id].response = httpdbg.requests[request_id].response || {
        "for_filter": ""
    }

    if (!request.pin) {
        get_request(httpdbg, request_id);
    }
}

async function get_all_requests(httpdbg) {

    var requests_already_loaded = 0
    for (const [request_id, request] of Object.entries(httpdbg.requests)) {
        if (request.loaded) {
            requests_already_loaded += 1;
        }
    }
    var url = "/requests?" + new URLSearchParams({
        "id": httpdbg.k7,
        "requests_already_loaded": requests_already_loaded,
    })

    await fetch(url)
        .then(res => res.json())
        .then(data => {
            httpdbg.connected = true;

            if (data.id != httpdbg.k7) {
                httpdbg.k7 = data.id;
                clean();
            };

            // the initiators
            for (const [initiator_id, initiator] of Object.entries(data.initiators)) {
                if (!(initiator_id in httpdbg.initiators)) {
                    // this is a new initiator
                    save_initiator(httpdbg, initiator_id, initiator);
                }
            };

            // the requests
            for (const [request_id, request] of Object.entries(data.requests)) {
                if (!(request_id in httpdbg.requests)) {
                    // this is a new request
                    save_request(httpdbg, request_id, request);
                } else {
                    if (httpdbg.requests[request_id].last_update < request.last_update) {
                        // this request has been updated (probably a "big" file) 
                        save_request(httpdbg, request_id, request);
                    }
                };
            };
        })
        .catch((error) => {
            // console.log("ERROR in get_all_requests: " + error.toString());
            httpdbg.connected = false;
        });

}

async function get_request(httpdbg, request_id) {

    await fetch("/request/" + request_id)
        .then(res => res.json())
        .then(data => {
            httpdbg.connected = true;

            httpdbg.requests[request_id].request = data.request;
            if (data.request.body && data.request.body.text) {
                httpdbg.requests[request_id].request.for_filter = prepare_for_filter(
                    parse_raw_text(
                        data.request.body.text,
                        data.request.body.content_type
                    ) || data.request.body.text
                );
            } else {
                httpdbg.requests[request_id].request.for_filter = "";
            }

            httpdbg.requests[request_id].response = data.response;
            if (data.response.body && data.response.body.text) {
                httpdbg.requests[request_id].response.for_filter = prepare_for_filter(
                    parse_raw_text(
                        data.response.body.text,
                        data.response.body.content_type
                    ) || data.response.body.text
                );
            } else {
                httpdbg.requests[request_id].response.for_filter = "";
            }

            // the full stack is not present in request summary
            httpdbg.requests[request_id].initiator = data.initiator;

            httpdbg.requests[request_id].to_refresh = true;

            httpdbg.requests[request_id].loaded = true;
        })
        .catch((error) => {
            httpdbg.connected = false;
        });

}


function pin_request(request_id, pin) {
    if (pin) {
        httpdbg_global.requests[request_id].pin = "checked";
    } else {
        httpdbg_global.requests[request_id].pin = "";
    }
}