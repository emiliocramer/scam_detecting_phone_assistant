import certifi
from pymongo import MongoClient
from src.config import MONGODB_ADMIN_PW

CONNECTION_STRING = f'mongodb+srv://admin:{MONGODB_ADMIN_PW}@aws-m0-cluster.34opjf9.mongodb.net/?retryWrites=true&w=majority&appName=aws-m0-cluster'
client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
db = client['aws-m0-cluster']

