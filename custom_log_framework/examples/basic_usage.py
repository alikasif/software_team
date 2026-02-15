import sys
import os

# Add the parent directory to sys.path to run this example without installing the package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_logger import Logger, LogLevel, ConsoleHandler, FileHandler

def main():
    # 1. Create a Logger
    logger = Logger("manual_config_logger", level=LogLevel.DEBUG)

    # 2. Create Handlers
    # Console handler that logs everything
    console_handler = ConsoleHandler()
    console_handler.set_level(LogLevel.DEBUG)

    # File handler that logs only warnings and above
    file_handler = FileHandler("manual.log", mode='w') # mode='w' to overwrite for this example
    file_handler.set_level(LogLevel.WARNING)

    # 3. Add Handlers to Logger
    logger.add_handler(console_handler)
    logger.add_handler(file_handler)

    # 4. Log Messages
    print("--- Starting Logging ---")
    logger.debug("This is a debug message (Console only)")
    logger.info("This is an info message (Console only)")
    logger.warning("This is a warning message (Console + File)")
    logger.error("This is an error message (Console + File)")
    logger.fatal("This is a fatal message (Console + File)")
    print("--- Finished Logging ---")
    
    print(f"Check 'manual.log' for warning+ messages.")

if __name__ == "__main__":
    main()
