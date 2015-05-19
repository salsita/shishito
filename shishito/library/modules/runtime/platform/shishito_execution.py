# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Selenium Webdriver Python test runner
"""

import os


class ShishitoExecution(object):
    """ """

    def __init__(self, shishito_support, test_timestamp):
        self.shishito_support = shishito_support

        environment_class = self.shishito_support.get_modules(module='test_environment')
        self.environment = environment_class(shishito_support)

        self.result_folder = os.path.join(self.shishito_support.project_root, 'results', test_timestamp)

    def run_tests(self):
        """ Triggers PyTest runner locally or on BrowserStack.
        It runs PyTest for each BS combination, taken from either versioned .properties file or environment variable """
        pass

    def trigger_pytest(self, config_section):
        """ Runs PyTest runner on specific configuration """
        pass
