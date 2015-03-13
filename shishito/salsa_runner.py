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

        # import execution class
        modules = self.select_modules()
        platform_path = 'shishito.library.modules.runtime.platform.' + modules['platform'] + '.control_execution'
        executor_class = getattr(import_module(platform_path), 'ControlExecution')
        executor = executor_class(modules['environment'])

        if __name__ == "__main__":
            sys.exit('The runner cannot be executed directly.'
                     ' You need to import it within project specific runner. Session terminated.')
        else:
            executor.run_tests()
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
        # default='local')
        args = parser.parse_args()

        # TODO hardcoded test data
        args.platform = 'web'
        args.environment = 'local'

        return {'platform': args.platform, 'environment': args.environment}


ShishitoRunner().run_tests()