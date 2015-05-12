# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Selenium Webdriver Python test runner
"""

import argparse
import sys

from shishito.library.modules.reporting.reporter import Reporter
from shishito.library.modules.runtime.shishito_support import ShishitoSupport


class ShishitoRunner(object):
    """ Selenium Webdriver Python test runner.
    - runs python selenium tests on customizable configurations, locally or on BrowserStack using PyTest
    - checks for available BrowserStack sessions and wait if necessary
    - archive the test results in .zip file """

    def __init__(self, project_root):
        # set project root
        self.project_root = project_root

        # parse cmd  args
        self.cmd_args = self.handle_cmd_args()

        self.reporter = Reporter(project_root)
        self.shishito_support = ShishitoSupport(
            cmd_args=self.cmd_args,
            project_root=self.project_root
        )

    def handle_cmd_args(self):
        """ Retrieves the command line arguments passed to the script """

        parser = argparse.ArgumentParser(description='Selenium Python test runner execution arguments.')

        parser.add_argument('--platform',
                            help='Platform on which run tests.',
                            dest='test_platform')
        parser.add_argument('--environment',
                            help='Environment for which run tests.',
                            dest='test_environment')
        parser.add_argument('--smoke',
                            help='Run only smoke tests',
                            action='store_true')
        parser.add_argument('--browserstack',
                            help='BrowserStack credentials; format: "username:token"',
                            default='none')

        args = parser.parse_args()

        # return args dict --> for use in other classes
        return vars(args)

    def run_tests(self):
        if __name__ == "__main__":
            sys.exit('The runner cannot be executed directly.'
                     ' You need to import it within project specific runner. Session terminated.')

        # cleanup previous results
        self.reporter.cleanup_results()

        # import execution class
        executor_class = self.shishito_support.get_modules(module='platform_execution')
        # executor_class = getattr(import_module(platform_path), 'ControlExecution')
        executor = executor_class(self.shishito_support)

        # run test
        executor.run_tests()

        # archive results + generate combined report
        self.reporter.archive_results()
        self.reporter.generate_combined_report()
