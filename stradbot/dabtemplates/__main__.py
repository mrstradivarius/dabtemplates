import sys
import traceback

from pywikibot import logging

from . import dabtemplates

if __name__ == "__main__":
    try:
        dabtemplates.main()
    except Exception as e:
        logging.critical(f"Error running dabtemplates task: {e}")
        logging.debug(traceback.format_exc())
        sys.exit(1)
    except KeyboardInterrupt:
        logging.critical("Dabtemplates task interrupted by user")
        sys.exit(2)
