"use strict";

let global = {
    "k7": null,
    "requests": {},
    "connected": false
}


async function get_all_requests() {

    await fetch("/requests")
        .then(res => res.json())
        .then(data => {
            global.connected = true;

            if (data.id != global.k7) {
                global.k7 = data.id;
                global.requests = {};
            };

            for (const [request_id, request] of Object.entries(data.requests)) {
                if (!(request_id in global.requests)) {
                    global.requests[request_id] = request;
                    get_request(request_id);
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