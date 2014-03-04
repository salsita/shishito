# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Author
"""
from unittestzero import Assert
import os
from library.lib_test_config import start_browser
from pages.sample_page import Products
# from library.ripple import switch_from_ripple_app, switch_to_ripple_app


class TestSample():
    """  Product page sample test """

    def setup_class(self):
        """ executes before test class starts """
        print('Test started')

    def teardown_class(self):
        """ executes after test class finishes """
        print('Test finished')

    def setup_method(self, method):
        """ executes before test function starts """
        self.testname = os.path.basename(__file__)[:-3]
        self.testcasename = "\n%s:%s" % (type(self).__name__, method.__name__)

        self.driver = start_browser(self, self.testname, self.testcasename)
        self.product_page = Products(self.driver)

    def teardown_method(self, method):
        """ executes after test function finishes """
        self.driver.quit()

    ### Tests ###

    def test_number_of_products(self):
        """ tests that number of products is as expected """
        Assert.equal(len(self.product_page.products, 8))

    def test_product_details(self):
        """ test details of specific product """
        product = self.product_page.get_product_by_name('Yellow Car')
        Assert.equal(product.product_color.text, 'yellow')
        Assert.equal(product.product_description, 'nicest yellow car you have ever seen')