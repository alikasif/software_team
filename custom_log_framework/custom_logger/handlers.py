import sqlite3
import threading
import sys
import logging
import os
from .core import Handler, LogLevel, LogRecord, StandardFormatter

class ConsoleHandler(Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout and sys.stderr may be used by other parts of the application.
    """
    def __init__(self, stream=None):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        Handler.__init__(self)
        if stream is None:
            stream = sys.stderr
        self.stream = stream

    def emit(self, record: LogRecord):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used when writing unicode strings
        to the output.
        """
        msg = self.format(record)
        with self.lock:
            try:
                stream = self.stream
                # issue 35046: flush to ensure output order
                stream.write(msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)

    def flush(self):
        """
        Flushes the stream.
        """
        if self.stream and hasattr(self.stream, "flush"):
            self.stream.flush()

    def handleError(self, record):
        """
        Handle errors which occur during an emit() call.
        """
        pass # simplified error handling

    terminator = '\n'

class FileHandler(Handler):
    """
    A handler class which writes formatted logging records to disk files.
    """
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        """
        Open the specified file and use it as the stream for logging.
        """
        Handler.__init__(self)
        self.baseFilename = os.path.abspath(filename)
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        if delay:
            self.stream = None
        else:
            self.stream = self._open()

    def _open(self):
        """
        Open the current base file with the (original) mode and encoding.
        """
        return open(self.baseFilename, self.mode, encoding=self.encoding)

    def close(self):
        """
        Closes the stream.
        """
        self.acquire()
        try:
            try:
                if self.stream:
                    try:
                        self.stream.flush()
                    finally:
                        stream = self.stream
                        self.stream = None
                        if hasattr(stream, "close"):
                            stream.close()
            finally:
                # Issue #19523: call whatever stream.close() calls.
                Handler.close(self)
        finally:
            self.release()
            
    def emit(self, record: LogRecord):
        """
        Emit a record.

        If the stream was not opened because 'delay' was specified in the
        constructor, open it before calling the superclass's emit.
        """
        msg = self.format(record)
        with self.lock:
            if self.stream is None:
                self.stream = self._open()
            
            try:
                self.stream.write(msg + '\n')
                self.flush()
            except Exception:
                self.handleError(record)

    def flush(self):
        if self.stream and hasattr(self.stream, "flush"):
            self.stream.flush()

    def handleError(self, record):
        pass # simplified

class DatabaseHandler(Handler):
    """
    A handler class which writes logging records to a sqlite3 database.
    """
    def __init__(self, db_path):
        Handler.__init__(self)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """
        Create the logs table if it doesn't exist.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                level INTEGER,
                message TEXT
            )
        ''')
        self.conn.commit()

    def emit(self, record: LogRecord):
        """
        Emit a record.
        """
        try:
            with self.lock: # Ensure thread safety for DB write
                self.cursor.execute('''
                    INSERT INTO logs (timestamp, level, message)
                    VALUES (?, ?, ?)
                ''', (record.timestamp, record.level, record.msg))
                self.conn.commit()
        except Exception:
            self.handleError(record)

    def close(self):
        """
        Closes the database connection.
        """
        self.conn.close()
        
    def handleError(self, record):
        pass # simplified
