import unittest
from custom_logger.config import dictConfig
from custom_logger.core import getLogger, LogLevel, Logger
from custom_logger.handlers import ConsoleHandler, FileHandler
import tempfile
import os

class TestConfig(unittest.TestCase):
    def test_dict_config(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_name = tmp.name
        
        try:
            config = {
                'version': 1,
                'handlers': {
                    'console': {
                        'class': 'ConsoleHandler',
                        'level': 'DEBUG'
                    },
                    'file': {
                        'class': 'FileHandler',
                        'level': 'ERROR',
                        'args': [tmp_name],
                        'kwargs': {'mode': 'w'}
                    }
                },
                'loggers': {
                    'test_app': {
                        'level': 'INFO',
                        'handlers': ['console', 'file']
                    }
                }
            }
            
            dictConfig(config)
            
            logger = getLogger('test_app')
            self.assertIsInstance(logger, Logger)
            self.assertEqual(logger.level, LogLevel.INFO)
            self.assertEqual(len(logger.handlers), 2)
            
            # Verify handlers are attached
            handler_types = [type(h).__name__ for h in logger.handlers]
            self.assertIn('ConsoleHandler', handler_types)
            self.assertIn('FileHandler', handler_types)

            # Clean up handlers to close files
            for h in logger.handlers:
                if hasattr(h, 'close'):
                    h.close()

        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

if __name__ == '__main__':
    unittest.main()
