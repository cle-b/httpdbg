var refresh = null;
var k7_id = null;

function refresh_resquests() {
    var table = document.getElementById("requests-list");
    var template_request = document.getElementById("template_request").innerHTML;
    var template_source = document.getElementById("template_source").innerHTML;
    fetch("/requests")
        .then(res => res.json())
        .then(data => {
            if (data["id"] != k7_id) {
                table.getElementsByTagName("tbody")[0].innerHTML = '';
                document.getElementById("headers").innerHTML = 'select a request to view details';
                document.getElementById("cookies").innerHTML = 'select a request to view details';
                document.getElementById("body_sent").innerHTML = 'select a request to view details';
                document.getElementById("body_received").innerHTML = 'select a request to view details';
            };
            k7_id = data["id"];

            var tbody = table.getElementsByTagName("tbody")[0];

            data["requests"].forEach(request => {
                if (!document.getElementById("request-" + request.id)) {

                    if (request.src) {
                        if (!document.getElementById("source-" + request.src.id)) {
                            var rendered = Mustache.render(template_source, request.src);
                            tbody.insertAdjacentHTML("beforeend", rendered);
                        }
                    }

                    var rendered = Mustache.render(template_request, request);
                    if (request.src) {
                        var last_row = document.querySelector("[data-source='" + request.src.id + "']:last-of-type");
                        last_row.insertAdjacentHTML("afterend", rendered);
                    } else {
                        tbody.insertAdjacentHTML("beforeend", rendered);
                    }
                };
            })
        })
        .then(enable_refresh())
        .catch((error) => {
            console.error('Error:', error);
            disable_refresh();
        });
};

function disable_refresh() {
    document.getElementById("refresh").style.display = "block";
    if (refresh != null)
        clearInterval(refresh);
    refresh = setInterval(function () {
        refresh_resquests();
    }, 20000);
}


function enable_refresh() {
    document.getElementById("refresh").style.display = "none";
    if (refresh != null)
        clearInterval(refresh);
    refresh = setInterval(function () {
        refresh_resquests();
    }, 2000);
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

    fetch("/request/" + request_id)
        .then(res => res.json())
        .then(data => function (data) {

                update_with_template("template_headers", "headers", data);

                update_with_template("template_cookies", "cookies", data);

                update_with_template("template_body", "body_sent", data.request);

                update_with_template("template_body", "body_received", data.response);
            }
            (data));
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