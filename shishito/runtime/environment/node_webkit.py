from __future__ import absolute_import

from selenium import webdriver
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
        capabilities = ''
        node_webkit = self.shishito_support.get_opt('app_path')

        if node_webkit is None:
            raise ValueError('Path to Chomedriver is not specified, please check configuration file.')
        # get driver
        return self.start_driver(node_webkit, capabilities)

    def is_correct_name_binary(self, node_webkit_path):
        """
        Method checks whether there exists properly named node-webkit binary in provided path to chromedrviver

        :param node_webkit_path: path to chromedriver
        :return: True if properly named node-webkit binary exists in given path, otherwise False
        """
        last_slash = node_webkit_path.rfind(os.path.sep)
        node_webkit_dir = node_webkit_path[:last_slash]
        aut_os = sys.platform

        if "linux" in aut_os:
            return os.path.exists(node_webkit_dir + os.path.sep + "nw")
        elif "os x" in aut_os:
            return os.path.exists(node_webkit_dir + os.path.sep + "node-webkit.app")
        elif "windows" in aut_os:
            return os.path.exists(node_webkit_dir + os.path.sep + "nw.exe")
        else:
            return False

    def start_driver(self, node_webkit_path, capabilities):
        """ Prepare chromedriver for node-webkit application.

        :param capabilities: capabilities used for webdriver initialization
        :param node_webkit_path: path to node-webkit chromedriver located in same folder as node-webkit application
        """
        if not self.is_correct_name_binary(node_webkit_path):
            raise ValueError(
                "Node-webkit binary has incorrect name. For more information see https://github.com/salsita/shishito#node-webkit-configuration")
        driver = webdriver.Chrome(node_webkit_path)

        return driver
