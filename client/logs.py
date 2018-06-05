import os
import logging
import logging.handlers


def SetupLogs(path):
    """
    Helper function for creating a logs for whole client.
    """

    # Create logging
    logger = logging.getLogger("miner_watchdog")

    # Switch files each day. Save backup for last 7 days
    file_handler = logging.handlers.TimedRotatingFileHandler( os.path.abspath( os.path.join(path, "./logs/miner_watchdog.log") ), when="D", interval=1, backupCount=7)

    # Format for log messages
    formatter = logging.Formatter("%(name)s %(levelname)s %(asctime)s %(message)s")

    # Output everything
    logger.setLevel(logging.DEBUG)

    # Set format and file handler
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger