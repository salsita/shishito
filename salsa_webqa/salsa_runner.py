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
        self.bs_config_file = os.path.join(self.project_root, 'config', 'browserstack.properties')
        self.bs_config_file_smoke = os.path.join(self.project_root, 'config', 'browserstack_smoke.properties')
        self.bs_config_file_mobile = os.path.join(self.project_root, 'config', 'browserstack_mobile.properties')
        self.bs_config = ConfigParser.RawConfigParser()

        # load cmd arguments and set default values if not specified
        cmd_args = self.get_runner_args()
        self.env_type = cmd_args[0]
        self.test_type = cmd_args[1]
        self.test_mobile = cmd_args[2]
        self.jira_username = cmd_args[3]
        self.jira_password = cmd_args[4]
        os.environ['jira_username'] = self.jira_username
        os.environ['jira_password'] = self.jira_password

        os.environ["test_mobile"] = self.test_mobile
        # load browserstack credentials from cmd argument, if available
        if cmd_args[5] != 'none':
            browserstack_auth = cmd_args[5].split(':')
            os.environ['bs_username'] = browserstack_auth[0]
            os.environ['bs_password'] = browserstack_auth[1]

        # check if configuration files are present
        if self.test_mobile == 'yes':
            if not (os.path.exists(self.bs_config_file_mobile)):
                sys.exit('Browserstack mobile properties file not found! Session terminated.')
        else:
            if not (os.path.exists(self.bs_config_file)) or not (os.path.exists(self.bs_config_file_smoke)):
                sys.exit('One of browserstack properties files not found! Session terminated.')

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
            self.generate_combined_report()
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
                elif self.test_mobile == 'yes':
                    self.bs_config.read(self.bs_config_file_mobile)
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
                junitxml_path = os.path.join(self.self.tim, browser + browser_version
                                             + os_type + os_version + resolution + '.xml')
                html_path = os.path.join(self.result_folder, browser + browser_version
                                         + os_type + os_version + resolution + '.html')

            # set pytest arguments values from configuration files
            else:

                if self.test_mobile == 'yes':
                    self.bs_config.read(self.bs_config_file_mobile)
                    browserName = self.bs_config.get(config_section, 'browserName')
                    platform = self.bs_config.get(config_section, 'platform')
                    device = self.bs_config.get(config_section, 'device')
                    orientation = self.bs_config.get(config_section, 'deviceOrientation')
                    junitxml_path = os.path.join(self.result_folder, config_section + '.xml')
                    html_path = os.path.join(self.result_folder, config_section + '.html')
                    test_result_prefix = '[' + device + ', ' + platform + ', ' + browserName + ']'

                    pytest_arguments.extend([
                        '--junitxml=' + junitxml_path,
                        '--junit-prefix=' + test_result_prefix,
                        '--html=' + html_path,
                        '--html-prefix=' + test_result_prefix,
                        '--xbrowserName=' + browserName,
                        '--xplatform=' + platform,
                        '--xdevice=' + device,
                        '--xdeviceOrientation=' + orientation,
                        '--jira_username=' + self.jira_username,
                        '--jira_password=' + self.jira_password])
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
                        '--instafail',
                        '--jira_username=' + self.jira_username,
                        '--jira_password=' + self.jira_password])

        # setup pytest arguments for local browser
        else:
            #pytest_arguments.append('--jirapasswd=' + os.path.join(self.result_folder, self.driver_name + '.html'))
            pytest_arguments.append('--junitxml=' + os.path.join(self.result_folder, self.driver_name + '.xml'))
            pytest_arguments.append('--html=' + os.path.join(self.result_folder, self.driver_name + '.html'))
            pytest_arguments.append('--jira_username=' + self.jira_username)
            pytest_arguments.append('--jira_password=' + self.jira_password)

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
        parser.add_argument('--mobile',
                            help='Run tests on mobile/tablets, "default:none"'
                                 'for running use "yes"',
                            default='none')
        parser.add_argument('--jira_username',
                            help='Jira username',
                            default='none')
        parser.add_argument('--jira_password',
                            help='Jira password',
                            default='none')
        parser.add_argument('--browserstack',
                            help='BrowserStack credentials; format: "username:token"',
                            default='none')

        args = parser.parse_args()
        return [args.env, args.tests, args.mobile, args.jira_username, args.jira_password, args.browserstack]

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
        shutil.make_archive(os.path.join(archive_folder, self.timestamp), "zip",
                            os.path.join(self.project_root, 'results'))

    def generate_combined_report(self):
        data = os.listdir(os.path.join(self.project_root, 'results', self.timestamp))
        result_reports = [item[:-5] for item in data if item.endswith('.html')]
        if len(result_reports) > 0:
            env = Environment(
                loader=FileSystemLoader(os.path.join(self.current_folder, 'library', 'report', 'resources')))
            template = env.get_template('CombinedReportTemplate.html')
            template_vars = {'data': result_reports}
            output = template.render(template_vars)
            formatted_output = output.encode('utf8').strip()
            final_report = open(os.path.join(self.project_root, 'results', self.timestamp, 'CombinedReport.html'), 'w')
            final_report.write(formatted_output)
            final_report.close()
            shutil.copy(os.path.join(self.current_folder, 'library', 'report', 'resources', 'combined_report.js'),
                        os.path.join(self.project_root, 'results', self.timestamp))
