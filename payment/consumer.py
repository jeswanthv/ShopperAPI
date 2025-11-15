import json
import logging
from kafka import KafkaConsumer
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_SERVER = 'localhost:9092'
PRODUCT_TOPIC = 'product_events'


def consume_product_events():
    consumer = KafkaConsumer(
        PRODUCT_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset='earliest',  # Start from the beginning
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    logger.info(
        f"Kafka consumer connected, listening for '{PRODUCT_TOPIC}'...")
    db: Session = SessionLocal()

    for message in consumer:
        event = message.value
        try:
            if event.get("type") in ["product_created", "product_updated"]:
                product_data = event["data"]
                logger.info(
                    f"Processing event for product ID: {product_data['product_id']}")

                product = db.query(Product).filter_by(
                    id=product_data["product_id"]).first()

                if product:  # Update
                    product.name = product_data["name"]
                    product.price = product_data["price"]
                else:  # Create
                    product = Product(
                        id=product_data["product_id"],
                        name=product_data["name"],
                        price=product_data["price"]
                    )
                    db.add(product)

                db.commit()

            elif event.get("type") == "product_deleted":
                # We could also handle deletions
                pass

        except Exception as e:
            logger.error(f"Failed to process event: {e}")
            db.rollback()


if __name__ == "__main__":
    consume_product_events()
