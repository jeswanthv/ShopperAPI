import strawberry
import grpc
import httpx
import logging
from typing import List, Optional
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

# Import Generated gRPC Modules
from .protos.pb import payment_pb2, payment_pb2_grpc
from .protos.pb import order_pb2, order_pb2_grpc
from .protos.pb import account_pb2, account_pb2_grpc
from .protos.pb import recommender_pb2, recommender_pb2_grpc

# --- Configuration ---
# We assume services are running on localhost for now
ACCOUNT_GRPC = "localhost:50051"
PRODUCT_API_URL = "http://localhost:8002"  # REST API
RECOMMENDER_GRPC = "localhost:50052"
ORDER_GRPC = "localhost:50053"
PAYMENT_GRPC = "localhost:50054"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GraphQL Types (The "View" Model) ---


@strawberry.type
class ProductType:
    id: str
    name: str
    description: str
    price: float
    account_id: int


@strawberry.type
class AccountType:
    id: int
    name: str
    email: str


@strawberry.type
class OrderProductType:
    product_id: str
    quantity: int


@strawberry.type
class OrderType:
    id: int
    account_id: int
    total_price: float
    status: str
    products: List[OrderProductType]


@strawberry.type
class AuthResponseType:
    token: str


@strawberry.type
class CheckoutResponseType:
    checkout_url: str

# --- Input Types (For Mutations) ---


@strawberry.input
class OrderProductInput:
    product_id: str
    quantity: int

# --- Resolvers (The Logic) ---


async def get_recommendations(user_id: str) -> List[ProductType]:
    """Calls Recommender Service (gRPC)"""
    try:
        async with grpc.aio.insecure_channel(RECOMMENDER_GRPC) as channel:
            stub = recommender_pb2_grpc.RecommenderServiceStub(channel)
            req = recommender_pb2.RecommendationRequestForUserId(
                user_id=user_id, take=5)
            response = await stub.GetRecommendations(req)

            return [
                ProductType(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    price=p.price,
                    account_id=0  # Recommender proto doesn't have account_id, defaulting to 0
                ) for p in response.recommended_products
            ]
    except Exception as e:
        logger.error(f"Recommender error: {e}")
        return []


async def register_user(name: str, email: str, password: str) -> AuthResponseType:
    """Calls Account Service (gRPC)"""
    async with grpc.aio.insecure_channel(ACCOUNT_GRPC) as channel:
        stub = account_pb2_grpc.AccountServiceStub(channel)
        response = await stub.Register(
            account_pb2.RegisterRequest(
                name=name, email=email, password=password)
        )
        return AuthResponseType(token=response.value)


async def create_order(account_id: int, products: List[OrderProductInput]) -> OrderType:
    """Calls Order Service (gRPC)"""
    async with grpc.aio.insecure_channel(ORDER_GRPC) as channel:
        stub = order_pb2_grpc.OrderServiceStub(channel)

        # Map input types to gRPC message types
        grpc_products = [
            order_pb2.OrderProduct(
                product_id=p.product_id, quantity=p.quantity)
            for p in products
        ]

        response = await stub.CreateOrder(
            order_pb2.CreateOrderRequest(
                account_id=account_id, products=grpc_products)
        )
        order = response.order

        return OrderType(
            id=int(order.id),
            account_id=int(order.account_id),
            total_price=order.total_price,
            status=order.status,
            products=[
                OrderProductType(product_id=p.product_id, quantity=p.quantity)
                for p in order.products
            ]
        )


async def create_checkout(user_id: int, order_id: int, email: str, products: List[OrderProductInput]) -> CheckoutResponseType:
    """Calls Payment Service (gRPC)"""
    async with grpc.aio.insecure_channel(PAYMENT_GRPC) as channel:
        stub = payment_pb2_grpc.PaymentServiceStub(channel)

        grpc_products = [
            payment_pb2.CartItem(product_id=p.product_id, quantity=p.quantity)
            for p in products
        ]

        response = await stub.CreateCheckoutSession(
            payment_pb2.CreateCheckoutRequest(
                user_id=user_id,
                order_id=order_id,
                email=email,
                products=grpc_products,
                # redirectURL="http://localhost:3000/success"
            )
        )
        return CheckoutResponseType(checkout_url=response.checkout_url)

# --- Schema Definition ---


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "The Gateway is Alive!"

    @strawberry.field
    async def recommendations(self, user_id: str) -> List[ProductType]:
        return await get_recommendations(user_id)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def register(self, name: str, email: str, password: str) -> AuthResponseType:
        return await register_user(name, email, password)

    @strawberry.mutation
    async def create_order(self, account_id: int, products: List[OrderProductInput]) -> OrderType:
        return await create_order(account_id, products)

    @strawberry.mutation
    async def checkout(self, user_id: int, order_id: int, email: str, products: List[OrderProductInput]) -> CheckoutResponseType:
        return await create_checkout(user_id, order_id, email, products)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
