from __future__ import absolute_import

from selenium import webdriver
from selenium.webdriver.chrome import options
import os
import sys
from shishito.runtime.environment.shishito import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Node-webkit control environment. """

    def call_browser(self, config_section):
        """ Start chromedriver for node-webkit application. Chromedriver have to be located in same
        folder as node-webkit application (AUT).

        :param str config_section: section in platform/environment.properties config
        :return: created webdriver
        """
        node_webkit_chromedriver_path = self.shishito_support.get_opt('node_webkit_chromedriver_path')
        if not node_webkit_chromedriver_path:
            raise ValueError('Path to Chomedriver is not specified, please check configuration file.')

        binary_location = self.shishito_support.get_opt(config_section, 'binary_location')
        if not binary_location:
            raise ValueError('Path "binary_location" of the binary being tested not specified, please check: config/node_webkit/*.properties')

        chrome_options = options.Options()
        chrome_options.binary_location = binary_location

        # get driver
        return self.start_driver(node_webkit_chromedriver_path, chrome_options)



    def start_driver(self, node_webkit_chromedriver_path, chrome_options):
        """ Prepare chromedriver for node-webkit application.

        :param capabilities: capabilities used for webdriver initialization
        """

        driver = webdriver.Chrome(node_webkit_chromedriver_path, chrome_options = chrome_options)

        return driver
