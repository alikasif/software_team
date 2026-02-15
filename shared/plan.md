# Project Name: custom_log_framework

## Git Strategy
-   Branch: `logging_framework`
-   Commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `chore:`

## architecture
-   **Core**: `Logger`, `LogRecord`, `LogLevel`, `Formatter` (abstract base).
-   **Handlers**: `Handler` (abstract base), `ConsoleHandler`, `FileHandler`, `DatabaseHandler` (sqlite3).
-   **Configuration**: `DictConfigurator` to load settings from a dictionary.
-   **Concurrency**: 
    -   `Logger` uses `threading.RLock` for managing handlers.
    -   Each `Handler` instance has its own `threading.Lock` to ensure atomic writes (especially for files/db).

## Modules
1.  `custom_logger/core.py`: Definitions for LogLevel (enum), LogRecord (dataclass), Logger, and Formatter base class.
2.  `custom_logger/handlers.py`: Concrete Handler implementations.
3.  `custom_logger/config.py`: Configuration parsing logic.
4.  `tests/`: Test suite using `unittest`.

## API Contracts
-   `Logger.log(level: LogLevel, msg: str, *args, **kwargs)`
-   `Handler.emit(record: LogRecord)`
-   `Formatter.format(record: LogRecord) -> str`
-   `config.dictConfig(config: dict)`

## Tasks
1.  Initialize Git & Push Scaffold
2.  Implement Core Classes (`LogLevel`, `LogRecord`, `Logger`, `Formatter`)
3.  Implement Handlers (`ConsoleHandler`, `FileHandler`, `DatabaseHandler`) and Thread Safety
4.  Implement Configuration Logic (`dictConfig`)
5.  Create Unit Tests and Thread Safety Tests
6.  Write Documentation and Usage Examples
