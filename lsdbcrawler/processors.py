import logging
import traceback
import sys


def to_int(s, fallback=0):
    """Try to cast an int to a string. If you can't, return the fallback value"""
    try:
        result = int(s)
    except ValueError:
        logging.warning("Couldn't cast %s to int", s)
        logging.error(traceback.format_exc())
        f = sys._getframe().f_back
        for item in traceback.StackSummary.from_list(traceback.extract_stack(f)):
            logging.error(item)

        result = fallback

    return result
