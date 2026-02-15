# Custom Logging Framework

A thread-safe, extensible logging framework for Python designed for simplicity and performance.

## Features

- **Log Levels**: Support for DEBUG, INFO, WARNING, ERROR, and FATAL levels.
- **Multiple Destinations**: Log to console, files, or SQLite databases simultaneously.
- **Thread-Safety**: Built-in locking mechanisms ensuring safe logging in concurrent environments.

## Quick Start
```python
from custom_logger import Logger, LogLevel

# Create a logger instance
logger = Logger("my_app")

# Log a message
logger.info("Hello World")
```

## Configuration

The framework supports configuration via a dictionary using `dictConfig`.

### Structure

The configuration dictionary should have the following structure:
- `version`: Version of the configuration schema (current supported version is `1`).
- `handlers`: A dictionary of handler definitions.
- `loggers`: A dictionary of logger definitions.

### Example Configuration

```python
config = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'ConsoleHandler',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'FileHandler',
            'level': 'INFO',
            'args': ['app.log'],
            'kwargs': {'mode': 'w'}
        }
    },
    'loggers': {
        'root': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
}
```

## Handlers

The framework includes three built-in handlers:

### `ConsoleHandler`
Writes log records to a stream (stdout/stderr).
- `stream`: The stream to write to. Defaults to `sys.stderr`.

### `FileHandler`
Writes log records to a file on disk.
- `filename`: The path to the log file.
- `mode`: The file mode (default 'a' for append).
- `encoding`: The file encoding.
- `delay`: If True, file opening is deferred until the first call to emit.

### `DatabaseHandler`
Writes log records to a SQLite database.
- `db_path`: The path to the SQLite database file.
