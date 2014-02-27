# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Author
"""
from selenium.webdriver.common.by import By
from pages.page_base import Page


class Products(Page):
    """ Sample Product page object (template) """

    def __init__(self, driver):
        Page.__init__(self, driver)
        self.driver = driver

        # page elements locators
        self._product_section = (By.CLASS_NAME, 'product-section')
        self._product_name_locator = (By.ID, 'some-element')

    @property
    def product_name(self):
        return self.driver.find_element(*self._product_name_locator)

    @property
    def products(self):
        return self.driver.find_elements(*self._product_section)

    def get_product_by_name(self, name):
        """ Returns Element object with name that matches supplied parameter value """
        products = self.driver.find_elements(*self._product_section)
        return_value = None
        for item in products:
            web_element = item.find_element(*self._product_name_locator)
            if web_element.text == name:
                return_value = self.ProductSection(item, self.driver)
                break
        return return_value

    class ProductSection(Page):
        """ Products Section web element object """

        def __init__(self, element, driver):
            Page.__init__(self, driver)
            self._root_element = element
            self._product_description_locator = (By.CSS_SELECTOR, 'div.place.ng-binding')
            self._product_color_locator = (By.ID, 'product-color')

        @property
        def product_description(self):
            return self.driver.find_element(*self._product_description_locator)

        @property
        def product_color(self):
            return self.driver.find_element(*self._product_color_locator)