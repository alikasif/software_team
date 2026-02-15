import unittest
import threading
import tempfile
import sqlite3
import os
import shutil
from custom_logger.core import Logger, LogLevel
from custom_logger.handlers import FileHandler, DatabaseHandler

class TestConcurrency(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")
        self.db_file = os.path.join(self.temp_dir, "test.db")
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_concurrent_logging(self):
        logger = Logger("concurrent_logger", LogLevel.DEBUG)
        
        file_handler = FileHandler(self.log_file)
        db_handler = DatabaseHandler(self.db_file)
        
        logger.add_handler(file_handler)
        logger.add_handler(db_handler)
        
        num_threads = 10
        msgs_per_thread = 100
        total_messages = num_threads * msgs_per_thread
        
        def worker(thread_id):
            for i in range(msgs_per_thread):
                logger.info(f"Thread {thread_id} msg {i}")
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        file_handler.close()
        db_handler.close()
        
        # Verify file lines
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), total_messages, f"Expected {total_messages} lines in file, got {len(lines)}")
        
        # Verify DB rows
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, total_messages, f"Expected {total_messages} rows in DB, got {count}")

if __name__ == '__main__':
    unittest.main()
