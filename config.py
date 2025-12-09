import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGO_URI') or "mongodb+srv://kingsleyaigbojie2023_db_user:Debbie2026.@cluster0.cp8y8rx.mongodb.net/?appName=Cluster0"
    # For MongoDB Atlas (cloud):
    # MONGO_URI = 'mongodb+srv://username:password@cluster.mongodb.net/database_name'

