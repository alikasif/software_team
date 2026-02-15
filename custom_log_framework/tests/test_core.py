import unittest
import os
import io
import time
import sqlite3
import tempfile
import shutil
from custom_logger.core import Logger, LogLevel, StandardFormatter, LogRecord
from custom_logger.handlers import ConsoleHandler, FileHandler, DatabaseHandler

class TestCore(unittest.TestCase):
    def test_logger_level_filtering(self):
        logger = Logger("test_logger", LogLevel.INFO)
        
        # Capture handler
        class MockHandler:
            def __init__(self):
                self.records = []
            def handle(self, record):
                self.records.append(record)
        
        handler = MockHandler()
        logger.add_handler(handler)
        
        logger.debug("This should not be logged")
        logger.info("This should be logged")
        logger.error("This should also be logged")
        
        self.assertEqual(len(handler.records), 2)
        self.assertEqual(handler.records[0].msg, "This should be logged")
        self.assertEqual(handler.records[1].msg, "This should also be logged")

    def test_standard_formatter(self):
        formatter = StandardFormatter()
        timestamp = 1600000000.0 # 2020-09-13 ...
        local_time_struct = time.localtime(timestamp)
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', local_time_struct)
        
        record = LogRecord(
            timestamp=timestamp,
            level=LogLevel.INFO,
            msg="Test Message",
            threadName="MainThread",
            filename="test.py",
            lineno=10
        )
        
        formatted = formatter.format(record)
        expected = f"[{time_str}] [INFO] Test Message"
        self.assertEqual(formatted, expected)

    def test_console_handler(self):
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream)
        handler.set_formatter(StandardFormatter())
        
        record = LogRecord(
            timestamp=time.time(),
            level=LogLevel.WARNING,
            msg="Console Test",
            threadName="MainThread",
            filename="test.py",
            lineno=10
        )
        
        handler.handle(record)
        output = stream.getvalue()
        self.assertIn("[WARNING] Console Test", output)

    def test_file_handler(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_name = tmp.name
        
        try:
            handler = FileHandler(tmp_name)
            handler.set_formatter(StandardFormatter())
            
            record = LogRecord(
                timestamp=time.time(),
                level=LogLevel.ERROR,
                msg="File Test",
                threadName="MainThread",
                filename="test.py",
                lineno=10
            )
            
            handler.handle(record)
            handler.close()
            
            with open(tmp_name, 'r') as f:
                content = f.read()
                
            self.assertIn("[ERROR] File Test", content)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def test_database_handler_memory(self):
        # DatabaseHandler constructor takes a path. 
        # Using ':memory:' might be tricky if it opens new connection in each thread 
        # or if implementation assumes a path. The standard sqlite3 supports :memory:.
        
        handler = DatabaseHandler(":memory:")
        # We need access to the connection to verify, but DatabaseHandler creates its own.
        # Let's inspect the handler.conn directly since it's an attribute.
        
        record = LogRecord(
            timestamp=123456789.0,
            level=LogLevel.FATAL,
            msg="DB Test",
            threadName="MainThread",
            filename="test.py",
            lineno=10
        )
        
        handler.handle(record)
        
        cursor = handler.conn.cursor()
        cursor.execute("SELECT message, level FROM logs")
        rows = cursor.fetchall()
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "DB Test")
        self.assertEqual(rows[0][1], LogLevel.FATAL)
        
        handler.close()

if __name__ == '__main__':
    unittest.main()
