# -*- coding: utf-8 -*-
from selenium.webdriver.common.by import By


class LPRequest(object):
    class SELECTORS:
        @staticmethod
        def ROOT_BY_ID(id):
            return (By.CSS_SELECTOR, f'[data-qa-request="{id}"]')

        STATUS = (By.CSS_SELECTOR, "[data-qa-request-status]")
        METHOD = (By.CSS_SELECTOR, "[data-qa-request-method]")
        URL = (By.CSS_SELECTOR, "[data-qa-request-url]")

    def __init__(self, parent, id):
        self.elt = parent.find_element(*self.SELECTORS.ROOT_BY_ID(id)).wait()

    @property
    def status(self):
        return self.elt.find_element(*self.SELECTORS.STATUS).text

    @property
    def method(self):
        return self.elt.find_element(*self.SELECTORS.METHOD).text

    @property
    def url(self):
        return self.elt.find_element(*self.SELECTORS.URL).text


class PanelRequests(object):
    class SELECTORS:
        ROOT = (By.CSS_SELECTOR, "[data-qa-panelrequests]")
        REQUEST = (By.CSS_SELECTOR, "[data-qa-request]")

        @staticmethod
        def REQUEST_BY_ID(id):
            return (By.CSS_SELECTOR, f'[data-qa-request="{id}"]')

    def __init__(self, parent):
        self.elt = parent.find_element(*self.SELECTORS.ROOT).wait()

    def __len__(self):
        total = 0
        elts = self.elt.find_elements(*self.SELECTORS.REQUEST)
        for elt in elts:
            if elt.is_displayed():
                total += 1
        return total

    def __contains__(self, id):
        elts = self.elt.find_elements(*self.SELECTORS.REQUEST_BY_ID(id))
        return (len(elts) == 1) and elts[0].is_displayed()

    def __getitem__(self, id):
        return LPRequest(self.elt, id)


class HttpdbgWebUI(object):
    def __init__(self, url, driver):
        self.url = url
        self.driver = driver
        self.driver.get(url)
        elt_body = self.driver.find_element(By.CSS_SELECTOR, "body")
        self.requests = PanelRequests(elt_body)
