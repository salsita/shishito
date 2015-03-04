# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Selenium Webdriver Python test runner
"""
import os
import ConfigParser
import time
import argparse

import pytest

from shishito.library.modules.reporting.reporter import Reporter
from shishito.library.modules.runtime.environment.local.environment_control import EnvironmentControl
from shishito.library.modules.runtime.shishito_support import ShishitoSupport


class ControlExecution():
    """ """

    def __init__(self):

        self.module_name = 'web'
        self.shishito_support = ShishitoSupport()
         # TODO this will have to passed as argument to constructor (not through pytest, pytest not yet triggered at this point)
        self.environment = EnvironmentControl()

        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.getcwd()

        self.reporter = Reporter()

        self.timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.result_folder = os.path.join(self.project_root, 'results', self.timestamp)
        self.config_file = os.path.join(self.project_root, 'config', self.module_name,
                                        self.environment.module_name + '.properties')
        self.config = ConfigParser.RawConfigParser()
        # self.arguments = self.get_runner_args()

    def run_tests(self):
        """ Triggers PyTest runner locally or on BrowserStack.
        It runs PyTest for each BS combination, taken from either versioned .properties file or environment variable """
        # check that runner is not run directly
        test_status = 0
        self.config.read(self.config_file)
        for config_section in self.config.sections():
            print('Running combination: ' + config_section)
            test_status = self.trigger_pytest(config_section)
        return test_status

    def trigger_pytest(self, config_section):
        """ Runs PyTest runner on specific configuration """
        self.config.read(self.config_file)
        browser = self.config.get(config_section, 'browser')
        browser_version = self.config.get(config_section, 'browser_version')
        resolution = self.config.get(config_section, 'resolution')
        junit_xml_path = os.path.join(self.result_folder, config_section + '.xml')
        html_path = os.path.join(self.result_folder, config_section + '.html')

        test_result_prefix = '[' + browser + ', ' + browser_version + ', ' + resolution + ']'

        # prepare pytest arguments into execution list
        pytest_arguments = [os.path.join(self.project_root, 'tests'),
                            '--junitxml=' + junit_xml_path,
                            '--junit-prefix=' + test_result_prefix,
                            '--html=' + html_path,
                            '--html-prefix=' + test_result_prefix,
                            '--instafail']

        # set pytest parallel execution argument
        parallel_tests = int(self.shishito_support.gid('parallel_tests'))
        if parallel_tests > 1:
            pytest_arguments.extend(['-n', str(parallel_tests)])

        # # set pytest smoke test argument
        # if self.arguments['test_type'] == 'smoke':
        #     pytest_arguments.extend(['-m', self.arguments['test_type']])

        # if self.cycle_id:
        # pytest_arguments.extend(['--jira_cycle_id', self.cycle_id])

        return pytest.main(pytest_arguments)

    def get_runner_args(self):
        """ Retrieves the command line arguments passed to the script """
        parser = argparse.ArgumentParser(description='Selenium Python test runner execution arguments.')
        # TODO = change this to just "smoke" and remove the smoke properties file (too much complexity)
        parser.add_argument('--tests',
                            help='Tests to run; options: "smoke", "all" (default)',
                            default='all')
        # TODO = possibly remove this and keep it just in config files (too much complexity)
        parser.add_argument('--jira_support',
                            help='Jira credentials; format: "username:password',
                            default='none')

        args = parser.parse_args()
        return {'tests': args.tests, 'jira_support': args.jira_support}
