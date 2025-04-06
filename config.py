import os

class Config(object):
  API_ID = int(os.getenv("apiid"))
  
  API_HASH = os.getenv("apihash")
  
  BOT_TOKEN = os.getenv("tk")
  
  AUTH = os.getenv("auth")
  
  OWNER =os.getenv("owner")

  Sub = os.getenv("sub", "iskolaP")

  TeraExScript = os.getenv("tscript")

  PW =int(os.getenv("spw"))

  PRARAL_LIMIT = int(os.getenv("pps",3))
