import logging
import os

class DebugLogger():

    indentation = 4
    indent_level = -indentation

    def __init__(self, loggerName, filePath, format):
        if filePath == 'default':
            filePath = "C:\Users\Sam\Documents\ASPIRA\Social-Network-Harvester\SocialNetworkHarvester\log\debugLogger.log"

#	open(filePath, 'w').close()
        self.logger = logging.getLogger(loggerName)
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(filePath, mode="a+")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(format)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def log(self, message):
        self.logger.info('%s%s'%(' '*self.indent_level, message))

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
            ret = func(*args, **kwargs)
            self.indent_level -= self.indentation
            return ret
        return inner
