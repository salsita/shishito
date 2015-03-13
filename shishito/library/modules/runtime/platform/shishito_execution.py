# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Selenium Webdriver Python test runner
"""
import inspect
import os
import ConfigParser
import time
import sys

from shishito.library.modules.reporting.reporter import Reporter
from shishito.library.modules.runtime.shishito_support import ShishitoSupport


class ShishitoExecution(object):
    """ """

    def __init__(self, environment_name):

        self.current_folder = os.path.dirname(os.path.abspath(__file__))

        # TODO = define platform name from parent path (ugly implementation)
        # self.platform_name = os.path.split(self.current_folder)[-1]
        self.platform_name = os.path.split(os.path.dirname(inspect.getsourcefile(sys._getframe(1))))[-1]

        # define module names
        self.environment_name = environment_name
        self.shishito_support = ShishitoSupport()

        # environment had to passed as argument to constructor (not through pytest - not yet triggered here)
        self.environment = self.shishito_support.get_modules(self.platform_name, self.environment_name)[
            'test_environment']()

        # TODO this may not work well if runner is not used
        self.project_root = os.getcwd()
        self.reporter = Reporter()

        self.timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.result_folder = os.path.join(self.project_root, 'results', self.timestamp)
        self.config_file = os.path.join(self.project_root, 'config', self.platform_name,
                                        self.environment_name + '.properties')
        self.config = ConfigParser.RawConfigParser()

    def run_tests(self):
        """ Triggers PyTest runner locally or on BrowserStack.
        It runs PyTest for each BS combination, taken from either versioned .properties file or environment variable """
        pass

    def trigger_pytest(self, config_section):
        """ Runs PyTest runner on specific configuration """
        pass

    def get_runner_args(self):
        """ Retrieves the command line arguments passed to the script """
        pass