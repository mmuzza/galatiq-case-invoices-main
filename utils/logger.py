
# For clean logging purposes instead of printing

import logging

def setup_logger(name="galatiq_logger"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)


    if logger.hasHandlers():
        logger.handlers.clear()

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)


    formatter = logging.Formatter("%(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logger



logger = setup_logger()


def section(title: str):
    logger.info("\n" + "=" * 60)
    logger.info(title)
    logger.info("=" * 60 + "\n")


def pretty_log_dict(data, indent=2):

    import json


    if hasattr(data, "dict"):
        data = data.dict()


    elif hasattr(data, "__dataclass_fields__"):
        from dataclasses import asdict
        data = asdict(data)


    elif hasattr(data, "__dict__"):
        data = data.__dict__


    if isinstance(data, list):
        data = [
            d.dict() if hasattr(d, "dict") else d.__dict__ if hasattr(d, "__dict__") else d
            for d in data
        ]

    logger.info(json.dumps(data, indent=indent))