import inspect
import os
import re
import configparser
import base64
from selenium import webdriver
import json
from shishito.runtime.all_content_type import content_types

OPTIONS = 'OPTIONS'
ARGUMENTS = 'ARGUMENTS'
EXTENSIONS = 'EXTENSIONS'
PREFS = 'PREFS'

BROWSER_KEYWORDS = {  # map lowercase browser name to option keyword understood by chromedriver/geckodriver...
    'chrome': {
        OPTIONS: 'chromeOptions',
        ARGUMENTS: 'args',
        EXTENSIONS: 'extensions',
        PREFS: 'prefs',
    },
    'firefox': {
        OPTIONS: 'moz:firefoxOptions',
        ARGUMENTS: 'args',
    }
}


class ShishitoEnvironment(object):
    """ Base class for test environment. """

    def __init__(self, shishito_support):
        self.shishito_support = shishito_support

    def get_browser_arguments(self, config_section):
        """
        return array of browser command line arguments from config_section
            [Chrome]
            browser_arguments=--enable-experimental-web-platform-features --unlimited-storage
            ...
        :param config_section: name of config section in web/*.properties (e.g. Chrome)
        :return: array
        """

        if config_section is None:
            return []

        try:
            arguments_string = self.shishito_support.get_opt(config_section, 'browser_arguments')
        except configparser.NoOptionError:
            return []

        if arguments_string:
            arguments = [i for i in re.split('\s+', arguments_string) if i != '']
            return arguments
        else:
            return []

    def get_experimental_arguments(self, config_section):
        """
        return array of browser command line arguments from config_section
            [Chrome]
            experimental_arguments=--mobileEmulation--{"deviceName": "Apple iPhone 6"}
            ...
        :param config_section: name of config section in web/*.properties (e.g. Chrome)
        :return: array
        """

        if config_section is None:
            return []

        try:
            arguments_string = self.shishito_support.get_opt(config_section, 'experimental_arguments')
        except configparser.NoOptionError:
            return []

        if arguments_string:
            arguments = arguments_string.split('--')
            return arguments[1:]
        else:
            return None

    def get_browser_extensions(self, config_section):
        """
        Check browser config for 'extensions' parameter, if not found fallback to common config.
        Return array of browser extension files from config_section.
        If the extension name is a variable ( $VAR_NAME ), get the value from the environment
            [Chrome]
            extensions=/tmp/extensions/my-extension.crx  another_extension.crx
            ...
        :param config_section: name of config section in web/*.properties (e.g. Chrome)
        :return: array
        """

        extension_string = None
        extensions = []
        if config_section is not None:
            try:
                extension_string = self.shishito_support.get_opt(config_section, 'browser_extensions')  # browser config
            except configparser.NoOptionError:
                extension_string = None

        if extension_string is None:
            try:
                extension_string = self.shishito_support.get_opt('browser_extensions')  # common config
            except configparser.NoOptionError:
                pass

        if extension_string is None:
            return []

        for item in re.split('\s+', extension_string):
            if item != '':
                m = re.match('^\$([A-Z][A-Z_]+)$', item)
                if m is not None:
                    var_name = m.group(1)
                    if var_name not in os.environ:
                        raise Exception("Error getting browser_extensions: env variable '" + item + "' not defined")
                    extensions.append(os.environ[var_name])  # take the extension path as configured
                else:
                    extensions.append(item)  # take the extension path as configured

        return extensions

    def add_cmdline_arguments_to_browser(self, browser_capabilities, config_section):
        """
        Add browser command line arguments to capabilities dict
        :param browser_capabilities: dict (see https://w3c.github.io/webdriver/webdriver-spec.html)
        :param config_section: name of the browser config section (e.g. 'Chrome')
        """

        browser_name = self.shishito_support.get_opt(config_section, 'browser').lower()
        arguments = self.get_browser_arguments(config_section)
        if arguments:
            try:
                options_kw = BROWSER_KEYWORDS[browser_name][OPTIONS]
                args_kw = BROWSER_KEYWORDS[browser_name][ARGUMENTS]
                browser_capabilities.setdefault(options_kw, {}).setdefault(args_kw, []).extend(arguments)
            except:
                pass

    def set_download_path(self, driver):
        """set download path for Chrome. Variable in config file download_path can be either string or env var."""
        try:
            download_directory = self.shishito_support.get_opt('download_path')
            if download_directory is None:
                return
        except configparser.NoOptionError:
            return

        try:
            driver.command_executor._commands["send_command"] = (
            "POST", '/session/$sessionId/chromium/send_command')
            params = {'cmd': 'Page.setDownloadBehavior',
                      'params': {'behavior': 'allow', 'downloadPath': download_directory}}
            driver.execute("send_command", params)
        except:
            return


    def add_extensions_to_browser(self, browser_capabilities, config_section):
        """
        Add base64-encoded extensions to capabilities dict
        :param browser_capabilities: dict (see https://w3c.github.io/webdriver/webdriver-spec.html)
        :param config_section: name of the browser config section (e.g. 'Chrome')
        """

        browser_name = self.shishito_support.get_opt(config_section, 'browser').lower()
        extensions = self.get_browser_extensions(config_section)

        if extensions:
            try:
                options_kw = BROWSER_KEYWORDS[browser_name][OPTIONS]
                exts_kw = BROWSER_KEYWORDS[browser_name][EXTENSIONS]
                browser_capabilities.setdefault(options_kw, {}).setdefault(exts_kw, [])
            except:
                return

            for extension in extensions:
                with open(extension, 'rb') as ext_file:
                    extension_base64 = base64.b64encode(ext_file.read()).decode('UTF-8')
                browser_capabilities[options_kw][exts_kw].append(extension_base64)

    def add_experimental_option(self, browser_capabilities, config_section):
        browser_name = self.shishito_support.get_opt(config_section, 'browser').lower()
        arguments = self.get_experimental_arguments(config_section)
        if arguments and browser_name == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            if ('mobileEmulation' in arguments):
                index = arguments.index('mobileEmulation')
                chrome_options.add_experimental_option(arguments[index], json.loads(arguments[index + 1]))
            return browser_capabilities.update(chrome_options.to_capabilities())
        return browser_capabilities

    def call_browser(self, config_section):
        """ Start webdriver for given config section."""
        raise NotImplementedError()

    def get_capabilities(self, config_section):
        """ Return dictionary of capabilities for specific config combination/

        :param str config_section: section in platform/environment.properties config
        :return: dict with capabilities
        Example of browser capabilities object:
             "desiredCapabilities" : {
                "browserName" : "chrome",
                "version" : "50.1",
                "acceptSslCerts" : true,
                "javascriptEnabled" : true,
                "platform" : "ANY",
                "chromeOptions" : {
                   "args" : [ "--ignore-certificate-errors" ],
                   "extensions" : [ "base64-xxxxx" ]
                }
             }
        """
        get_opt = self.shishito_support.get_opt
        test_platform = self.shishito_support.test_platform
        if (test_platform == 'web'):
            # Get logging levels from config
            logging_driver = get_opt(config_section, 'logging_driver', default='WARNING').upper()
            logging_browser = get_opt(config_section, 'logging_browser', default='WARNING').upper()
            logging_performance = get_opt(config_section, 'logging_performance', default='WARNING').upper()

            capabilities = {
                'browserName': get_opt(config_section, 'browser').lower(),
                'version': get_opt(config_section, 'browser_version'),
                'resolution': get_opt(config_section, 'resolution'),
                'javascriptEnabled': True,
                'acceptSslCerts': get_opt('accept_ssl_cert').lower() == 'true',
                'loggingPrefs': {'driver': logging_driver,
                                 'browser': logging_browser,
                                 'performance': logging_performance}
            }
        if (test_platform == 'mobile'):
            capabilities = {
                'browserName': get_opt(config_section, 'browser').lower(),
                'javascriptEnabled': True,
                'acceptSslCerts': get_opt('accept_ssl_cert').lower() == 'true',
            }

        self.add_cmdline_arguments_to_browser(capabilities, config_section)
        self.add_extensions_to_browser(capabilities, config_section)
        self.add_experimental_option(capabilities, config_section)
        return capabilities

    def start_driver(self, browser_type, capabilities, config_section=None):
        """ Prepare selenium webdriver.

        :param str browser_type: type of browser for which prepare driver
        :param dict capabilities: capabilities used for webdriver initialization
        """

        raise NotImplementedError()

    def get_browser_profile(self, browser_type, capabilities, config_section=None):
        """ Return browser profile ready to be passed to driver.

        :param str browser_type: browser type (chrome, firefox, ..)
        :param dict capabilities: capabilities dict - can be updated
        :return: browser profile or None
        """

        # lowercase browser_type
        browser_type = browser_type.lower()
        profile = None

        if browser_type == 'firefox':
            profile = webdriver.FirefoxProfile()
            try:
                download_file_path = self.shishito_support.get_opt('download_path')
                if download_file_path:
                    profile.set_preference("browser.download.folderList", 2)
                    profile.set_preference("browser.download.manager.showWhenStarting", False)
                    profile.set_preference("browser.download.dir", download_file_path)
                    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", content_types)
                    profile.set_preference("browser.helperApps.alwaysAsk.force", False)
                    profile.set_preference("browser.download.manager.useWindow", False)
                    profile.set_preference("browser.download.manager.focusWhenStarting", False)
                    profile.set_preference("browser.helperApps.neverAsk.openFile", True)
                    profile.set_preference("browser.download.manager.showAlertOnComplete", False)
                    profile.set_preference("browser.download.manager.closeWhenDone", True)
            except configparser.NoOptionError:
                pass

            for ext in self.get_browser_extensions(config_section):
                profile.add_extension(ext)

        return profile

    def get_pytest_arguments(self, config_section):
        """ Get environment specific arguments for pytest.

        :param config_section: section in platform/environment.properties config
        :return: dict with arguments for pytest or None
        """
        pass

    def get_test_name(self):
        try:
            return os.environ.get('PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0]
        except:
            return self.shishito_support.get_opt('project_name')
