# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Author
"""
from unittestzero import Assert
from library.lib_selenium import save_screenshot
from library.lib_test_config import start_browser, stop_browser, start_test
from pages.sample_page import Products
import pytest


class TestSample():
    """  Product page sample test """

    def setup_class(self):
        """ executes before test class starts """
        self.driver = start_browser(self)

        self.product_page = Products(self.driver)

    def teardown_class(self):
        """ executes after test class finishes """
        stop_browser(self)

    def setup_method(self, method):
        """ executes before test function starts """
        start_test(self)

    def teardown_method(self, method):
        """ executes after test function finishes """
        save_screenshot(self, method.__name__)

    ### Tests ###

    def test_page_title(self):
        Assert.equal(self.driver.title, 'Some expected title')

    @pytest.mark.smoke
    def test_only_when_smoke(self):
        Assert.not_equal(self.driver.title, 'Some unexpected title')

        # DUMMY TESTS USING SAMPLE PAGE OBJECT
        # ------------------------------------
        # def test_number_of_products(self):
        #     """ tests that number of products is as expected """
        #     Assert.equal(len(self.product_page.products), 8)
        #
        # def test_product_details(self):
        #     """ test details of specific product """
        #     product = self.product_page.get_product_by_name('Yellow Car')
        #     Assert.equal(product.product_color.text, 'yellow')
        #     Assert.equal(product.product_description, 'nicest yellow car you have ever seen')