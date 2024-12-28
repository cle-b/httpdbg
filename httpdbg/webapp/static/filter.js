"use strict";

function update_filter_url() {
    var sheet = document.getElementById("filter").sheet;

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0);
    }

    var value = prepare_for_filter(document.getElementById("filter-url").value);

    if (value == "") {
        // if there is no filter, all rows are visible
        sheet.insertRule("[data-filter] {display: table-row;}");
        sheet.insertRule(".group-header {display: table-row-group;}");
    } else {
        // if there is a filter, only the requests that match the filter are visible
        sheet.insertRule('[data-filter*="' + value + '"] {display: table-row;}');
        if (CSS.supports("selector(:has(*))")) {
            // a group row is visible only if it contains at least one visible request
            sheet.insertRule('.group-header:has([data-filter*="' + value + '"]) {display: table-row-group;}');
            // if there is a filter and no request visible, the filter icon is red
            sheet.insertRule('.requests-table:not(:has([data-filter*="' + value + '"])):has(tbody) .icon-filter {filter: grayscale(0%) !important;}');
        } else {
            // in case :has is not supported, the group rows are always visible
            sheet.insertRule(".group-header {display: table-row-group;}");
        }
    }

    filter_requests_count();
}

function collapse_group(group_id, collapse) {
    if (collapse) {
        global.group_collapse.push(group_id);
    } else {
        let index = global.group_collapse.indexOf(group_id);
        if (index !== -1) {
            global.group_collapse.splice(index, 1);
        }
    }

    update_collapse_group();
}

function update_collapse_group() {
    var sheet = document.getElementById("collapsegroupcss").sheet;

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0);
    }

    for (let group_id of global.group_collapse) {
        sheet.insertRule('[data-group="' + group_id + '"] {display: none;}');
    }
}

function filter_requests_count() {
    var filter = document.getElementById("filter-url").value;
    var counter = document.getElementById("filter-requests-count");

    const nb_total = Object.keys(global.requests).length || 0;
    var nb_found = nb_total;    

    if (filter) {
        filter = prepare_for_filter(filter);
        var table = document.getElementById("requests-list");        
        nb_found = table.querySelectorAll('[data-filter*="' + filter + '"]').length;
    }

    counter.innerText = nb_found + "/" + nb_total + " requests";
}