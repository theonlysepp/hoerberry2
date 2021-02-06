#!/usr/bin/env python
# -*- coding: utf8 -*-


# Testprogramm fuer den Logger

import logging
import time

# create logger
logger = logging.getLogger('test_logger')
logger.setLevel(logging.DEBUG)

# create file handler and set level to debug
timestring = time.strftime('%x')
ch = logging.FileHandler('log/testlog_{}.log'.format(timestring.replace('/','_') ) )
ch.setLevel(logging.DEBUG)    # hier wird entschieden, bis zu welchem Level alles mitgelogged wird. 

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# Haupschleife

logger.debug('debug message')
time.sleep(1)
logger.info('info message')
time.sleep(1)
logger.warning('warn message')
time.sleep(1)
logger.error('error message')
logger.critical('critical message')


