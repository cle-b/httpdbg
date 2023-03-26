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
        var new_rule = '[data-filter-url*="' + value + '"] {display: table-row;}'
    }

    sheet.insertRule(new_rule);
}