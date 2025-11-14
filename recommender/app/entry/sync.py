from kafka import KafkaConsumer
import json
import requests
from app.db.session import ReplicaSession
from app.db.models import Product, Interaction
from config.settings import PRODUCT_API, KAFKA_SERVER


def sync_products():
    consumer = KafkaConsumer("product_events", bootstrap_servers=KAFKA_SERVER)
    print("Kafka consumer connected, listening for 'product_events'...")
    for message in consumer:
        event = json.loads(message.value)
        with ReplicaSession() as session:
            if event["type"] in ["product_created", "product_updated"]:
                product_data = event["data"]
                print(f"Product data: {product_data}")
                print(
                    f"Processing product event: {event['type']} for product ID: {product_data['product_id']}")
                product = session.query(Product).filter_by(
                    id=product_data["product_id"]).first()
                if product:
                    product.name = product_data["name"]
                    product.description = product_data["description"]
                    product.price = product_data["price"]
                    product.account_id = product_data["account_id"]
                else:
                    product = Product(
                        id=product_data["product_id"],
                        name=product_data["name"],
                        description=product_data["description"],
                        price=product_data["price"],
                        # --- IMPORTANT ---
                        # Use 'account_id' (lowercase) to match the event
                        account_id=product_data["account_id"]
                    )
                    session.add(product)
                session.commit()
            elif event["type"] == "product_deleted":
                product = session.query(Product).filter_by(
                    id=event["data"]["product_id"]).first()
                if product:
                    session.delete(product)
                    session.commit()


def process_interactions():
    consumer = KafkaConsumer("interaction_events",
                             bootstrap_servers=KAFKA_SERVER)
    print("Kafka consumer connected, listening for 'interaction_events'...")
    for message in consumer:
        event = json.loads(message.value)
        with ReplicaSession() as session:
            interaction = Interaction(
                user_id=event["data"]["user_id"],
                product_id=event["data"]["product_id"],
                interaction_type=event["type"]
            )
            session.add(interaction)
            # This part is for syncing products if they don't exist
            # We can simplify for now, but it's good to have
            product = session.query(Product).filter_by(
                id=event["data"]["product_id"]).first()
            if not product:
                try:
                    # This PRODUCT_API is not set, so this will fail
                    # We will add interaction events later
                    response = requests.get(
                        f"{PRODUCT_API}/{event['product_id']}")
                    response.raise_for_status()
                    product_data = response.json()
                    product = Product(**product_data)
                    session.add(product)
                except requests.RequestException as e:
                    print(
                        f"Failed to fetch product {event['data']['product_id']}: {e}")
            session.commit()


if __name__ == "__main__":
    # For now, we only need to sync products
    sync_products()
    # We will run process_interactions() later
    # process_interactions()
