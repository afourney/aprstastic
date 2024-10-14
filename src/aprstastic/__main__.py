import logging
import yaml
from ._gateway import Gateway
logging.basicConfig(level=logging.INFO) 

with open("config.yml", 'r') as file:
    config = yaml.safe_load(file)

gateway = Gateway(config)
gateway.run()
