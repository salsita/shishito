# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: BrowserStack test runner
"""
import pytest
import os
import ConfigParser
from library.lib_test_config import gid
import sys
import getopt
import time
import json
import shutil


class PyTestRunner():
    """ Selenium PyTest runner """

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
            print('Both browserstack properties files not found! Session terminated.')
            sys.exit()
        self.bs_config = ConfigParser.RawConfigParser()

        # load cmd arguments and set default values if not specified
        self.env_type = self.get_runner_args()[0]
        self.test_type = self.get_runner_args()[1]
        if self.env_type is None:
            self.env_type = 'vcs'
        if self.test_type is None:
            self.test_type = 'all'

    def run_tests(self):
        """ Runs tests locally or using Browserstack. """
        self.get_runner_args()
        if os.path.exists(self.dir_path + '/results'):
            shutil.rmtree(self.dir_path + '/results')
        os.makedirs(self.result_folder)
        if self.driver_name.lower() == 'browserstack':
            if self.env_type == 'vcs':
                if self.test_type == 'smoke':
                    self.bs_config.read(self.bs_config_file_smoke)
                else:
                    self.bs_config.read(self.bs_config_file)
                for config_section in self.bs_config.sections():
                    print('Running combination: ' + config_section)
                    self.trigger_pytest(config_section)
            elif self.env_type == 'os_vars':
                config_list = json.loads(str(os.environ['BROWSERSTACK']))
                for config_section in config_list['test_suite']:
                    print('Running combination: ' + str(config_section))
                    self.trigger_pytest(config_section)
        else:
            config_section = self.driver_name
            print('Running for browser: ' + config_section)
            self.trigger_pytest(config_section)
        self.archive_results()

    def trigger_pytest(self, config_section):
        """ trigger PyTest runner """
        pytest_arguments = [self.dir_path + '/tests', '-n', gid('parallel_tests')]
        if self.test_type == 'smoke':
            pytest_arguments.extend(['-m', self.test_type])
        if self.driver_name.lower() == 'browserstack':
            if self.env_type == 'os_vars':
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
                '--xbuildname=' + gid('build_name')])
        else:
            pytest_arguments.append('--junitxml=' + self.result_folder + '/' + self.driver_name)

        pytest.main(pytest_arguments)

    def get_runner_args(self):
        """ Retrieves the build name from script argument and also appends timestamp. """
        env_type = None
        test_type = None
        try:
            options, args = getopt.getopt(sys.argv[1:], 'hg:d', ['env=', 'tests='])
            for opt, arg in options:
                if opt == '--env':
                    env_type = arg
                if opt == '--tests':
                    test_type = arg
        except:
            print('Arguments passed to script were incomplete or incorrect!')
            sys.exit()
        return [env_type, test_type]

    def archive_results(self):
        """ Archives test results in zip package """
        archive_folder = self.dir_path + '/results_archive'
        if not (os.path.exists(archive_folder)):
            os.makedirs(archive_folder)
        shutil.make_archive(archive_folder + '/' + self.timestamp, "zip", self.dir_path + '/results')


test_runner = PyTestRunner()
test_runner.run_tests()