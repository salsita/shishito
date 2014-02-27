# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common function library
"""
import ConfigParser
from selenium import webdriver
import os


def config_loader():
    """ loads variables from .properties configuration files """
    # load server config variables
    server_config = ConfigParser.ConfigParser()
    server_config.read(os.path.dirname(
        os.path.abspath(__file__)) + '/../server_config.properties')
    server_config_vars = dict(server_config.defaults())

    # load local config variables
    local_config = ConfigParser.ConfigParser()
    local_config.read(os.path.dirname(
        os.path.abspath(__file__)) + '/../local_config.properties')
    local_config_vars = dict(local_config.defaults())

    return_configs = [server_config_vars, local_config_vars]
    return return_configs


def gid(searched_id, config_vars):
    """ Gets value from config variables based on provided key.
     If local execution parameter is "True", function will try to search for parameter in local configuration file.
     If such parameter is not found or there is an error while reading the file, server (default) configuration
     file will be used instead. """
    server_config = config_vars[0]
    local_config = config_vars[1]
    local_execution = local_config.get('local_execution')
    use_server = True

    if local_execution.lower() == 'true':
        try:
            searched_value = local_config.get(searched_id)
            if searched_value == '':
                print('Local value for "' + searched_id + '" empty! Using server value instead...')
            else:
                use_server = False
        except:
            print('There was an error while retrieving value "' + searched_id + '" from local config!.'
                  + '\nUsing server value instead.')
    if use_server:
        value_to_return = server_config.get(searched_id)
    else:
        value_to_return = local_config.get(searched_id)

    return value_to_return


def get_capabilities(testname, testcase):
    """ Returns dictionary of capabilities for specific Browserstack browser/os combination """
    config = ConfigParser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) + '/../temp_combo')
    section = 'BROWSERSTACK'
    desired_cap = {'os': config.get(section, 'os'),
                   'os_version': config.get(section, 'os_version'),
                   'browser': config.get(section, 'browser'),
                   'browser_version': config.get(section, 'browser_version'),
                   'resolution': config.get(section, 'resolution'),
                   'project': gid('project_name', config_loader()),
                   'build': config.get(section, 'build_name'),
                   'name': testname + ': ' + testcase.split(':')[1]}
    return desired_cap


def start_browser(self, testname, testcase, url=gid('base_url', config_loader()),
                  browser=gid('driver', config_loader()), width=gid('window_width', config_loader()),
                  height=gid('window_height', config_loader())):
    """ Browser startup function.
     Initialize session over Browserstack or local browser. """
    if browser.lower() == "browserstack":
        self.driver = webdriver.Remote(
            command_executor=gid('command_executor', config_loader()),
            desired_capabilities=get_capabilities(testname, testcase))
    elif browser == "Firefox":
        self.driver = webdriver.Firefox()
    elif browser == "Chrome":
        self.driver = webdriver.Chrome()
    elif browser == "IE":
        self.driver = webdriver.Ie
    elif browser == "PhantomJS":
        self.driver = webdriver.PhantomJS()
    elif browser == "Opera":
        self.driver = webdriver.OperaDriver()
    elif browser == "Safari":
        self.driver = webdriver.SafariDriver()

    if browser.lower() != "browserstack":
        self.driver.set_window_size(width, height)
    self.driver.get(url)
    self.driver.implicitly_wait(10)
    return self.driver


def log_in(email_field, email, password_field, password, submit_button):
    """ basic login function """
    email_field.clear()
    password_field.clear()

    email_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()