import threading
import time
import inspect
from enum import IntEnum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict

class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    FATAL = 50

@dataclass
class LogRecord:
    timestamp: float
    level: LogLevel
    msg: str
    threadName: str
    filename: str
    lineno: int

    def get_message(self) -> str:
        """Return the raw message."""
        return self.msg

class Formatter(ABC):
    @abstractmethod
    def format(self, record: LogRecord) -> str:
        """Format the log record into a string."""
        pass

class StandardFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        """
        Formats the record as:
        [Time] [Level] Message
        """
        # Simple timestamp formatting
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.timestamp))
        return f"[{time_str}] [{record.level.name}] {record.msg}"

class Handler(ABC):
    def __init__(self, level: LogLevel = LogLevel.DEBUG):
        self.level = level
        self.formatter: Optional[Formatter] = None
        self.lock = threading.Lock()

    def set_level(self, level: LogLevel):
        """Set the logging level of this handler."""
        self.level = level

    def set_formatter(self, formatter: Formatter):
        """Set the formatter for this handler."""
        self.formatter = formatter

    def format(self, record: LogRecord) -> str:
        """Format the record using the handler's formatter, or default if none."""
        if self.formatter:
            return self.formatter.format(record)
        return str(record.msg)

    def acquire(self):
        """Acquire the thread lock."""
        if self.lock:
            self.lock.acquire()

    def release(self):
        """Release the thread lock."""
        if self.lock:
            self.lock.release()

    def close(self):
        """Tidy up any resources used by the handler."""
        pass

    def handle(self, record: LogRecord):
        """
        Conditionally emit the record if it meets the level requirement.
        Thread-safety is expected to be handled in emit.
        """
        if record.level >= self.level:
            self.emit(record)

    @abstractmethod
    def emit(self, record: LogRecord):
        """
        Do whatever it takes to actually log the specified logging record.
        Must be thread-safe (acquire self.lock).
        """
        pass

class Logger:
    def __init__(self, name: str, level: LogLevel = LogLevel.DEBUG):
        self.name = name
        self.level = level
        self.handlers: List[Handler] = []
        self.lock = threading.RLock()

    def set_level(self, level: LogLevel):
        """Set the logging level of this logger."""
        self.level = level

    def add_handler(self, handler: Handler):
        """Add a handler to this logger."""
        with self.lock:
            if handler not in self.handlers:
                self.handlers.append(handler)

    def remove_handler(self, handler: Handler):
        """Remove a handler from this logger."""
        with self.lock:
            if handler in self.handlers:
                self.handlers.remove(handler)

    def log(self, level: LogLevel, msg: str, *args, **kwargs):
        """
        Low-level logging method which creates a LogRecord and 
        dispatches it to all handlers.
        """
        # If level is an int, convert to LogLevel
        if isinstance(level, int):
            try:
                level = LogLevel(level)
            except ValueError:
                # Fallback or handle invalid level
                pass

        if level < self.level:
            return

        # Simple string formatting for args if provided
        if args:
            try:
                msg = msg % args
            except TypeError:
                # Fallback if formatting fails
                pass
        
        # Capture caller info
        # stack()[0] is log, stack()[1] is info/debug/etc (or caller if called directly), stack()[2] is the caller
        try:
            # We need to find the caller frame. If called via debug(), stack is:
            # log -> debug -> caller.
            # If called via log(), stack is:
            # log -> caller.
            # We can inspect the stack to find the first frame outside this module?
            # Or just assume standard depth.
            
            # Simple heuristic:
            frame = inspect.currentframe()
            caller_frame = frame.f_back
            while caller_frame:
                if caller_frame.f_code.co_name in ('debug', 'info', 'warning', 'error', 'fatal', 'log'):
                     caller_frame = caller_frame.f_back
                     continue
                break
            
            if caller_frame:
                filename = caller_frame.f_code.co_filename
                lineno = caller_frame.f_lineno
            else:
                filename = "unknown"
                lineno = 0
            
        except Exception:
            filename = "unknown"
            lineno = 0

        record = LogRecord(
            timestamp=time.time(),
            level=level,
            msg=str(msg),
            threadName=threading.current_thread().name,
            filename=filename,
            lineno=lineno
        )

        with self.lock:
            for handler in self.handlers:
                handler.handle(record)

    def debug(self, msg: str, *args, **kwargs):
        """Log a message with severity 'DEBUG'."""
        self.log(LogLevel.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log a message with severity 'INFO'."""
        self.log(LogLevel.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log a message with severity 'WARNING'."""
        self.log(LogLevel.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log a message with severity 'ERROR'."""
        self.log(LogLevel.ERROR, msg, *args, **kwargs)


    def fatal(self, msg: str, *args, **kwargs):
        """Log a message with severity 'FATAL'."""
        self.log(LogLevel.FATAL, msg, *args, **kwargs)

# Registry to hold configured loggers
_logger_registry: Dict[str, Logger] = {}
root = Logger("root", LogLevel.WARNING)
_logger_registry["root"] = root

def getLogger(name: str = None) -> Logger:
    """
    Return a logger with the specified name, creating it if necessary.
    If name is None, return the root logger.
    """
    if not name:
        return root
    
    if name not in _logger_registry:
        _logger_registry[name] = Logger(name)
    return _logger_registry[name]
