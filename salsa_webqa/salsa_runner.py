# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Selenium Webdriver Python test runner
"""
import os
import ConfigParser
import sys
import time
import json
import shutil
import argparse

import pytest

from salsa_webqa.library.support.browserstack import BrowserStackAPI
from salsa_webqa.library.test_control import TestControl


bs_api = BrowserStackAPI()


class SalsaRunner():
    """ Selenium Webdriver Python test runner.
    - runs python selenium tests on customizable configurations, locally or on BrowserStack using PyTest
    - checks for available BrowserStack sessions and wait if necessary
    - archive the test results in .zip file """

    def __init__(self, project_root):
        # set project root folder
        self.project_root = project_root
        self.set_project_root()

        # set support variables
        self.tc = TestControl()
        self.driver_name = self.tc.gid('driver')
        self.timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.result_folder = os.path.join(self.project_root, 'results', self.timestamp)

        # load configuration files
        self.bs_config_file = os.path.join(self.project_root, 'config', 'browserstack.properties')
        self.bs_config_file_smoke = os.path.join(self.project_root, 'config', 'browserstack_smoke.properties')
        if not (os.path.exists(self.bs_config_file)) or not (os.path.exists(self.bs_config_file_smoke)):
            sys.exit('One of browserstack properties files not found! Session terminated.')
        self.bs_config = ConfigParser.RawConfigParser()

        # load cmd arguments and set default values if not specified
        cmd_args = self.get_runner_args()
        self.env_type = cmd_args[0]
        self.test_type = cmd_args[1]

    def set_project_root(self):
        """ Sets tested project root folder into OS environment variable """
        if os.path.exists(self.project_root) and os.path.isdir(self.project_root):
            os.environ['SALSA_WEBQA_PROJECT'] = self.project_root
        else:
            sys.exit('Project directory "' + self.project_root + '" does not exist! Session terminated.')

    def run_tests(self):
        """ Triggers PyTest runner locally or on BrowserStack.
        It runs PyTest for each BS combination, taken from either versioned .properties file or environment variable """
        # check that runner is not run directly
        if __name__ == "__main__":
            sys.exit('The runner cannot be executed directly.'
                     ' You need to import it within project specific runner. Session terminated.')
        else:
            if self.driver_name.lower() == 'browserstack':
                test_status = self.run_on_browserstack()
            else:
                test_status = self.run_locally()
            self.archive_results()
            return test_status

    def run_on_browserstack(self):
        """ Runs tests on BrowserStack """
        test_status = 0
        if bs_api.wait_for_free_sessions((self.tc.gid('bs_username'), self.tc.gid('bs_password')),
                                             self.tc.gid('session_waiting_time'), self.tc.gid('session_waiting_delay')):
            self.cleanup_results()

            # load browserstack variables from configuration files
            if self.env_type == 'versioned':
                if self.test_type == 'smoke':
                    self.bs_config.read(self.bs_config_file_smoke)
                else:
                    self.bs_config.read(self.bs_config_file)
                for config_section in self.bs_config.sections():
                    print('Running combination: ' + config_section)
                    test_status = self.trigger_pytest(config_section)

            # load browserstack variables from OS environment variable
            elif self.env_type == 'direct':
                config_list = json.loads(str(os.environ['BROWSERSTACK']))
                for config_section in config_list['test_suite']:
                    print('Running combination: ' + str(config_section))
                    test_status = self.trigger_pytest(config_section)
        return test_status

    def run_locally(self):
        """ Runs tests on local browser """
        self.cleanup_results()
        print('Running for browser: ' + self.driver_name)
        return self.trigger_pytest(self.driver_name)

    def trigger_pytest(self, config_section):
        """ Runs PyTest runner on specific configuration """
        pytest_arguments = [os.path.join(self.project_root, 'tests')]

        # set pytest parallel execution argument
        parallel_tests = int(self.tc.gid('parallel_tests'))
        if parallel_tests > 1:
            pytest_arguments.extend(['-n', str(parallel_tests)])

        # set pytest smoke test argument
        if self.test_type == 'smoke':
            pytest_arguments.extend(['-m', self.test_type])

        # setup pytest arguments for browserstack
        if self.driver_name.lower() == 'browserstack':

            # set pytest arguments values from OS environment variable
            if self.env_type == 'direct':
                browser = config_section['browser']
                browser_version = config_section['browser_version']
                os_type = config_section['os']
                os_version = config_section['os_version']
                resolution = config_section['resolution']
                junitxml_path = os.path.join(self.result_folder, browser + browser_version
                                             + os_type + os_version + resolution + '.xml')
                html_path = os.path.join(self.result_folder, browser + browser_version
                                         + os_type + os_version + resolution + '.html')

            # set pytest arguments values from configuration files
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
                junitxml_path = os.path.join(self.result_folder, config_section + '.xml')
                html_path = os.path.join(self.result_folder, config_section + '.html')
            test_result_prefix = '[' + browser + ', ' + browser_version + ', ' + os_type \
                                 + ', ' + os_version + ', ' + resolution + ']'

            # prepare pytest arguments into execution list
            pytest_arguments.extend([
                '--junitxml=' + junitxml_path,
                '--junit-prefix=' + test_result_prefix,
                '--html=' + html_path,
                '--html-prefix=' + test_result_prefix,
                '--xbrowser=' + browser,
                '--xbrowserversion=' + browser_version,
                '--xos=' + os_type,
                '--xosversion=' + os_version,
                '--xresolution=' + resolution,
                '--instafail'])

        # setup pytest arguments for local browser
        else:
            pytest_arguments.append('--junitxml=' + os.path.join(self.result_folder, self.driver_name + '.xml'))
            pytest_arguments.append('--html=' + os.path.join(self.result_folder, self.driver_name + '.html'))

        # run pytest and return its exit code
        return pytest.main(pytest_arguments)

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
        if os.path.exists(os.path.join(self.project_root, 'results')):
            shutil.rmtree(os.path.join(self.project_root, 'results'))
        os.makedirs(self.result_folder)

    def archive_results(self):
        """ Archives test results in zip package """
        archive_folder = os.path.join(self.project_root, 'results_archive')
        if not (os.path.exists(archive_folder)):
            os.makedirs(archive_folder)
        shutil.make_archive(os.path.join(archive_folder, self.timestamp), "zip", os.path.join(self.project_root, 'results'))