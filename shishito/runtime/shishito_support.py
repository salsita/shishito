import ConfigParser
import os
from importlib import import_module

import pytest
import sys


class ShishitoSupport(object):
    """ Support class for getting config values and importing modules according to
    test platform and environment.

    :param cmd_args: dictionary with command lines arguments
    :type cmd_args: dict or None
    :param project_root: test project root (where to find config files, tests, ..)
    :type project_root: str or None
    """

    def __init__(self, cmd_args=None, project_root=None):
        # parsed arguments from commad_line
        self.args_config = cmd_args or {}

        # called without cmd_args
        # if True gid will use only pytest.config
        # if False gid uses pytest.config, cmd_args and config files
        self.used_in_test = cmd_args is None

        self.project_root = project_root or self.find_project_root()

        # get configs
        self.configs = self.load_configs()

        self.test_environment = self.get_opt('test_environment')
        self.test_platform = self.get_opt('test_platform')

        # get environment config
        self.env_config = self.get_environment_config()

    def find_project_root(self):
        """ Try to find config directory on sys.path

        :raises ValueError: if config directory is not found on sys.path
        """

        for path in sys.path:
            config_dir = os.path.join(path, 'config')
            if os.path.exists(config_dir):
                return path

        raise ValueError('Can not find config dir on sys.path')

    def load_configs(self):
        """ Load variables from .properties configuration files """

        config_path = os.path.join(self.project_root, 'config')
        if not os.path.exists(config_path):
            raise ValueError('Configuration path does not exist (%s)' % config_path)

        configs = []

        # load server config variables
        config = ConfigParser.ConfigParser()
        server_config = os.path.join(config_path, 'server_config.properties')
        config.read(server_config)
        server_config_vars = dict(config.defaults())
        configs.append((server_config_vars, 'server config'))

        # load local config variables
        config = ConfigParser.ConfigParser()
        local_config = os.path.join(config_path, 'local_config.properties')
        config.read(local_config)
        local_config_vars = dict(config.defaults())

        if local_config_vars.get('local_execution').lower() == 'true':
            configs.insert(0, (local_config_vars, 'local config'))

        return configs

    def get_opt(self, *args):
        """ Get value from config variables based on provided key.

        If local execution parameter is "True", function will try to search for parameter in local configuration file.
        If such parameter is not found or there is an error while reading the file, server (default) configuration
        file will be used instead.

        :param args: key or config_section, key
        """

        if len(args) > 2 or not args:
            raise TypeError('Wrong number of arguments (%s), takes 1 or 2.' % len(args))

        if len(args) == 2:
            section, key = args
        else:
            key = args[0]
            section = None

        if section:
            # use env config
            return self.env_config.get(section, key)

        # first try to lookup pytest config
        try:
            value = pytest.config.getoption(key)
            if value:
                return value
        except (ValueError, AttributeError):
            pass

        # look in cmd args config
        value = self.args_config.get(key)
        if value:
            return value

        for cfg, cfg_name in self.configs:
            value = cfg.get(key)
            if value:
                return value

    def get_environment_config(self):
        """ Load environment specific configuration file according to current test platform and environment """

        config = ConfigParser.ConfigParser()
        config_path = os.path.join(self.project_root, 'config', self.test_platform, self.test_environment + '.properties')

        if not os.path.exists(config_path):
            raise ValueError('Config file in location {0} was not found!'.format(config_path))

        config.read(config_path)
        return config

    def get_module(self, module):
        """ Import object from given module according to current test platform and environment.

        :param str module: module used for import
        :return: imported object
        :raises ValueError: in case of unknown module
        """

        platform_execution = 'shishito.runtime.platform.' + self.test_platform + '.control_execution'
        platform_test = 'shishito.runtime.platform.' + self.test_platform + '.control_test'
        test_environment = 'shishito.runtime.environment.' + self.test_environment

        if module == 'platform_execution':
            return getattr(import_module(platform_execution), 'ControlExecution')
        elif module == 'platform_test':
            return getattr(import_module(platform_test), 'ControlTest')
        elif module == 'test_environment':
            return getattr(import_module(test_environment), 'ControlEnvironment')

        raise ValueError('Unknown module.')

    def get_test_control(self):
        """ Return TestControl object for current test platform. Used in tests.

        :return: TestControl object
        """

        return self.get_module('platform_test')()
