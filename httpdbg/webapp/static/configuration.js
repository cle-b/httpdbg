"use strict";

function config() {
    if (document.getElementById("configuration").style.display == "block") {
        document.getElementById("configuration").style.display = "none";
    } else {
        document.getElementById("configuration").style.display = "block";
    }
}

function apply_config_rule_css(a_config, sheet) {
    document.getElementById(a_config.checkbox).checked = a_config.value;
    if (a_config.value) {
        sheet.insertRule(a_config.css);
    }
}

function apply_config_rule_click(a_config) {
    document.getElementById(a_config.checkbox).checked = a_config.value;
    document.getElementsByName(a_config.elt_name).forEach(element => {
        if (element.checked != a_config.value) {
            element.click();
        }
    });

}

function apply_config() {
    var sheet = document.getElementById("configurationcss").sheet;

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0);
    }

    apply_config_rule_css(httpdbgApp.config.hide_netloc, sheet);
    apply_config_rule_css(httpdbgApp.config.hide_group, sheet);
    apply_config_rule_css(httpdbgApp.config.hide_tag, sheet);

    apply_config_rule_click(httpdbgApp.config.details_wrap_default);
    apply_config_rule_click(httpdbgApp.config.details_raw_default);
}

function load_config_rule_from_url(a_config, params) {
    a_config.value = (params.get(a_config.param) || "off") == "on";
}

function load_config_from_url(apply) {
    const params = new URLSearchParams(window.location.search);

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
    a_config.value = document.getElementById(a_config.checkbox).checked;
}

function load_config_from_form(apply) {
    const params = new URLSearchParams(window.location.search);

    load_config_rule_from_form(httpdbgApp.config.hide_netloc);
    load_config_rule_from_form(httpdbgApp.config.hide_group);
    load_config_rule_from_form(httpdbgApp.config.hide_tag);
    load_config_rule_from_form(httpdbgApp.config.details_wrap_default);
    load_config_rule_from_form(httpdbgApp.config.details_raw_default);

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