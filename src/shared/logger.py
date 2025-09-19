import logging

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class LoggerWrapper:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)