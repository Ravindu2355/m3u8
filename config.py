import os

class Config(object):
  API_ID = int(os.getenv("apiid"))
  
  API_HASH = os.getenv("apihash")
  
  BOT_TOKEN = os.getenv("tk")
  
  AuthU = os.getenv("auth")
  
  OWNER =os.getenv("owner")
