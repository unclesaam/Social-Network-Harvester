import logging
import os
import pprint

class DebugLogger():

    indentation = 4
    indent_level = -indentation
    pp = pprint.PrettyPrinter() 

    def __init__(self, loggerName, filePath, format):
    	open(filePath, 'w').close()
        self.logger = logging.getLogger(loggerName)
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(filePath, mode="a+")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(format)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def log(self, message, indent=True):
        self.logger.info('%s%s'%(' '*(self.indent_level+1*indent), message))

    def pretty(self, message):
        self.logger.info(self.pp.pformat(message).encode('utf8'))

    def exception(self, message):
        self.logger.exception(message)

    def debug(self, func):
        '''Decorator used to intelligently debug functions
        '''
        def inner(*args, **kwargs):
            #self.logger.info('%s%s%s'%(' '*self.indent_level, func.func_name, func.func_code.co_varnames[:func.func_code.co_argcount]))
            self.indent_level += self.indentation
            if self.indent_level > self.indentation*40:
                self.indent_level = 8
            elif self.indent_level < 0:
                self.indent_level = self.indentation*40 - 4
            try:
                ret = func(*args, **kwargs)
                self.indent_level -= self.indentation
            except:
                self.indent_level -= self.indentation
                raise
            return ret
        return inner
