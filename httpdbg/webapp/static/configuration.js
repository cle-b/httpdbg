function hide_column(params, param, selector, sheet) {
    if (params.has(param)) {
        if (params.get(param) == "on") {
            sheet.insertRule(selector + " {display: none;}");
        }
    }
}

function configure_index() {
    var sheet = document.getElementById("configuration").sheet;
    const params = new URLSearchParams(window.location.search);

    hide_column(params, "hs", ".status", sheet);
    hide_column(params, "hm", ".method", sheet);
    hide_column(params, "hi", ".initiator", sheet);

    document.getElementById("config").href = "config" + window.location.search;
}

function check_it(params, param, id) {
    if (params.has(param)) {
        if (params.get(param) == "on") {
            document.getElementById(id).checked = true;
        }
    }
}

function configure_config() {
    const params = new URLSearchParams(window.location.search);

    check_it(params, "hs", "hs");
    check_it(params, "hm", "hm");
    check_it(params, "hi", "hi");
}