from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import dotenv, os
from argon2 import PasswordHasher


dotenv.load_dotenv()
db = MongoClient(os.environ.get('MONGO_URI', None)).Data
motor = AsyncIOMotorClient(os.environ.get('MONGO_URI', None)).Data
ph = PasswordHasher()
