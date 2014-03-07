# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: BrowserStack test runner
"""
import pytest
import os
import ConfigParser
from library.lib_test_config import gid, config_loader
import sys
import getopt
import datetime
import requests
import xml.etree.ElementTree as ET
import json


class PyTestRunner():
    """ Selenium PyTest runner """

    def __init__(self):
        now = datetime.datetime.now()
        bs_config_file = os.path.dirname(os.path.abspath(__file__)) + '/browserstack.properties'
        if not (os.path.exists(bs_config_file)):
            print('"browserstack.properties" file was not found! Session terminated.')
            sys.exit()

        self.bs_config = ConfigParser.RawConfigParser()
        self.bs_config.read(bs_config_file)
        self.timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        self.result_folder = os.path.dirname(os.path.abspath(__file__)) + '/' \
                             + gid('result_folder', config_loader()) + '/' + self.timestamp
        self.build_name = self.get_build_name()

    def run_tests(self):
        """ Runs tests locally or using Browserstack. """
        driver_name = gid('driver', config_loader())
        if not (os.path.exists(self.result_folder)):
            os.makedirs(self.result_folder)
        if driver_name.lower() == 'browserstack':
            for config_section in self.bs_config.sections():
                print('Running combination: ' + config_section)
                self.trigger_pytest(config_section)
            self.correct_browserstack_results(gid('bs_username', config_loader()),
                                              gid('bs_password', config_loader()),
                                              self.build_name, self.result_folder + '/' + config_section)
        else:
            config_section = driver_name
            self.trigger_pytest(config_section)

    def trigger_pytest(self, config_section):
        """ trigger PyTest runner """
        current_path = os.path.dirname(os.path.abspath(__file__))
        driver_name = gid('driver', config_loader())
        if driver_name.lower() == 'browserstack':
            config = self.bs_config
            test_result_prefix = '[' + config.get(config_section, 'browser') \
                                 + ', ' + config.get(config_section, 'browser_version') \
                                 + ', ' + config.get(config_section, 'os') \
                                 + ', ' + config.get(config_section, 'os_version') \
                                 + ', ' + config.get(config_section, 'resolution') + ']'

            pytest.main([current_path + '/tests',
                         '-n', gid('parallel_tests', config_loader()),
                         '--junit-prefix=' + test_result_prefix,
                         '--junitxml=' + self.result_folder + '/' + config_section,
                         '--xbrowser=' + config.get(config_section, 'browser'),
                         '--xbrowserversion=' + config.get(config_section, 'browser_version'),
                         '--xos=' + config.get(config_section, 'os'),
                         '--xosversion=' + config.get(config_section, 'os_version'),
                         '--xresolution=' + config.get(config_section, 'resolution'),
                         '--xbuildname=' + self.build_name])
        else:
            pytest.main([current_path + '/tests',
                         '-n', gid('parallel_tests', config_loader()),
                         '--junitxml=' + self.result_folder + '/' + config_section])

    def get_build_name(self):
        """ Retrieves the build name from script argument and also appends timestamp. """
        build_name = ''
        try:
            options, args = getopt.getopt(sys.argv[1:], 'hg:d', ['bname='])
            for opt, arg in options:
                if opt == '--bname':
                    build_name = arg
        except:
            print('Build name argument passed to script by Continuous Integration Job was incomplete or incorrect!'
                  '\nSetting default name: ' + self.timestamp)

        build_name = build_name + ' (' + self.timestamp + ')'
        return build_name

    def correct_browserstack_results(self, username, password, session_name, result_file):
        """ Searches for failed tests in PyTest xUnit report XML file
         and mark those tests on BrowserStack as failed through API call """
        # parse report xUnit XML file
        for invalid_char in [['#', ' '], ['-', ' '], ['(', ''], [')', '']]:
            session_name = session_name.replace(invalid_char[0], invalid_char[1])
        session_name = session_name.strip()
        if os.path.isfile(result_file):
            root = ET.parse(result_file)
        else:
            print('Could not find result file "' + result_file + '"! BrowserStack results not changed.')
            sys.exit()

        tree = root.getroot()
        failed_tests = []

        test_cases = tree.findall('testcase')
        for test in test_cases:
            if len(test.getchildren()) > 0:
                if test.getchildren()[0].tag in ('error', 'failure'):
                    failed_tests.append(test.get('name'))

        # get build session id
        build_id = None
        url = 'https://www.browserstack.com/automate/builds.json'
        response = requests.get(url, auth=(username, password)).json()
        for item in response:
            if item['automation_build']['name'] == session_name:
                build_id = item['automation_build']['hashed_id']

        # get test session id
        failed_sessions = []

        if build_id is None:
            print('Build with id: :"' + session_name + '" was not found!')
            sys.exit()
        else:
            url = 'https://www.browserstack.com/automate/builds/' + build_id + '/sessions.json'
            response = requests.get(url, auth=(username, password)).json()
            for item in response:
                test_case_name = item['automation_session']['name'].split(': ')[1]
                if test_case_name in failed_tests:
                    print('Will set "' + test_case_name + '" as failed! '
                                                          '(' + item['automation_session']['hashed_id'] + ')')
                    failed_sessions.append(item['automation_session']['hashed_id'])

        # set session statuses
        for session_id in failed_sessions:
            url = 'https://www.browserstack.com/automate/sessions/' + session_id + '.json'
            payload = {'status': 'error'}
            headers = {'content-type': 'application/json'}
            requests.put(url, auth=(username, password), data=json.dumps(payload), headers=headers)


test_runner = PyTestRunner()
test_runner.run_tests()