# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common library for functions executing actions over Ripple Emulator UI (Mobile OS web emulator)
"""
import time

from selenium.webdriver.common.by import By


class TestRipple():

    def __init__(self, driver):
        self.driver = driver
        self.left_section_locator = (By.CSS_SELECTOR, '.left.sortable.main.ui-sortable')
        self.right_section_locator = (By.CSS_SELECTOR, '.right.sortable.main.ui-sortable')
        self.left_arrow_locator = (By.CSS_SELECTOR, '#ui > section.left-panel-collapse.ui-state-default.'
                                                    'ui-corner-all.ui-state-hover > span')
        self.right_arrow_locator = (By.CSS_SELECTOR, '#ui > section.right-panel-collapse.ui-state-default.'
                                                     'ui-corner-all.ui-state-hover > span')
        self.gps_header_locator = (By.CSS_SELECTOR, '#gps-container > section.h2.info-header > section.collapse-handle')
        self.gps_container_locator = (By.CSS_SELECTOR, '#gps-container > section.info.ui-widget-content.ui-corner-all')
        self.geo_latitude_locator = (By.ID, 'geo-latitude')
        self.geo_longitude_locator = (By.ID, 'geo-longitude')

    def prepare_for_testing(self):
        """ prepares Ripple Simulator for App testing """
        self.expand_left_section(False)
        self.expand_right_section(False)
        self.switch_to_ripple_app()

    def expand_left_section(self, expand=True):
        """ expands or hides left section of Ripple UI controls """
        left_section = self.driver.find_element(*self.left_section_locator)
        left_arrow = self.driver.find_element(*self.left_arrow_locator)
        if expand:
            if left_section.get_attribute('style') not in ('left: 0px; opacity: 1;', ''):
                left_arrow.click()
                time.sleep(2)
        else:
            if left_section.get_attribute('style') in ('left: 0px; opacity: 1;', ''):
                left_arrow.click()
                time.sleep(2)

    def expand_right_section(self, expand=True):
        """ expands or hides right section of Ripple UI controls """
        right_section = self.driver.find_element(*self.right_section_locator)
        right_arrow = self.driver.find_element(*self.right_arrow_locator)
        if expand:
            if right_section.get_attribute('style') not in ('right: 0px; opacity: 1;', ''):
                right_arrow.click()
                time.sleep(2)
        else:
            if right_section.get_attribute('style') in ('right: 0px; opacity: 1;', ''):
                right_arrow.click()
                time.sleep(2)

    def switch_to_ripple_app(self):
        """ switches to PhoneGap HMTL app iframe (so selenium can target elements inside it) """
        app_frame = self.driver.find_elements_by_tag_name('iframe')[0]
        self.driver.switch_to_frame(app_frame)

    def switch_from_ripple_app(self):
        """ switches into the default Ripple Emulator UI DOM (so selenium can target Ripple control elements) """
        self.driver.switch_to_default_content()

    def set_geo_location(self, lat, long):
        """ sets location to given coordinates """
        self.switch_from_ripple_app()
        self.expand_right_section(True)
        if not self.driver.find_element(*self.gps_container_locator).is_displayed():
            self.driver.find_element(*self.gps_header_locator).click()
            time.sleep(1)
        latitude = self.driver.find_element(*self.geo_latitude_locator)
        longitude = self.driver.find_element(*self.geo_longitude_locator)
        latitude.clear()
        longitude.clear()
        latitude.send_keys(str(lat))
        longitude.send_keys(str(long))
        self.expand_right_section(False)
        self.driver.refresh()
        self.switch_to_ripple_app()