import grpc
from concurrent import futures

from proto.pb import recommender_pb2, recommender_pb2_grpc
from app.services.recommender import recommender
from app.db.models import Product
from app.db.session import ReplicaSession


def _fetch_grpc_products(product_ids):
    """Helper method to fetch products from the DB and return gRPC ProductReplica objects."""
    with ReplicaSession() as session:
        products = (
            session.query(Product)
            .filter(Product.id.in_(product_ids))
            .all()
        )

    grpc_products = [
        recommender_pb2.ProductReplica(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
        )
        for product in products
    ]
    return grpc_products


def _handle_exception(context, error_message):
    """Helper method to set gRPC status code and details."""
    context.set_code(grpc.StatusCode.INTERNAL)
    context.set_details(error_message)


class RecommenderServiceServicer(recommender_pb2_grpc.RecommenderServiceServicer):

    def GetRecommendations(self, request, context):
        user_id = request.user_id
        skip = request.skip or 0  # default to 0 if not set
        take = request.take or 5  # default to 5 if not set

        try:
            # Get recommended product IDs
            recommended_product_ids = recommender.recommend_on_user_id(
                user_id=user_id,
                skip=skip,
                take=take
            )

            # Fetch product details as gRPC objects
            grpc_products = _fetch_grpc_products(recommended_product_ids)
            return recommender_pb2.RecommendationResponse(
                recommended_products=grpc_products
            )

        except Exception as e:
            _handle_exception(
                context, f"Failed to get recommendations: {str(e)}")
            return recommender_pb2.RecommendationResponse()

    def GetRecommendationsBasedOnViewed(self, request, context):
        viewed_product_ids = request.ids  # Match the .proto file
        skip = request.skip or 0
        take = request.take or 5

        try:
            recommended_product_ids = recommender.recommend_on_viewed_ids(
                viewed_ids=viewed_product_ids,
                skip=skip,
                take=take
            )

            # Fetch product details as gRPC objects
            grpc_products = _fetch_grpc_products(recommended_product_ids)
            return recommender_pb2.RecommendationResponse(
                recommended_products=grpc_products
            )

        except Exception as e:
            _handle_exception(
                context, f"Failed to get recommendations: {str(e)}")
            return recommender_pb2.RecommendationResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    recommender_pb2_grpc.add_RecommenderServiceServicer_to_server(
        RecommenderServiceServicer(), server
    )
    # --- IMPORTANT ---
    # Change port to 50052 to avoid conflict with Account service
    server.add_insecure_port('[::]:50052')
    print("gRPC server started on port 50052")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
