import logging
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Set up a custom logger for your application
logger = logging.getLogger("RvX")
logger.setLevel(logging.INFO)

# Create a file handler to log messages to a file
file_handler = logging.FileHandler("login_activity.log")
file_handler.setLevel(logging.INFO)

# Create a console handler to log messages to the console (optional)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the custom logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
