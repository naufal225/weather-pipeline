import logging
from datetime import datetime
import os

def get_logger(name: str) -> logging.Logger:
    #Buat logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    #Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    os.makedirs("logs", exist_ok=True)

    #Handler 1 : Tulis ke file
    file_handler = logging.FileHandler(f"logs/pipeline_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler.setFormatter(formatter)

    #Handler 2: Tulis ke console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger