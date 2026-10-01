"""Advisory file locking implementation."""

import os
import time
import logging
import random
from pathlib import Path
from typing import Optional

from src.logger import logger

class LockError(Exception):
    """Raised when a file lock cannot be acquired."""
    pass

class FileLock:
    """
    An advisory file lock using a '.lock' file.
    Uses os.O_CREAT | os.O_EXCL for atomic lock acquisition.
    """

    def __init__(
        self, 
        target_file: str, 
        timeout: float = 10.0, 
        max_retries: int = 5,
        base_delay: float = 0.1,
        max_delay: float = 2.0
    ):
        self.target_file = Path(target_file)
        self.lock_file = self.target_file.with_suffix(self.target_file.suffix + '.lock')
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._lock_fd: Optional[int] = None

    def acquire(self):
        """
        Attempts to acquire the lock with exponential backoff.
        """
        start_time = time.time()
        retries = 0

        while time.time() - start_time < self.timeout:
            try:
                # Attempt to create the lock file exclusively
                # os.O_CREAT | os.O_EXCL is atomic on most systems
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                self._lock_fd = fd
                
                # Write PID to the lock file for debugging purposes
                os.write(fd, str(os.getpid()).encode())
                
                logger.debug(f"Acquired lock on {self.lock_file}")
                return True

            except FileExistsError:
                # Lock is held by another process
                retries += 1
                if retries > self.max_retries:
                    # If we exceeded max retries, but still within timeout, 
                    # we might want to continue or fail. 
                    # Here we decide to fail after max_retries to prevent infinite loops.
                    raise LockError(f"Failed to acquire lock on {self.lock_file} after {self.max_retries} retries.")

                # Exponential backoff with jitter
                delay = min(self.max_delay, self.base_delay * (2 ** (retries - 1)))
                jitter = delay * 0.5 * random.random()
                sleep_time = delay + jitter
                
                logger.debug(f"Lock held by another process. Retrying in {sleep_time:.2f}s (Attempt {retries}/{self.max_retries})")
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Unexpected error during lock acquisition: {e}")
                raise

        raise LockError(f"Timeout reached while waiting for lock on {self.lock_file}")

    def release(self):
        """
        Releases the lock by closing the file descriptor and removing the lock file.
        """
        if self._lock_fd is not None:
            try:
                os.close(self._lock_fd)
                if self.lock_file.exists():
                    self.lock_file.unlink()
                logger.debug(f"Released lock on {self.lock_file}")
            except Exception as e:
                logger.error(f"Error releasing lock on {self.lock_file}: {e}")
            finally:
                self._lock_fd = None
        else:
            logger.warning(f"Attempted to release a lock that was not acquired: {self.lock_file}")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
