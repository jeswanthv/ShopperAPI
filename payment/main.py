import grpc
import asyncio
import json
import logging
import uvicorn
import httpx  # For calling the Order service
from concurrent import futures
from sqlalchemy.orm import Session
from fastapi import FastAPI, Request, HTTPException
import grpc.aio
import time

# gRPC imports
from .proto.pb import payment_pb2, payment_pb2_grpc
from .proto.pb import order_pb2, order_pb2_grpc

# FastAPI imports
from fastapi import FastAPI

# Local imports
from .database import SessionLocal, create_db_and_tables
from .models import Product, Transaction

# --- Service Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- gRPC Service Implementation ---


class PaymentService(payment_pb2_grpc.PaymentServiceServicer):

    async def CreateCheckoutSession(self, request, context):
        logger.info(
            f"CreateCheckoutSession request for order ID: {request.order_id}")
        db: Session = SessionLocal()
        try:
            total_price = 0.0

            # 1. Calculate total price from our local product DB
            for item in request.products:
                product = db.query(Product).filter_by(
                    id=item.product_id).first()
                if not product:
                    await context.abort(grpc.StatusCode.NOT_FOUND, f"Product {item.product_id} not found")
                    return

                total_price += product.price * item.quantity

            # 2. Create a new transaction in our DB
            new_transaction = Transaction(
                order_id=request.order_id,
                user_id=request.user_id,
                total_price=total_price,
                status="PENDING"
            )
            db.add(new_transaction)
            db.commit()
            db.refresh(new_transaction)

            # 3. Simulate creating a checkout session
            # This is the URL the user would be redirected to.
            # It includes our /webhook URL so the provider can notify us.

            # THIS IS OUR SIMULATED PAYMENT PAGE
            checkout_url = f"http://localhost:8003/simulate_payment/{new_transaction.id}"

            return payment_pb2.CreateCheckoutResponse(checkout_url=checkout_url)

        except Exception as e:
            logger.error(f"Error in CreateCheckoutSession: {e}")
            db.rollback()
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
        finally:
            db.close()


# --- FastAPI (Webhook) Implementation ---

app = FastAPI()

ORDER_SERVICE_GRPC_URL = 'localhost:50053'


@app.post("/webhook/payment")
async def payment_webhook(request: Request):
    # ... (data = await request.json(), etc.)

    logger.info(
        f"Webhook received for transaction {transaction_id} with status {payment_status}")

    db: Session = SessionLocal()
    try:
        # 1. Find and Update the transaction
        transaction = db.query(Transaction).filter_by(
            id=transaction_id).first()
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found!")
            raise HTTPException(
                status_code=404, detail="Transaction not found")

        transaction.status = payment_status
        transaction.payment_gateway_id = data.get(
            "payment_gateway_id", "sim_123")
        db.commit()

        # 2. --- UN-MOCK THE CALL ---
        # Call the Order service to update its status
        if payment_status == "SUCCESS":  # Only update if payment was successful
            logger.info(
                f"Calling Order service to update order {transaction.order_id} to PAID")

            async with grpc.aio.insecure_channel(ORDER_SERVICE_GRPC_URL) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)
                await stub.UpdateOrderStatus(
                    order_pb2.UpdateOrderStatusRequest(
                        order_id=transaction.order_id,
                        status="PAID"  # Set a clear status
                    )
                )
            logger.info(
                f"Order service updated for order {transaction.order_id}")

        return {"status": "webhook received"}

    except Exception as e:
        logger.error(f"Error in payment_webhook: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()


@app.get("/simulate_payment/{transaction_id}")
async def simulate_payment_page(transaction_id: int):
    """
    This is a FAKE payment page. It just shows the user
    two buttons: "Pay" or "Cancel".
    """
    return {
        "message": f"Simulated Payment for Transaction ID: {transaction_id}",
        "success_url": f"/simulate_payment_action/{transaction_id}/SUCCESS",
        "fail_url": f"/simulate_payment_action/{transaction_id}/FAILED"
    }


@app.get("/simulate_payment_action/{transaction_id}/{status}")
async def simulate_payment_action(transaction_id: int, status: str):
    """
    This is what the "Pay" or "Cancel" buttons call.
    It simulates the payment provider by calling our *own* webhook.
    """
    webhook_url = "http://localhost:8003/webhook/payment"
    payload = {
        "transaction_id": transaction_id,
        "status": status,
        "payment_gateway_id": f"sim_{time.time()}"
    }

    async with httpx.AsyncClient() as client:
        try:
            await client.post(webhook_url, json=payload)
            return {"message": f"Payment simulated as {status}. Webhook called."}
        except Exception as e:
            return {"error": f"Failed to call webhook: {e}"}

# --- Server Runner ---


async def serve_grpc():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(
        PaymentService(), server)
    port = '50054'  # New port
    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"🚀 Payment gRPC server started on port {port}...")
    await server.start()
    await server.wait_for_termination()


async def serve_fastapi():
    port = 8003  # New port
    config = uvicorn.Config("payment.main:app", host="0.0.0.0",
                            port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info(f"🚀 Payment FastAPI server started on port {port}...")
    await server.serve()


async def main():
    # Create tables before starting
    create_db_and_tables()

    # Run both servers concurrently
    await asyncio.gather(
        serve_grpc(),
        serve_fastapi()
    )

if __name__ == '__main__':
    asyncio.run(main())
