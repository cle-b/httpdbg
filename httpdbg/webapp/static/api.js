"use strict";

const global = {
    session: null,
    sessions: {},
    requests: {},
    initiators: {},
    groups: {},    
    connected: false,
    group_collapse: [],
    groupby: "default"
}

function save_request(request_id, request, session_id) {
    const initiator = global.initiators[request.initiator_id] ?? null;
    if (initiator !== null) {  // the initiator may be missing if the clean list is executed in parrallel
        request.loaded = false;
        request.to_refresh = true;
        if (request.pin == undefined) {
            request.pin = "";
        }
        if (request.filter == undefined) {
            request.filter = "---";
        }
        request.session_id = session_id;
        request.initiator = initiator;
    
        if (request.in_progress) {
            request.status_code_view = '<img class="icon" src="static/icons/wait-sandclock-icon.svg-+-$**HTTPDBG_VERSION**$" alt="loading"/>';
        } else {
            switch (request.status_code) {
                case 0:
                    request.status_code_view = '<img class="icon" src="static/icons/wait-sandclock-icon.svg-+-$**HTTPDBG_VERSION**$/" alt="loading"/>';
                    break;
                case -1:
                    request.status_code_view = '<img class="icon" src="static/icons/math-multiplication-icon.svg-+-$**HTTPDBG_VERSION**$/" alt="load failed"/>';
                    break;
                default:
                    request.status_code_view = request.status_code;
                    break;
            }
        }
    
        global.requests[request_id] = request;    
    
        if (!request.pin) {
            get_request(request_id);
        }    
    }
}

async function get_all_requests() {

    var requests_already_loaded = 0
    for (const [request_id, request] of Object.entries(global.requests)) {
        if (request.loaded && (global.session == request.session_id)) {
            requests_already_loaded += 1;
        }
    }
    var url = "/requests?" + new URLSearchParams({
        "id": global.session,
        "requests_already_loaded": requests_already_loaded,
    })

    await fetch(url)
        .then(res => res.json())
        .then(data => {
            global.connected = true;

            if (data.session.id != global.session) {
                clean();                
                global.session = data.session.id;
                global.sessions[data.session.id] = data.session;                
            };

            // for the initiators and the groups, we can just save them without any verification
            Object.assign(global.initiators, data.initiators);
            Object.assign(global.groups, data.groups);

            // for the requests, we may have to update them 
            for (const [request_id, request] of Object.entries(data.requests)) {
                if (!(request_id in global.requests)) {
                    // this is a new request
                    save_request(request_id, request, data.session.id);
                } else {
                    if (global.requests[request_id].last_update < request.last_update) {
                        // this request has been updated (probably a "big" file) 
                        save_request(request_id, request, data.session.id);
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
            global.requests[request_id].filter = prepare_for_filter(global.requests[request_id].url);

            global.requests[request_id].request = data.request;
            if (data.request.body && data.request.body.text) {
                global.requests[request_id].filter += " " + prepare_for_filter(
                    parse_raw_text(
                        data.request.body.text,
                        data.request.body.content_type
                    ) || data.request.body.text
                );
            }

            global.requests[request_id].response = data.response;
            if (data.response.body && data.response.body.text) {
                global.requests[request_id].filter += " " + prepare_for_filter(
                    parse_raw_text(
                        data.response.body.text,
                        data.response.body.content_type
                    ) || data.response.body.text
                );
            }

            // the full stack is not present in request summary
            global.requests[request_id].initiator_id = data.initiator_id;
            global.requests[request_id].exception = data.exception;

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