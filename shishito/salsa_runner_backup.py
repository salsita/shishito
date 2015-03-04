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
from jinja2 import Environment, FileSystemLoader

from salsa_webqa.library.support.browserstack import BrowserStackAPI
from salsa_webqa.library.control_test import ControlTest


bs_api = BrowserStackAPI()


class SalsaRunner():
    """ Selenium Webdriver Python test runner.
    - runs python selenium tests on customizable configurations, locally or on BrowserStack using PyTest
    - checks for available BrowserStack sessions and wait if necessary
    - archive the test results in .zip file """

    def __init__(self, project_root):

        # set project root folder and current folder
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        self.project_root = project_root
        self.set_project_root()

        # set support variables
        self.tc = ControlTest()
        self.driver_name = self.tc.gid('driver')
        self.timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.result_folder = os.path.join(self.project_root, 'results', self.timestamp)

        # load configuration files
        if self.driver_name is not None:
            self.bs_config_file = os.path.join(self.project_root, 'config', 'browserstack.properties')
            self.bs_config_file_smoke = os.path.join(self.project_root, 'config', 'browserstack_smoke.properties')
            self.bs_config_file_mobile = os.path.join(self.project_root, 'config', 'browserstack_mobile.properties')
            self.config_file_appium = os.path.join(self.project_root, 'config', 'appium.properties')
            self.config = ConfigParser.RawConfigParser()
        self.bs_username = None
        self.bs_password = None
        self.jira_username = None
        self.jira_password = None
        # load credentials
        credentials = self.load_services_credentials()
        self.reporting = credentials['reporting']
        self.env_type = credentials['env_type']
        self.test_type = credentials['test_type']
        self.test_mobile = credentials['test_mobile']
        self.jira_username = credentials['jira_username']
        self.jira_password = credentials['jira_password']
        self.cycle_id = credentials['cycle_id']
        self.bs_username = credentials['bs_username']
        self.bs_password = credentials['bs_password']
        self.appium_platform = self.tc.gid('appium_platform')
        # check if configuration files are present
        if self.reporting != "simple" and self.driver_name is not None:
            if self.test_mobile == 'yes':
                if not (os.path.exists(self.bs_config_file_mobile)):
                    sys.exit('Browserstack mobile properties file not found! Session terminated.')
            else:
                if not (os.path.exists(self.bs_config_file)) or not (os.path.exists(self.bs_config_file_smoke)):
                    sys.exit('One of browserstack properties files not found! Session terminated.')
        if self.appium_platform:
            if not (os.path.exists(self.config_file_appium)):
                sys.exit('Appium properties file not found! Session terminated.')

    # TODO rename to clearer name which would show the purpose: parse cmd arguments
    def load_services_credentials(self):
        # load cmd arguments and set default values if not specified
        credentials = {}
        cmd_args = self.get_runner_args()
        credentials['reporting'] = cmd_args[0]
        credentials['env_type'] = cmd_args[1]
        credentials['test_type'] = cmd_args[2]
        credentials['test_mobile'] = cmd_args[3]
        credentials['jira_username'] = None
        credentials['jira_password'] = None
        credentials['cycle_id'] = None
        credentials['bs_username'] = None
        credentials['bs_password'] = None

        # load Jira credentials from cmd argument, if available
        if cmd_args[4] != 'none':
            # Jira support activated
            jira_auth = cmd_args[4].split(':')
            auth = (jira_auth[0], jira_auth[1])
            credentials['jira_username'] = jira_auth[0]
            credentials['jira_password'] = jira_auth[1]
            # create test cycle and remember it's id in env variable
            credentials['cycle_id'] = self.tc.create_cycle(self.tc.gid('jira_cycle_name'), auth)

        # load browserstack credentials from cmd argument, if available
        if cmd_args[5] != 'none':
            browserstack_auth = cmd_args[5].split(':')
            credentials['bs_username'] = browserstack_auth[0]
            credentials['bs_password'] = browserstack_auth[1]
        return credentials

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
            test_status = 0
            self.cleanup_results()
            if self.reporting == 'simple' or self.driver_name is None:
                test_status = self.trigger_pytest()
            elif self.reporting == 'all':
                if self.driver_name.lower() == 'browserstack':
                    test_status_selenium = self.run_on_browserstack()
                else:
                    test_status_selenium = self.run_locally()
                test_status_simple = self.trigger_pytest()
                test_status = max(test_status_selenium, test_status_simple)

            elif self.reporting == 'selenium':
                if self.driver_name.lower() == 'browserstack':
                    test_status = self.run_on_browserstack()
                else:
                    test_status = self.run_locally()
            self.archive_results()
            self.generate_combined_report()
            return test_status

    def run_on_browserstack(self):
        """ Runs tests on BrowserStack """
        test_status = 0
        # If password not provided in command line look ad server configuration file
        if self.bs_username is None:
            credentials = self.tc.gid('browserstack').split(':')
            self.bs_username = credentials[0]
            self.bs_password = credentials[1]
        if bs_api.wait_for_free_sessions((self.bs_username, self.bs_password),
                                         self.tc.gid('session_waiting_time'), self.tc.gid('session_waiting_delay')):
            # load browserstack variables from configuration files
            if self.env_type == 'versioned':
                if self.test_type == 'smoke':
                    self.config.read(self.bs_config_file_smoke)
                elif self.test_mobile == 'yes':
                    self.config.read(self.bs_config_file_mobile)
                else:
                    self.config.read(self.bs_config_file)
                for config_section in self.config.sections():
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
        print('Running for browser: ' + self.driver_name)
        return self.trigger_pytest(self.driver_name)

    def trigger_pytest(self, config_section=None):
        """ Runs PyTest runner on specific configuration """
        if config_section is None or self.reporting == 'simple':
            path = os.path.join(self.project_root, 'non_selenium_tests')
            print('Running non selenium tests')
            if not os.path.exists(path):
                print("Can't run non selenium tests files are not found")
                return None
            pytest_arguments = [os.path.join(self.project_root, 'non_selenium_tests'),
                                '--junitxml=' + os.path.join(self.result_folder, "Non_selenium_report" + '.xml'),
                                '--html=' + os.path.join(self.result_folder, "Non_selenium_report" + '.html')]
            return pytest.main(pytest_arguments)
        pytest_arguments = [os.path.join(self.project_root, 'tests')]
        # set pytest parallel execution argument
        parallel_tests = int(self.tc.gid('parallel_tests'))
        if parallel_tests > 1:
            pytest_arguments.extend(['-n', str(parallel_tests)])

        # set pytest smoke test argument
        if self.test_type == 'smoke':
            pytest_arguments.extend(['-m', self.test_type])

        if self.cycle_id:
            pytest_arguments.extend(['--jira_cycle_id', self.cycle_id])

        # setup pytest arguments for browserstack
        if self.driver_name.lower() == 'browserstack':
            # get arguments for running tests on mobile browsers
            if self.test_mobile == 'yes':
                pytest_arguments = self.get_pytest_arguments_mobile(config_section, pytest_arguments)
            # get arguments for running tests on desktop browsers
            elif self.appium_platform:
                pytest_arguments = self.get_pytest_arguments_appium(config_section, pytest_arguments)
            else:
                pytest_arguments = self.get_pytest_arguments_desktop(config_section, pytest_arguments)

        # setup pytest arguments for local browser
        else:
            pytest_arguments.append('--junitxml=' + os.path.join(self.result_folder, self.driver_name + '.xml'))
            pytest_arguments.append('--html=' + os.path.join(self.result_folder, self.driver_name + '.html'))

        # check if jira credentials are setup and add it to pytest
        if self.jira_username and self.jira_password:
            pytest_arguments.append('--jira_support=' + self.jira_username + ":" + self.jira_password)
        if self.bs_username and self.bs_password:
            pytest_arguments.append('--browserstack=' + self.bs_username + ":" + self.bs_password)

        # run pytest and return its exit code
        return pytest.main(pytest_arguments)

    def get_pytest_arguments_desktop(self, config_section, pytest_arguments):
        """ get pytest arguments to run tests on browserstack desktop browsers """
        # arguments passed through environment variable
        if self.env_type == 'direct':
            browser = config_section['browser']
            browser_version = config_section['browser_version']
            os_type = config_section['os']
            os_version = config_section['os_version']
            resolution = config_section['resolution']
            junit_xml_path = os.path.join(self.result_folder, browser + browser_version
                                          + os_type + os_version + resolution + '.xml')
            html_path = os.path.join(self.result_folder, browser + browser_version
                                     + os_type + os_version + resolution + '.html')
        # arguments passed through config file
        else:
            if self.test_type == 'smoke':
                self.config.read(self.bs_config_file_smoke)
            else:
                self.config.read(self.bs_config_file)
            browser = self.config.get(config_section, 'browser')
            browser_version = self.config.get(config_section, 'browser_version')
            os_type = self.config.get(config_section, 'os')
            os_version = self.config.get(config_section, 'os_version')
            resolution = self.config.get(config_section, 'resolution')
            junit_xml_path = os.path.join(self.result_folder, config_section + '.xml')
            html_path = os.path.join(self.result_folder, config_section + '.html')

        test_result_prefix = '[' + browser + ', ' + browser_version + ', ' + os_type \
                             + ', ' + os_version + ', ' + resolution + ']'

        # prepare pytest arguments into execution list
        pytest_arguments.extend([
            '--junitxml=' + junit_xml_path,
            '--junit-prefix=' + test_result_prefix,
            '--html=' + html_path,
            '--html-prefix=' + test_result_prefix,
            '--xbrowser=' + browser,
            '--xbrowserversion=' + browser_version,
            '--xos=' + os_type,
            '--xosversion=' + os_version,
            '--xresolution=' + resolution,
            '--instafail',
            '--test_mobile=no'])

        return pytest_arguments

    def get_pytest_arguments_mobile(self, config_section, pytest_arguments):
        """ get pytest arguments to run tests on browserstack mobile browsers """
        # arguments passed through environment variable
        if self.env_type == 'direct':
            browser_name = config_section['browserName']
            platform = config_section['platform']
            device = config_section['device']
            orientation = config_section['deviceOrientation']
            junit_xml_path = os.path.join(self.result_folder, browser_name + platform + device + orientation + '.xml')
            html_path = os.path.join(self.result_folder, browser_name + platform + device + orientation + '.html')
        # arguments passed through config file
        else:
            self.config.read(self.bs_config_file_mobile)
            browser_name = self.config.get(config_section, 'browserName')
            platform = self.config.get(config_section, 'platform')
            device = self.config.get(config_section, 'device')
            orientation = self.config.get(config_section, 'deviceOrientation')
            junit_xml_path = os.path.join(self.result_folder, config_section + '.xml')
            html_path = os.path.join(self.result_folder, config_section + '.html')

        test_result_prefix = '[' + device + ', ' + platform + ', ' + browser_name + ']'

        pytest_arguments.extend([
            '--junitxml=' + junit_xml_path,
            '--junit-prefix=' + test_result_prefix,
            '--html=' + html_path,
            '--html-prefix=' + test_result_prefix,
            '--xbrowserName=' + browser_name,
            '--xplatform=' + platform,
            '--xdevice=' + device,
            '--xdeviceOrientation=' + orientation,
            '--test_mobile=yes'])

        return pytest_arguments

    def get_pytest_arguments_appium(self, config_section, pytest_arguments):
        """ get pytest arguments to run tests on browserstack mobile browsers """
        # arguments passed through environment variable
        if self.env_type == 'direct':
            browser_name = config_section['browserName']
            platform = config_section['platform']
            device = config_section['device']
            orientation = config_section['deviceOrientation']
            junit_xml_path = os.path.join(self.result_folder, browser_name + platform + device + orientation + '.xml')
            html_path = os.path.join(self.result_folder, browser_name + platform + device + orientation + '.html')
        # arguments passed through config file
        else:
            self.config.read(self.bs_config_file_mobile)
            browser_name = self.config.get(config_section, 'browserName')
            platform = self.config.get(config_section, 'platform')
            device = self.config.get(config_section, 'device')
            orientation = self.config.get(config_section, 'deviceOrientation')
            junit_xml_path = os.path.join(self.result_folder, config_section + '.xml')
            html_path = os.path.join(self.result_folder, config_section + '.html')

        test_result_prefix = '[' + device + ', ' + platform + ', ' + browser_name + ']'

        pytest_arguments.extend([
            '--junitxml=' + junit_xml_path,
            '--junit-prefix=' + test_result_prefix,
            '--html=' + html_path,
            '--html-prefix=' + test_result_prefix,
            '--xbrowserName=' + browser_name,
            '--xplatform=' + platform,
            '--xdevice=' + device,
            '--xdeviceOrientation=' + orientation,
            '--test_mobile=yes'])

        return pytest_arguments

    def get_runner_args(self):
        # TODO pass those arguments to modules
        """ Retrieves the command line arguments passed to the script """
        parser = argparse.ArgumentParser(description='Selenium Python test runner execution arguments.')
        # TODO = rename this and allow to run test for each "module" ?
        parser.add_argument('--reporting',
                            help='Generate reports for non selenium non_selenium_tests;'
                                 'options: "all, selenium, simple"',
                            default='all')
        # TODO = possibly remove this option: is it even used? (too much complexity)
        parser.add_argument('--env',
                            help='BrowserStack environments; '
                                 'options: "direct" - passed as OS environment variable '
                                 '(JSON format), "versioned" (default) - loaded from *.properties configuration files',
                            default='versioned')
        # TODO = change this to just "smoke" and remove the smoke properties file (too much complexity)
        parser.add_argument('--tests',
                            help='Tests to run; options: "smoke", "all" (default)',
                            default='all')
        # TODO = possibly remove this and keep it just in config files (too much complexity)
        parser.add_argument('--mobile',
                            help='Run tests on mobile/tablets, "default:none"'
                                 'for running use "yes"',
                            default='none')
        parser.add_argument('--jira_support',
                            help='Jira credentials; format: "username:password',
                            default='none')
        parser.add_argument('--browserstack',
                            help='BrowserStack credentials; format: "username:token"',
                            default='none')

        args = parser.parse_args()
        return [args.reporting, args.env, args.tests, args.mobile, args.jira_support, args.browserstack]
