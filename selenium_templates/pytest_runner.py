# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: BrowserStack test runner
"""
import pytest
import os
import ConfigParser
from library.common import gid, config_loader
import sys
import getopt
import datetime


class PyTestRunner():
    """ Selenium PyTest runner """

    def __init__(self):
        self.browserstack_env = None
        self.bs_config = ConfigParser.RawConfigParser()
        self.bs_config_file = os.path.dirname(os.path.abspath(__file__)) + '/browserstack.properties'
        now = datetime.datetime.now()
        self.current_date = now.strftime("%Y-%m-%d")
        self.current_time = now.strftime("%H-%M-%S")
        self.build_name = self.get_build_name()

    def run_tests(self):
        """ Runs tests locally or using Browserstack. """
        driver_name = gid('driver', config_loader())
        result_folder = os.path.dirname(os.path.abspath(__file__)) + '/' + gid('result_folder', config_loader())
        if not(os.path.exists(result_folder)):
            os.makedirs(result_folder)
        if driver_name.lower() == 'browserstack':
            if os.path.exists(self.bs_config_file):
                self.bs_config.read(self.bs_config_file)
                for item in self.bs_config.sections():
                    print('Running combination: ' + item)
                    existing_file = os.path.dirname(os.path.abspath(__file__)) + '/temp_combo'
                    if os.path.isfile(existing_file):
                        os.remove(existing_file)
                    self.browserstack_env = item
                    self.set_browserstack_env()
                    self.trigger_pytest(item)
            else:
                print('"browserstack.properties" file was not found! Session terminated.')
                sys.exit()
        else:
            item = driver_name
            self.trigger_pytest(item)

    def trigger_pytest(self, item):
        """ trigger PyTest runner """
        pytest.main([os.path.dirname(os.path.abspath(__file__))+'/tests',
                     '-n', gid('parallel_tests', config_loader()),
                     '--junitxml=' + os.path.dirname(os.path.abspath(__file__)) + '/'
                     + gid('result_folder', config_loader()) + '/' + item])
        driver_name = gid('driver', config_loader())
        if driver_name.lower() == 'browserstack':
            self.process_xunit_results(item)


    def set_browserstack_env(self):
        """ Creates temporary file with current BrowserStack combination. """
        config = self.bs_config
        config.read(self.bs_config_file)
        current_combo = self.browserstack_env
        f = open(os.path.dirname(os.path.abspath(__file__)) + '/temp_combo', 'w')
        f.write('[BROWSERSTACK]\n')
        f.write('os=' + config.get(current_combo, 'os') + '\n')
        f.write('os_version=' + config.get(current_combo, 'os_version') + '\n')
        f.write('browser=' + config.get(current_combo, 'browser') + '\n')
        f.write('browser_version=' + config.get(current_combo, 'browser_version') + '\n')
        f.write('resolution=' + config.get(current_combo, 'resolution') + '\n')
        f.write('build_name=' + self.build_name)
        f.close()

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
                  '\nSetting default name: ' + self.current_date + '_' + self.current_time)

        build_name = build_name + ' (' + self.current_date + '_' + self.current_time + ')'
        return build_name

    def process_xunit_results(self,item):
        """ Appends information about Browser and OS to xunit test result file,
         so it's not merged with other files, using different configuration, in Jenkins test report """
        config = self.bs_config
        config.read(self.bs_config_file)
        current_combo = self.browserstack_env
        text_to_append = '[' + config.get(current_combo, 'browser') + ' '\
                         + config.get(current_combo, 'browser_version') + ', '\
                         + config.get(current_combo, 'os') + ' ' + config.get(current_combo, 'os_version')\
                         + ', ' + config.get(current_combo, 'resolution') + '] '
        result_file = os.path.dirname(os.path.abspath(__file__))\
                      + '/' + gid('result_folder', config_loader()) + '/' + item
        f = open(result_file)
        text = f.read()
        f.close()
        text = text.replace('<testcase classname="', '<testcase classname="'+text_to_append)
        f = open(result_file, 'w')
        f.write(text)
        f.close()


test_runner = PyTestRunner()
test_runner.run_tests()
