from __future__ import absolute_import

from selenium import webdriver

from shishito.runtime.environment.shishito import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Node-webkit control environment. """

    def call_browser(self, config_section):
        """ Start chromedriver for node-webkit application. Chromedriver have to be located in same
        folder as node-webkit application (AUT).

        :param str config_section: section in platform/environment.properties config
        :return: created webdriver
        """
        capabilities = ''
        node_webkit = self.shishito_support.get_opt('app_path')

        if node_webkit is None:
            raise ValueError('Path to Chomedriver is empty, please check configuration file.')
        # get driver
        return self.start_driver(node_webkit, capabilities)

    def start_driver(self, node_webkit_path, capabilities):
        """ Prepare chromedriver for node-webkit application.

        :param capabilities: capabilities used for webdriver initialization
        :param node_webkit_path: path to node-webkit chromedriver located in same folder as node-webkit application
        """
        driver = webdriver.Chrome(node_webkit_path)

        return driver
