import sys
from typing import Dict, Any, List
# Import getLogger and root from core to utilize the global registry
from .core import Logger, LogLevel, Handler, Formatter, StandardFormatter, getLogger, root
from .handlers import ConsoleHandler, FileHandler, DatabaseHandler

def dictConfig(config: Dict[str, Any]):
    """
    Configure the logging system from a dictionary.
    
    Keys: 
      - version (required, must be 1)
      - handlers (optional)
      - loggers (optional)
    """
    version = config.get('version')
    if version != 1:
        raise ValueError("Only version 1 is supported")
    
    handlers_config = config.get('handlers', {})
    loggers_config = config.get('loggers', {})
    
    created_handlers: Dict[str, Handler] = {}
    
    # Create handlers
    for handler_name, handler_cfg in handlers_config.items():
        class_name = handler_cfg.get('class')
        level_input = handler_cfg.get('level', 'DEBUG') 
        if isinstance(level_input, str):
            level_name = level_input.upper()
        else:
            level_name = level_input
            
        # Resolve level
        try:
            if isinstance(level_name, int):
                level = LogLevel(level_name)
            else:
                level = LogLevel[level_name]
        except (KeyError, ValueError):
            level = LogLevel.DEBUG

        # Instantiate handler
        handler_class = None
        # Support full dotted path imports if needed, but simplistic check for now
        if class_name == 'logging.StreamHandler' or class_name == 'ConsoleHandler':
             handler_class = ConsoleHandler
        elif class_name == 'logging.FileHandler' or class_name == 'FileHandler':
             handler_class = FileHandler
        elif class_name == 'DatabaseHandler':
             handler_class = DatabaseHandler
        
        if handler_class:
            # Prepare arguments
            # args can be a list or tuple
            args = handler_cfg.get('args', [])
            kwargs = handler_cfg.get('kwargs', {})
            
            # Instantiate
            try:
                handler = handler_class(*args, **kwargs)
                handler.set_level(level)
                
                # Setup formatter (always StandardFormatter for now)
                formatter = StandardFormatter()
                handler.set_formatter(formatter)
                
                created_handlers[handler_name] = handler
            except Exception:
                pass

    # Configure loggers
    for logger_name, logger_cfg in loggers_config.items():
        if logger_name == 'root':
            logger = root
        else:
            logger = getLogger(logger_name)
            
        level_input = logger_cfg.get('level', 'DEBUG')
        if isinstance(level_input, str):
            level_name = level_input.upper()
        else:
            level_name = level_input

        try:
            if isinstance(level_name, int):
                level = LogLevel(level_name)
            else:
                level = LogLevel[level_name]
        except (KeyError, ValueError):
             level = LogLevel.DEBUG
                 
        logger.set_level(level)
        
        # Add handlers
        handler_names = logger_cfg.get('handlers', [])
        for h_name in handler_names:
            if h_name in created_handlers:
                logger.add_handler(created_handlers[h_name])
