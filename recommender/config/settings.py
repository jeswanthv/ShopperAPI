import os
from dotenv import load_dotenv

load_dotenv()

# We don't have a product API yet, so we can ignore this
PRODUCT_API = os.getenv("PRODUCT_API")

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5433/recommender_db")
