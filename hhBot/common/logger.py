import logging
import json
from threading import Lock
from logging.handlers import RotatingFileHandler

class LoggerMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'message': record.getMessage(),
            'name': record.name,
            'filename': record.filename,
            'lineno': record.lineno,
        }
        return json.dumps(log_record, ensure_ascii=False)

def initLogger(log_file=None, log_level=logging.INFO, max_bytes=1024*1024*10, backup_count=5):
    stream_handler = logging.StreamHandler()
    handlers = [stream_handler]

    if log_file is not None:
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        json_file_handler = RotatingFileHandler(f"{log_file}.json", maxBytes=max_bytes, backupCount=backup_count)
        handlers.extend([file_handler, json_file_handler])

    formatter = logging.Formatter("[%(levelname)s] %(asctime)s : %(message)s")
    json_formatter = JsonFormatter()

    for handler in handlers:
        if isinstance(handler, RotatingFileHandler) and handler.baseFilename.endswith('.json'):
            handler.setFormatter(json_formatter)
        else:
            handler.setFormatter(formatter)
        handler.setLevel(log_level)

    logging.basicConfig(level=log_level, handlers=handlers)

class Logger(metaclass=LoggerMeta):
    def __init__(self, log_file=None, log_level=logging.INFO, max_bytes=10485760, backup_count=5):
        initLogger(log_file, log_level, max_bytes, backup_count)
        self.logging = logging.getLogger(__name__)
    
    def log(self, message, level=logging.INFO):
        self.logging.log(level, message)
    
    def info(self, message):
        self.log(message, logging.INFO)
    
    def debug(self, message):
        self.log(message, logging.DEBUG)
        
    def error(self, message):
        self.log(message, logging.ERROR)
    
    def warning(self, message):
        self.log(message, logging.WARNING)

logger = Logger(log_file="heychat_bot.log")