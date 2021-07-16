"use strict";

function wait_for(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
