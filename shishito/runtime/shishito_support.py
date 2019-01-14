import os
from importlib import import_module

import pytest
import sys
if sys.version_info.major > 2:
    import configparser
else:
    import ConfigParser
    configparser = ConfigParser


class ShishitoSupport(object):
    """ Support class for getting config values and importing modules according to
    test platform and environment.

    :param cmd_args: dictionary with command lines arguments
    :type cmd_args: dict or None
    :param project_root: test project root (where to find config files, tests, ..)
    :type project_root: str or None
    """

    def __init__(self, cmd_args=None, project_root=None):
        # parsed arguments from command_line
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
            tests_dir = os.path.join(path, 'tests')
            if os.path.exists(config_dir) and os.path.exists(tests_dir):
                return path

        raise ValueError('Can not find config dir on sys.path')

    def load_configs(self):
        """ Load variables from .properties configuration files. If local_execution is true in local_config file, function
        return both local config dict and server confgi dict. Otherwise function returns only server config dict.

        :return: list with config dictionaries
        :raises ValueError: if config path does not exist
        """

        config_path = os.path.join(self.project_root, 'config')
        if not os.path.exists(config_path):
            raise ValueError('Configuration path does not exist (%s)' % config_path)

        configs = []

        # load server config variables
        config = configparser.ConfigParser()
        server_config = os.path.join(config_path, 'server_config.properties')
        config.read(server_config)
        server_config_vars = dict(config.defaults())
        configs.append((server_config_vars, 'server config'))

        # load local config variables
        config = configparser.ConfigParser()
        local_config = os.path.join(config_path, 'local_config.properties')
        config.read(local_config)
        local_config_vars = dict(config.defaults())

        if local_config_vars.get('local_execution').lower() == 'true':
            configs.insert(0, (local_config_vars, 'local config'))

        return configs

    def get_opt(self, *args, default=None):
        """ Get value from config variables based on provided key and optionaly section.

        If key is given, function searches in pytest.config, command lines arguments, local config (if enabled) and server config.
        If section and key are given, function searches in environment config file.


        :param args: key or config_section, key
        :param default: default value to return if not found
        :return: value for given key or None
        :raises TypeError: if called with wrong number of arguments
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
            try:
                value = self.env_config.get(section, key)
                if value[0] == '$':
                    return os.environ[value[1:]]
                return value
            except configparser.NoOptionError:
                return default

        # first try to lookup pytest config
        try:
            value = pytest.config.getoption(key)
            if value:
                if value[0] == '$':
                    return os.environ[value[1:]]
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
                if value[0] == '$':
                    return os.environ[value[1:]]
                return value
            else:
                return default

    def get_environment_config(self):
        """ Load environment specific configuration file according to current test platform and environment

        :return: environment configuration file
        :raises ValueError: if config path does not exist
        """

        config = configparser.ConfigParser()
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
