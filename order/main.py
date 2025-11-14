import grpc
import httpx  # The HTTP client
import json
import logging
import time
from concurrent import futures
from sqlalchemy.orm import Session

# Import our generated gRPC files
from .proto.pb import order_pb2, order_pb2_grpc

# Import database and models
from .database import SessionLocal, create_db_and_tables, get_db
from .models import Order, OrderedProduct

# Import Kafka producer
from kafka import KafkaProducer

# --- Service Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL for our Product service (running on port 8002)
PRODUCT_SERVICE_URL = "http://localhost:8002"

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

# --- gRPC Service Implementation ---


class OrderService(order_pb2_grpc.OrderServiceServicer):

    def CreateOrder(self, request, context):
        logger.info(
            f"CreateOrder request received for account: {request.account_id}")
        db: Session = SessionLocal()

        total_price = 0.0
        product_details = []

        try:
            # --- 1. Service-to-Service Call ---
            # We need to get product prices from the Product Service
            # Note: This is a simple implementation. In a real-world scenario,
            # you'd fetch all products in one request if the API supported it.
            with httpx.Client() as client:
                for product in request.products:
                    logger.info(f"Fetching product: {product.product_id}")

                    product_url = f"{PRODUCT_SERVICE_URL}/products/{product.product_id}"
                    res = client.get(product_url)

                    if res.status_code != 200:
                        logger.error(
                            f"Failed to fetch product {product.product_id}: {res.text}")
                        raise Exception(
                            f"Product {product.product_id} not found")

                    product_data = res.json()
                    price = product_data['price']

                    total_price += price * product.quantity
                    product_details.append(
                        OrderedProduct(
                            product_id=product.product_id,
                            quantity=product.quantity
                        )
                    )

            # 2. Save to Order Database
            new_order = Order(
                account_id=request.account_id,
                total_price=total_price,
                status="PENDING",
                products=product_details  # Add the list of products
            )

            db.add(new_order)
            db.commit()
            db.refresh(new_order)

            logger.info(f"Order {new_order.id} created successfully.")

            # 3. Publish to Kafka
            # (The recommender will want to know about this purchase)
            event_payload = {
                "type": "order_created",
                "data": {
                    "order_id": new_order.id,
                    "account_id": new_order.account_id,
                    "total_price": new_order.total_price,
                    "products": [
                        {"product_id": p.product_id, "quantity": p.quantity}
                        for p in new_order.products
                    ]
                }
            }
            producer.send("order_events", value=event_payload)
            producer.flush()
            logger.info("Published 'order_created' event to Kafka.")

            # 4. Create and return gRPC response
            grpc_products = [
                order_pb2.OrderProduct(
                    product_id=p.product_id, quantity=p.quantity)
                for p in new_order.products
            ]

            grpc_order = order_pb2.Order(
                id=new_order.id,
                account_id=new_order.account_id,
                total_price=new_order.total_price,
                status=new_order.status,
                products=grpc_products
            )

            return order_pb2.CreateOrderResponse(order=grpc_order)

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            db.rollback()
            context.set_details(f'Internal server error: {e}')
            context.set_code(grpc.StatusCode.INTERNAL)
            return order_pb2.CreateOrderResponse()
        finally:
            db.close()


# --- Server Setup ---

def serve():
    create_db_and_tables()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderService(), server)

    port = '50053'  # New port for this service
    server.add_insecure_port(f'[::]:{port}')

    logger.info(f"🚀 Order gRPC server started on port {port}...")

    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
