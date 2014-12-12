__author__ = 'HSC'
__version__ = 0.1

import os
import re
import sys
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

PYTHON3 = sys.version > '3'


class ChonfigDOTException(Exception):
    pass

class ChonfigInterpolationException(Exception):
    pass


class Chonfig:

    def __init__(self, cfg_file=None, default_cfg=None):
        # cfg_file must be a str pointing to a valid path
        assert isinstance(cfg_file, str)
        assert os.path.isfile(cfg_file)
        self._cfg_file = cfg_file
        # default_cfg must be a dictionary or None
        assert isinstance(default_cfg, dict) or default_cfg is None
        self._default_cfg = default_cfg
        # default inits
        self._raw_cfg_obj = None
        self._cfg = {}
        # doing the stuff
        self._load_config_file()
        self._string_interpolation()
        self._function_execute()
        print(self._cfg)

    def _load_config_file(self):
        self._raw_cfg_obj = configparser.RawConfigParser()
        self._raw_cfg_obj.read(self._cfg_file)
        for sect in self._raw_cfg_obj.sections():
            if '.' in sect:
                raise ChonfigDOTException('Sections cannot contain "." in their name: %s' % sect)
            for name, value in self._raw_cfg_obj.items(sect):
                if '.' in name:
                    raise ChonfigDOTException('Option names cannot contain "." in their name: %s' % name)
                self._cfg['%s.%s' % (sect, name)] = value

    def _string_interpolation(self, retry=10):
        assert not self._raw_cfg_obj is None
        if retry < 0:
            raise ChonfigInterpolationException('Possible self referencing interpolation')
        p = re.compile('(%\(([\w\.]+)\)s)')
        # for C:\%(sect3.val)s44\test we have ret[0] = ("%(set3.sf4)s", "set3.sf4")
        must_retry = False
        for opt in self._cfg:
            ret = re.findall(p, self._cfg[opt])
            if len(ret) == 0:
                continue
            else:
                must_retry = True
                for full, tmp_opt in ret:
                    if not '.' in tmp_opt:
                        raise ChonfigInterpolationException('Invalid reference for interpolation: %s' % tmp_opt)
                    self._cfg[opt] = self._cfg[opt].replace(full, self._cfg[tmp_opt])
        if must_retry:
            self._string_interpolation(retry=retry-1)

    def _function_execute(self, retry=10):
        assert not self._raw_cfg_obj is None
        if retry < 0:
            raise ChonfigInterpolationException('Possible self referencing interpolation')
        p = re.compile('%(?P<func>\w+)\((?P<rest>(?!%)(?P<stop>(?!\)f).)*\)f)')
        must_retry = False
        for opt in self._cfg:
            ret = re.findall(p, self._cfg[opt])
            if len(ret) == 0:
                continue
            must_retry = True
            ret = ret[0] #  [(func, rest, stop)]
            data = ret[1][:2]
            self._cfg[opt] = self._cfg[opt].replace('%%%s(%s' % (ret[0], ret[1]), data)
        if must_retry:
            self._function_execute(retry=retry-1)


if __name__ == '__main__':
    print('chonfig v%.2f by %s' % (__version__, __author__))
    test_fname = r'E:\Projects\chonfig\test\test.con'
    if not os.path.isfile(test_fname):
        test_fname = '/vagrant/test/test.con'
    cfg = Chonfig(cfg_file=test_fname)