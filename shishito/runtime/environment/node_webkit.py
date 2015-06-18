from __future__ import absolute_import

from selenium import webdriver
import os
import sys
from shishito.runtime.environment.shishito import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Node-webkit control environment. """

    def call_browser(self):
        """ Start chromedriver for node-webkit application. Chromedriver have to be located in same
        folder as node-webkit application (AUT).

        :param str config_section: section in platform/environment.properties config
        :return: created webdriver
        """

        node_webkit_chromedriver_path = self.shishito_support.get_opt('node_webkit_chromedriver_path')

        if not node_webkit_chromedriver_path:
            raise ValueError('Path to Chomedriver is not specified, please check configuration file.')
        elif not self.is_correct_name_binary(node_webkit_chromedriver_path):
            raise ValueError(
                "Node-webkit binary has incorrect name or path to node-webkit binary does not exists, please check configuration file. "
                "For more information see https://github.com/salsita/shishito#node-webkit-configuration")
        # get driver
        return self.start_driver(node_webkit_chromedriver_path)

    def is_correct_name_binary(self, node_webkit_chromedriver_path):
        """
        Method checks whether there exists properly named node-webkit binary in provided path to chromedriver

        :param node_webkit_chromedriver_path: path to chromedriver
        :return: True if properly named node-webkit binary exists in given path, otherwise False
        """

        node_webkit_dir = os.path.split(node_webkit_chromedriver_path)[0]
        aut_os = sys.platform.lower()

        # check whether node-webkit apps are correct based on OS on which test are executed
        if "linux" in aut_os:
            return os.path.exists(os.path.join(node_webkit_dir, "nw"))
        elif "darwin" in aut_os:
            return os.path.exists(os.path.join(node_webkit_dir, "node-webkit.app"))
        elif "win" in aut_os:
            return os.path.exists(os.path.join(node_webkit_dir, "nw.exe"))
        else:
            return False

    def start_driver(self, node_webkit_chromedriver_path):
        """ Prepare chromedriver for node-webkit application.

        :param capabilities: capabilities used for webdriver initialization
        """

        driver = webdriver.Chrome(node_webkit_chromedriver_path)

        return driver
