"""
@author: Vojtech Burian
@summary: Selenium Webdriver Python test runner
"""

import argparse
import sys
import time

from shishito.reporting.reporter import Reporter
from shishito.runtime.shishito_support import ShishitoSupport
from shishito.services.testrail_api import TestRail
from shishito.services.qastats_api import QAStats

class ShishitoRunner(object):
    """ Base shishito test runner.

    - runs python selenium tests on customizable configurations (using PyTest)
    - archive the test results in .zip file """

    def __init__(self, project_root):
        # set project root
        self.project_root = project_root

        # test timestamp - for storing results
        self.test_timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.epoch = int(time.time())

        # parse cmd  args
        self.cmd_args = self.handle_cmd_args()

        # Get SUT build for use in reporting
        self.test_build = self.cmd_args['build']

        self.reporter = Reporter(project_root, self.test_timestamp)
        self.shishito_support = ShishitoSupport(
            cmd_args=self.cmd_args,
            project_root=self.project_root
        )

    def handle_cmd_args(self):
        """ Retrieve command line arguments passed to the script.

        :return: dict with parsed command line arguments
        """

        parser = argparse.ArgumentParser(description='Selenium Python test runner execution arguments.')

        parser.add_argument('--platform',
                            help='Platform on which run tests.',
                            dest='test_platform')
        parser.add_argument('--environment',
                            help='Environment for which run tests.',
                            dest='test_environment')
        parser.add_argument('--test_directory',
                            help='Directory where to lookup for tests')
        parser.add_argument('--smoke',
                            help='Run only smoke tests',
                            action='store_true')
        parser.add_argument('--browserstack',
                            help='BrowserStack credentials; format: "username:token"')
        parser.add_argument('--saucelabs',
                            help='Saucelabs credentials; format: "username:token"')
        parser.add_argument('--test_rail',
                            help='TestRail Test Management tool credentials; format: "username:password"')
        parser.add_argument('--qastats',
                            help='QAStats Test Management tool credentials; format: "token"')
        parser.add_argument('--node_webkit_chromedriver_path',
                            help='Path to chromedriver located in same directory as node-webkit application')
        parser.add_argument('--app',
                            help='Path to appium application')
        parser.add_argument('--test',
                            help='Run specified test (PyTest string expression)')
        parser.add_argument('--build',
                            help='Specify build number for reporting purposes')
        parser.add_argument('--maxfail',
                            help='stop after x failures')
        args = parser.parse_args()

        # return args dict --> for use in other classes
        return vars(args)

    def run_tests(self):
        """ Execute tests for given platform and environment. Platform and Environment can be passed as command lines
        argument or settings in config file.
        """

        if __name__ == "__main__":
            sys.exit('The runner cannot be executed directly.'
                     ' You need to import it within project specific runner. Session terminated.')

        # cleanup previous results
        self.reporter.cleanup_results()

        # import execution class
        executor_class = self.shishito_support.get_module('platform_execution')
        # executor_class = getattr(import_module(platform_path), 'ControlExecution')
        executor = executor_class(self.shishito_support, self.test_timestamp)

        # run test
        exit_code = executor.run_tests()

        # archive results + generate combined report
        self.reporter.archive_results()
        self.reporter.generate_combined_report()

        # upload results to QAStats test management app
        qastats_credentials = self.shishito_support.get_opt('qastats')
        if qastats_credentials:
            try:
                qas_user, qas_password = qastats_credentials.split(':', 1)
            except (AttributeError, ValueError):
                raise ValueError('QAStats credentials were not specified! Unable to connect to QAStats.')

            qastats = QAStats(qas_user, qas_password, self.test_timestamp, self.epoch, self.test_build)
            qastats.post_results()

        # upload results to TestRail test management app
        test_rail_credentials = self.shishito_support.get_opt('test_rail')
        if test_rail_credentials:
            try:
                tr_user, tr_password = test_rail_credentials.split(':', 1)
            except (AttributeError, ValueError):
                raise ValueError('TestRail credentials were not specified! Unable to connect to TestRail.')

            test_rail = TestRail(tr_user, tr_password, self.test_timestamp, self.test_build)
            test_rail.post_results()

        return exit_code
