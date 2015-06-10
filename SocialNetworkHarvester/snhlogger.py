# coding=UTF-8

import sys
import os
import logging
from settings import PROJECT_PATH, LOG_LEVEL

INDENT_LEVEL = 0

def init_logger(logger_name, log_file):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(os.path.join(PROJECT_PATH, "log/%s" % log_file), mode="a+")
    fh.setLevel(LOG_LEVEL)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s<br>')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def init_custom_logger(logger_name, log_file, format):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(os.path.join(PROJECT_PATH, "log/%s" % log_file), mode="a+")
    fh.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger