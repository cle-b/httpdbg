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
        sheet.insertRule(".initiator-header {display: table-row-group;}");
    } else {
        // if there is a filter, only the requests that match the filter are visible
        sheet.insertRule('[data-filter*="' + value + '"] {display: table-row;}');
        if (CSS.supports("selector(:has(*))")) {
            // an initiator row is visible only if it contains at least one visible request
            sheet.insertRule('.initiator-header:has([data-filter*="' + value + '"]) {display: table-row-group;}');
            // if there is a filter and no request visible, the filter icon is red
            sheet.insertRule('.requests-table:not(:has([data-filter*="' + value + '"])):has(tbody) .icon-filter {filter: grayscale(0%) !important;}');
        } else {
            // in case :has is not supported, the initiator rows are always visible
            sheet.insertRule(".initiator-header {display: table-row-group;}");
        }
    }

    filter_requests_count();
}

function collapse_initiator(initiator_id, collapse) {
    if (collapse) {
        global.initiator_collapse.push(initiator_id);
    } else {
        let index = global.initiator_collapse.indexOf(initiator_id);
        if (index !== -1) {
            global.initiator_collapse.splice(index, 1);
        }
    }

    update_collapse_initiator();
}

function update_collapse_initiator() {
    var sheet = document.getElementById("collapseinitiatorcss").sheet;

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0);
    }

    for (let initiator_id of global.initiator_collapse) {
        sheet.insertRule('[data-initiator="' + initiator_id + '"] {display: none;}');
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