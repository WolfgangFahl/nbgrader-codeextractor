__version__ = "0.0.1"
# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())