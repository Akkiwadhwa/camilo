# logger.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name='app_logger', log_file='logs/app.log', level=logging.INFO):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    handler.setFormatter(formatter)

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console)

    return logger
