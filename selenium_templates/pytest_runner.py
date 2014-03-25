# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Selenium Webdriver Python test runner
"""
import pytest
import os
import ConfigParser
from library.browserstack_api import BrowserStackAPI
from library.lib_test_config import gid
import sys
import time
import json
import shutil
import argparse

bs_api = BrowserStackAPI()


class PyTestRunner():
    """ Selenium Webdriver Python test runner.
    - runs python selenium tests on customizable configurations, locally or on BrowserStack using PyTest
    - checks for available BrowserStack sessions and wait if necessary
    - archive the test results in .zip file """

    def __init__(self):
        # set support variables
        self.dir_path = os.path.dirname(os.path.abspath(__file__))
        self.driver_name = gid('driver')
        self.timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.result_folder = self.dir_path + '/results/' + self.timestamp

        # load configuration files
        self.bs_config_file = self.dir_path + '/config/browserstack.properties'
        self.bs_config_file_smoke = self.dir_path + '/config/browserstack_smoke.properties'
        if not (os.path.exists(self.bs_config_file)) or not (os.path.exists(self.bs_config_file_smoke)):
            sys.exit('One of browserstack properties files not found! Session terminated.')
        self.bs_config = ConfigParser.RawConfigParser()

        # load cmd arguments and set default values if not specified
        cmd_args = self.get_runner_args()
        self.env_type = cmd_args[0]
        self.test_type = cmd_args[1]

    def run_tests(self):
        """ Triggers PyTest runner locally or on BrowserStack.
        It runs PyTest for each BS combination, taken from either versioned .properties file or environment variable """
        if self.driver_name.lower() == 'browserstack':
            if bs_api.wait_for_free_sessions((gid('bs_username'), gid('bs_password')),
                                             gid('session_waiting_time'), gid('session_waiting_delay')):
                self.cleanup_results()
                if self.env_type == 'versioned':
                    if self.test_type == 'smoke':
                        self.bs_config.read(self.bs_config_file_smoke)
                    else:
                        self.bs_config.read(self.bs_config_file)
                    for config_section in self.bs_config.sections():
                        print('Running combination: ' + config_section)
                        self.trigger_pytest(config_section)
                elif self.env_type == 'direct':
                    config_list = json.loads(str(os.environ['BROWSERSTACK']))
                    for config_section in config_list['test_suite']:
                        print('Running combination: ' + str(config_section))
                        self.trigger_pytest(config_section)
        else:
            self.cleanup_results()
            config_section = self.driver_name
            print('Running for browser: ' + config_section)
            self.trigger_pytest(config_section)
        self.archive_results()

    def trigger_pytest(self, config_section):
        """ Runs PyTest runner on specific configuration """
        pytest_arguments = [self.dir_path + '/tests']
        parallel_tests = int(gid('parallel_tests'))
        if parallel_tests > 1:
            pytest_arguments.extend(['-n', str(parallel_tests)])
        if self.test_type == 'smoke':
            pytest_arguments.extend(['-m', self.test_type])
        if self.driver_name.lower() == 'browserstack':
            if self.env_type == 'direct':
                browser = config_section['browser']
                browser_version = config_section['browser_version']
                os_type = config_section['os']
                os_version = config_section['os_version']
                resolution = config_section['resolution']
                junitxml_path = self.result_folder + '/' + browser + browser_version + os_type + os_version + resolution

            else:
                if self.test_type == 'smoke':
                    self.bs_config.read(self.bs_config_file_smoke)
                else:
                    self.bs_config.read(self.bs_config_file)

                browser = self.bs_config.get(config_section, 'browser')
                browser_version = self.bs_config.get(config_section, 'browser_version')
                os_type = self.bs_config.get(config_section, 'os')
                os_version = self.bs_config.get(config_section, 'os_version')
                resolution = self.bs_config.get(config_section, 'resolution')
                junitxml_path = self.result_folder + '/' + config_section

            test_result_prefix = '[' + browser + ', ' + browser_version + ', ' + os_type \
                                 + ', ' + os_version + ', ' + resolution + ']'

            pytest_arguments.extend([
                '--junitxml=' + junitxml_path,
                '--junit-prefix=' + test_result_prefix,
                '--xbrowser=' + browser,
                '--xbrowserversion=' + browser_version,
                '--xos=' + os_type,
                '--xosversion=' + os_version,
                '--xresolution=' + resolution,
                '--instafail'])
        else:
            pytest_arguments.append('--junitxml=' + self.result_folder + '/' + self.driver_name)

        pytest.main(pytest_arguments)

    def get_runner_args(self):
        """ Retrieves the command line arguments passed to the script """
        parser = argparse.ArgumentParser(description='Selenium Python test runner execution arguments.')
        parser.add_argument('--env',
                            help='BrowserStack environments; '
                                 'options: "direct" - passed as OS environment variable '
                                 '(JSON format), "versioned" (default) - loaded from *.properties configuration files',
                            default='versioned')
        parser.add_argument('--tests',
                            help='Tests to run; options: "smoke", "all" (default)',
                            default='all')
        args = parser.parse_args()
        return [args.env, args.tests]

    def cleanup_results(self):
        """ Cleans up test result folder """
        if os.path.exists(self.dir_path + '/results'):
            shutil.rmtree(self.dir_path + '/results')
        os.makedirs(self.result_folder)

    def archive_results(self):
        """ Archives test results in zip package """
        archive_folder = self.dir_path + '/results_archive'
        if not (os.path.exists(archive_folder)):
            os.makedirs(archive_folder)
        shutil.make_archive(archive_folder + '/' + self.timestamp, "zip", self.dir_path + '/results')


test_runner = PyTestRunner()
test_runner.run_tests()