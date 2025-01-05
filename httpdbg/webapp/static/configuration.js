"use strict";

function apply_config_rule_css(a_config, sheet) {
    document.getElementById(a_config.id).checked = a_config.value;
    if (a_config.value) {
        sheet.insertRule(a_config.css);
    }
}

function apply_config_rule_click(a_config) {
    document.getElementById(a_config.id).checked = a_config.value;
    document.getElementsByName(a_config.elt_name).forEach(element => {
        if (element.checked != a_config.value) {
            element.click();
        }
    });

}

function apply_config_rule(a_config, sheet) {
    document.getElementById(a_config.id).checked = a_config.value;
}

function apply_config_rule_select(a_config, sheet) {
    document.getElementById(a_config.id).value = a_config.value;
}

function apply_config() {
    var sheet = document.getElementById("configurationcss").sheet;

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0);
    }

    apply_config_rule(httpdbgApp.config.keep_previous_sessions);

    apply_config_rule_select(httpdbgApp.config.group_by);

    apply_config_rule_css(httpdbgApp.config.hide_netloc, sheet);
    apply_config_rule_css(httpdbgApp.config.hide_group, sheet);
    apply_config_rule_css(httpdbgApp.config.hide_tag, sheet);

    apply_config_rule_click(httpdbgApp.config.details_wrap_default);
    apply_config_rule_click(httpdbgApp.config.details_raw_default);
}

function load_config_rule_from_url(a_config, params) {
    if (a_config.type === "select") {
        a_config.value = params.get(a_config.param) || "default";
    } else {
        a_config.value = (params.get(a_config.param) || "off") == "on";
    }
}

function load_config_from_url(apply) {
    const params = new URLSearchParams(window.location.search);

    load_config_rule_from_url(httpdbgApp.config.keep_previous_sessions, params);
    load_config_rule_from_url(httpdbgApp.config.group_by, params);
    load_config_rule_from_url(httpdbgApp.config.hide_netloc, params);
    load_config_rule_from_url(httpdbgApp.config.hide_group, params);
    load_config_rule_from_url(httpdbgApp.config.hide_tag, params);
    load_config_rule_from_url(httpdbgApp.config.details_wrap_default, params);
    load_config_rule_from_url(httpdbgApp.config.details_raw_default, params);

    if (apply) {
        apply_config();
    }
}

function load_config_rule_from_form(a_config) {
    if (a_config.type === "select") {
        a_config.value = document.getElementById(a_config.id).value;
    } else {
        a_config.value = document.getElementById(a_config.id).checked;
    }
}

function load_config_from_form(apply) {
    const params = new URLSearchParams(window.location.search);

    load_config_rule_from_form(httpdbgApp.config.keep_previous_sessions);
    load_config_rule_from_form(httpdbgApp.config.group_by);
    load_config_rule_from_form(httpdbgApp.config.hide_netloc);
    load_config_rule_from_form(httpdbgApp.config.hide_group);
    load_config_rule_from_form(httpdbgApp.config.hide_tag);
    load_config_rule_from_form(httpdbgApp.config.details_wrap_default);
    load_config_rule_from_form(httpdbgApp.config.details_raw_default);

    if (apply) {
        apply_config();
    }

    save_config_to_url();
}

function save_config_to_url() {
    const formData = new FormData(document.forms[0]);
    const params = (new URLSearchParams(formData)).toString();
    history.replaceState("", "", "?" + params)
}