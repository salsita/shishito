# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common library for functions executing actions over Ripple Emulator UI (Mobile OS web emulator)
"""
import time

from selenium.webdriver.common.by import By


class TestRipple(object):

    def __init__(self, driver):
        self.driver = driver
        self.section_locator = (By.CSS_SELECTOR, '.%s.sortable.main.ui-sortable')
        self.arrow_locator = (
            By.CSS_SELECTOR,
            '#ui > section.%s-panel-collapse.ui-state-default.ui-corner-all.ui-state-hover > span')
        self.gps_header_locator = (By.CSS_SELECTOR, '#gps-container > section.h2.info-header > section.collapse-handle')
        self.gps_container_locator = (By.CSS_SELECTOR, '#gps-container > section.info.ui-widget-content.ui-corner-all')
        self.geo_latitude_locator = (By.ID, 'geo-latitude')
        self.geo_longitude_locator = (By.ID, 'geo-longitude')

    def prepare_for_testing(self):
        """ prepares Ripple Simulator for App testing """
        self.expand_section('left', False)
        self.expand_section('right', False)
        self.switch_to_ripple_app()

    def expand_section(self, side, expand=True):
        section = self.driver.find_element(self.section_locator[0], self.section_locator[1] % side)
        arrow = self.driver.find_element(self.arrow_locator[0], self.arrow_locator[1] % side)
        contains = section.get_attribute('style') in ('left: 0px; opacity: 1;', '')
        if expand != contains:
            arrow.click()
            time.sleep(2)

    def switch_to_ripple_app(self):
        """ switches to PhoneGap HMTL app iframe (so selenium can target elements inside it) """
        app_frame = self.driver.find_elements_by_tag_name('iframe')[0]
        self.driver.switch_to_frame(app_frame)

    def switch_from_ripple_app(self):
        """ switches into the default Ripple Emulator UI DOM (so selenium can target Ripple control elements) """
        self.driver.switch_to_default_content()

    def set_geo_location(self, lat, lng):
        """ sets location to given coordinates """
        self.switch_from_ripple_app()
        self.expand_section('right', True)
        if not self.driver.find_element(*self.gps_container_locator).is_displayed():
            self.driver.find_element(*self.gps_header_locator).click()
            time.sleep(1)
        latitude = self.driver.find_element(*self.geo_latitude_locator)
        longitude = self.driver.find_element(*self.geo_longitude_locator)
        latitude.clear()
        longitude.clear()
        latitude.send_keys(str(lat))
        longitude.send_keys(str(lng))
        self.expand_section('right', False)
        self.driver.refresh()
        self.switch_to_ripple_app()
