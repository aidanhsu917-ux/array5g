One of the purposes of the README is to form the central hub for the design journal and documentation. It will transition uses when development of a phase is complete. 

# Issues by Date
## 09_28_2026
What is numpy.arange(start, stop, step)? Creates an array with equal spacing of "ste'" between stop and start. 

**More Robust Debugging:**
```python
import logging
import os

def setup_logging():
    # Read environment variable; default to INFO
    debug_mode = os.getenv("DEBUG", "false").lower() in ("true", "1", "t", "yes")
    log_level = logging.DEBUG if debug_mode else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        force=True  # Overrides pre-existing handlers
    )
    
    if debug_mode:
        logging.debug("Debug mode IS ACTIVE.")

setup_logging()
logger = logging.getLogger(__name__)

#Usage anywhere in your application:
logger.debug("Executing query: %s", "SELECT * FROM users")  # Included only when DEBUG is active
logger.info("Server started on port 8080")                 # Always included
```

