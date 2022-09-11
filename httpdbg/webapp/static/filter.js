"use strict";

function update_filter_url() {
    var sheet = document.getElementById("filter").sheet;

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0);
    }

    var value = document.getElementById("filter-url").value;
    if (value == "") {
        new_rule = '[data-filter-url] {display: table-row;}'
    } else {
        if (document.querySelectorAll('[data-filter-url*="' + value + '"]').length == 0) {
            sheet.insertRule("#filter-url-btn {color: #c74545;}");
        } else {
            sheet.insertRule("#filter-url-btn {color: #91e64b;}");
        }
        var new_rule = '[data-filter-url*="' + value + '"] {display: table-row;}'
    }

    sheet.insertRule(new_rule);
}

function show_filter_url() {
    var elt = document.getElementById("filter-url");

    if (elt.style.display === "none") {
        elt.style.display = "inline-block";
    } else {
        elt.style.display = "none";
    }
}