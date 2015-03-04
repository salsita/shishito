# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Selenium Webdriver Python test runner
"""
import argparse
from importlib import import_module
import sys

from shishito.library.modules.reporting.reporter import Reporter


class ShishitoRunner():
    """ Selenium Webdriver Python test runner.
    - runs python selenium tests on customizable configurations, locally or on BrowserStack using PyTest
    - checks for available BrowserStack sessions and wait if necessary
    - archive the test results in .zip file """

    def __init__(self):
        self.reporter = Reporter()

    def run_tests(self):
        self.reporter.cleanup_results()
        modules = self.select_modules()
        executor_class = getattr(modules['platform'], 'ControlExecution')
        executor = executor_class()
        if __name__ == "__main__":
            sys.exit('The runner cannot be executed directly.'
                     ' You need to import it within project specific runner. Session terminated.')
        else:
            executor.run_tests() # TODO need to pass the "environment module" so executor can store it in pytest variable
        self.reporter.archive_results()
        self.reporter.generate_combined_report()

    def select_modules(self):
        """ Retrieves the command line arguments passed to the script """
        parser = argparse.ArgumentParser(description='Selenium Python test runner execution arguments.')
        # parser.add_argument('--platform',
        # help='',
        # default='web')
        # parser.add_argument('--environment',
        # help='',
        #                     default='local')
        args = parser.parse_args()

        # TODO hardcoded test data
        args.platform = 'web'
        args.environment = 'local'

        platform_path = 'shishito.library.modules.runtime.platform.' + args.platform + '.control_execution'
        environment_path = 'shishito.library.modules.runtime.environment.' + args.environment + '.environment_control'
        selected_platform = import_module(platform_path)
        selected_environment = import_module(environment_path)

        return {'platform': selected_platform, 'environment': selected_environment}


ShishitoRunner().run_tests()