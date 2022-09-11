"use strict";

function config() {
    if (document.getElementById("configuration").style.display == "block") {
        document.getElementById("configuration").style.display = "none";
    } else {
        document.getElementById("configuration").style.display = "block";
    }
}

function apply_config_rule(a_config, sheet) {
    document.getElementById(a_config.checkbox).checked = a_config.value;
    if (a_config.value) {
        sheet.insertRule(a_config.css);
    }
}

function apply_config() {
    var sheet = document.getElementById("configurationcss").sheet;

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0);
    }

    apply_config_rule(httpdbgApp.config.hide_status, sheet);
    apply_config_rule(httpdbgApp.config.hide_method, sheet);
    apply_config_rule(httpdbgApp.config.hide_netloc, sheet);
    apply_config_rule(httpdbgApp.config.hide_initiator, sheet);
}

function load_config_rule_from_url(a_config, params) {
    a_config.value = (params.get(a_config.param) || "off") == "on";
}

function load_config_from_url(apply) {
    const params = new URLSearchParams(window.location.search);

    load_config_rule_from_url(httpdbgApp.config.hide_status, params);
    load_config_rule_from_url(httpdbgApp.config.hide_method, params);
    load_config_rule_from_url(httpdbgApp.config.hide_netloc, params);
    load_config_rule_from_url(httpdbgApp.config.hide_initiator, params);

    if (apply) {
        apply_config();
    }
}

function load_config_rule_from_form(a_config) {
    a_config.value = document.getElementById(a_config.checkbox).checked;
}

function load_config_from_form(apply) {
    const params = new URLSearchParams(window.location.search);

    load_config_rule_from_form(httpdbgApp.config.hide_status);
    load_config_rule_from_form(httpdbgApp.config.hide_method);
    load_config_rule_from_form(httpdbgApp.config.hide_netloc);
    load_config_rule_from_form(httpdbgApp.config.hide_initiator);

    if (apply) {
        apply_config();
    }
}

function save_config_to_url(hide_config_panel) {
    const formData = new FormData(document.forms[0]);
    const params = (new URLSearchParams(formData)).toString();
    history.replaceState("", "", "?" + params)

    if (hide_config_panel) {
        config();
    }
}