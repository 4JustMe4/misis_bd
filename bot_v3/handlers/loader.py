import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from parser.mongo import loadJsonFromMongo



def loadData(name):
    data = loadJsonFromMongo(name)
    if data is not None:
        return data
    else:
        try:
            with open(f"data/{name}.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"Ошибка при чтении локального файла {name}.json: {e}")
            return None