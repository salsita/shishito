import ConfigParser
import os
from importlib import import_module

import pytest
import sys


class ShishitoSupport(object):

    def __init__(self, cmd_args=None, project_root=None):
        """ cmd_args added only if called from runner.
        when called from tests cmd_args have to be added to pytest and taken from pytest.config
        """

        # parsed arguments from commad_line
        self.args_config = cmd_args or {}

        # called without cmd_args
        # if True gid will use only pytest.config
        # if False gid uses pytest.config, cmd_args and config files
        self.used_in_test = True if cmd_args is None else False

        if project_root:
            self.project_root = project_root
        else:
            self.project_root = os.getcwd()

        self.configs = self.load_configs()

        self.test_environment = self.gid('test_environment')
        self.test_platform = self.gid('test_platform')

    def load_configs(self):
        """ Loads variables from .properties configuration files,  check if project didn't contain such folder
        (for non selenium projects) """

        config_path = os.path.join(self.project_root, 'config')
        config = ConfigParser.ConfigParser()
        if not os.path.exists(config_path):
            return None

        # load server config variables
        server_config = os.path.join(config_path, 'server_config.properties')
        config.read(server_config)
        server_config_vars = dict(config.defaults())

        # load local config variables
        local_config = os.path.join(config_path, 'local_config.properties')
        config.read(local_config)
        local_config_vars = dict(config.defaults())

        # load non selenium config variables
        non_selenium_config = os.path.join(config_path, 'non_selenium_config.properties')
        config.read(non_selenium_config)
        non_selenium_config = dict(config.defaults())
        return_configs = [server_config_vars, local_config_vars, non_selenium_config]

        return return_configs

    def gid(self, key):
        """ Gets value from config variables based on provided key.
         If local execution parameter is "True", function will try to search for parameter in local configuration file.
         If such parameter is not found or there is an error while reading the file, server (default) configuration
         file will be used instead. """

        if not self.configs:
            return None

        # first try to lookup pytest config
        try:
            # TODO: find out why these options have '='
            if self.used_in_test and key in ['test_platform', 'test_environment', 'environment_configuration']:
                key += '='

            value = pytest.config.getoption(key)
            if value:
                return value
        except (ValueError, AttributeError):
            pass

        # look in cmd args config
        value = self.args_config.get(key)
        if value:
            return value

        # lookup value from config files
        server_config = self.configs[0]
        local_config = self.configs[1]

        configs = []

        # TOOD: this can be done in __init__ instead of each gid call
        if local_config.get('local_execution').lower() == 'true':
            configs.append((local_config, 'local config'))

        configs.extend([(server_config, 'server config'), (os.environ, 'env variables')])
        for cfg in configs:
            if key in cfg[0] and cfg[0][key] != '':
                return cfg[0][key]

    def get_environment_config(self, platform_name=None, environment_name=None):
        """ gets config """

        # TODO: review the functionality (is it what we want?)

        if platform_name is None:
            platform_name = self.gid('test_platform')

        if environment_name is None:
            environment_name = self.gid('test_environment')

        config = ConfigParser.ConfigParser()
        config_path = os.path.join(self.project_root, 'config', platform_name, environment_name + '.properties')

        if not config_path:
            sys.exit('Config file in location {0} was not found! Terminating test.'.format(config_path))

        config.read(config_path)
        return config

    def get_modules(self, platform=None, environment=None, module=None):
        if platform is None:
            platform = self.gid('test_platform')

        if environment is None:
            environment = self.gid('test_environment')

        platform_execution = 'shishito.library.modules.runtime.platform.' + platform + '.control_execution'
        platform_test = 'shishito.library.modules.runtime.platform.' + platform + '.control_test'
        test_environment = 'shishito.library.modules.runtime.environment.' + environment + '_control_environment'

        if module == 'platform_execution':
            return getattr(import_module(platform_execution), 'ControlExecution')
        elif module == 'platform_test':
            return getattr(import_module(platform_test), 'ControlTest')
        elif module == 'test_environment':
            return getattr(import_module(test_environment), 'ControlEnvironment')

        return {
            'platform_execution': getattr(import_module(platform_execution), 'ControlExecution'),
            'platform_test': getattr(import_module(platform_test), 'ControlTest'),
            'test_environment': getattr(import_module(test_environment), 'ControlEnvironment')
        }

    def get_test_control(self):
        return self.get_modules(module='platform_test')()
