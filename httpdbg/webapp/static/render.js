function refresh_resquests() {
    var table = document.getElementById("requests-list");
    var template = document.getElementById("template_request").innerHTML;
    fetch("http://localhost:5000/requests")
        .then(res => res.json())
        .then(data => data.forEach(request => {    
            if (! document.getElementById("request-" + request.id)){
                var rendered = Mustache.render(template, request);
                table.getElementsByTagName("tbody")[0].insertAdjacentHTML("beforeend", rendered);
            }
        }));
};


function update_with_template(template_id, target_id, data){
    var template = document.getElementById(template_id).innerHTML;
    var rendered = Mustache.render(template, data);
    document.getElementById(target_id).innerHTML = rendered;
}

function show_request(request_id) {
    fetch("http://localhost:5000/request/" + request_id)
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