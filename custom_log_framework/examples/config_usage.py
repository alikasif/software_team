import sys
import os

# Add the parent directory to sys.path to run this example without installing the package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_logger import dictConfig, getLogger, LogLevel

def main():
    # 1. Define Configuration Dictionary
    config = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'ConsoleHandler',
                'level': 'DEBUG'
            },
            'file': {
                'class': 'FileHandler',
                'level': 'INFO',
                'args': ['config.log'],
                'kwargs': {'mode': 'w'}
            }
        },
        'loggers': {
            'my_app': {
                'level': 'DEBUG',
                'handlers': ['console', 'file']
            }
        }
    }

    # 2. Apply Configuration
    print("Applying configuration...")
    dictConfig(config)

    # 3. Get Logger
    # Note: 'my_app' matches the key in the 'loggers' config
    logger = getLogger("my_app")

    # 4. Log Messages
    print("--- Starting Logging ---")
    logger.debug("Debug message (Console only, as file is INFO)")
    logger.info("Info message (Console + File)")
    logger.warning("Warning message (Console + File)")
    print("--- Finished Logging ---")

    print(f"Check 'config.log' for info+ messages.")

if __name__ == "__main__":
    main()
