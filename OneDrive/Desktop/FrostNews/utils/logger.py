import logging

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="[{asctime}] [{levelname}] {message}",
        style="{",
        handlers=[
            logging.FileHandler("frostnews.log"),
            logging.StreamHandler()
        ]
    )
