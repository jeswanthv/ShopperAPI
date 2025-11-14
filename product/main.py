import json
import logging
import time
from fastapi import FastAPI, HTTPException
from elasticsearch import Elasticsearch
from kafka import KafkaProducer
from pydantic import BaseModel

# --- Pydantic Models (Data Validation) ---


class Product(BaseModel):
    name: str
    description: str
    price: float
    account_id: int  # The ID of the user who created it


class ProductInDB(Product):
    id: str  # The ID from Elasticsearch


# --- Service Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Connect to Elasticsearch
# We'll retry a few times, as it can be slow to start
es = None
for i in range(5):
    try:
        es = Elasticsearch("http://localhost:9200",
                           verify_certs=False, ssl_show_warn=False, basic_auth=None,
                           api_key=None)
        if es.cluster.health():
            logger.info("✅ Connected to Elasticsearch!")
            break
    except Exception as e:
        logger.warning(
            f"Connecting to Elasticsearch failed (Attempt {i+1})... {e}")
        time.sleep(3)

if not es:
    logger.critical("❌ Could not connect to Elasticsearch. Exiting.")
    exit()

# Connect to Kafka
try:
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    logger.info("✅ Connected to Kafka!")
except Exception as e:
    logger.critical(f"❌ Could not connect to Kafka: {e}")
    exit()

# --- API Endpoints ---


@app.post("/products/", response_model=ProductInDB, status_code=201)
def create_product(product: Product):
    logger.info(f"Received request to create product: {product.name}")

    try:
        # 1. Save to Elasticsearch
        # We let Elasticsearch generate the ID
        res = es.index(
            index="products",  # The "table" name
            body=product.model_dump_json()  # Use model_dump_json() for Pydantic v2
        )

        product_id = res['_id']
        logger.info(f"Saved to Elasticsearch with ID: {product_id}")

        # 2. Create the event payload
        event_payload = {
            "type": "product_created",
            "data": {
                "product_id": product_id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "account_id": product.account_id
            }
        }

        # 3. Send to Kafka
        producer.send("product_events", value=event_payload)
        producer.flush()  # Ensure the message is sent
        logger.info(f"Published 'product_created' event to Kafka.")

        return ProductInDB(id=product_id, **product.model_dump())

    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}", response_model=ProductInDB)
def get_product(product_id: str):
    logger.info(f"Fetching product with ID: {product_id}")
    try:
        res = es.get(index="products", id=product_id)
        if not res['found']:
            raise HTTPException(status_code=404, detail="Product not found")

        return ProductInDB(id=res['_id'], **res['_source'])

    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        # 'NotFoundError' is a specific exception from the elasticsearch client
        if 'NotFoundError' in str(type(e)):
            raise HTTPException(status_code=404, detail="Product not found")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok"}
