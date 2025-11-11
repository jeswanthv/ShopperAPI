import grpc
import time
from concurrent import futures
from sqlalchemy.orm import Session
import logging

# Import our generated gRPC files
from .proto.pb import account_pb2, account_pb2_grpc

# Import database and repository
from .database import SessionLocal, create_db_and_tables
from .repository import AccountRepository

# Import auth helpers
from .auth import create_access_token

# Import wrapper types
from google.protobuf import wrappers_pb2

# --- Our gRPC Service Implementation ---


class AccountService(account_pb2_grpc.AccountServiceServicer):

    def __init__(self):
        self.repo = AccountRepository()

    def Register(self, request, context):
        logging.info(f"Register request received for: {request.email}")
        db: Session = SessionLocal()
        try:
            # 1. Check if user already exists
            db_account = self.repo.get_account_by_email(
                db, email=request.email)
            if db_account:
                context.set_details('Email already registered')
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                return wrappers_pb2.StringValue()

            # 2. Create new user
            new_account = self.repo.create_account(
                db,
                name=request.name,
                email=request.email,
                password=request.password
            )

            # 3. Create access token
            token = create_access_token(data={"sub": str(new_account.id)})

            return wrappers_pb2.StringValue(value=token)

        except Exception as e:
            logging.error(f"Register error: {e}")
            context.set_details('Internal server error')
            context.set_code(grpc.StatusCode.INTERNAL)
            return wrappers_pb2.StringValue()
        finally:
            db.close()

    def Login(self, request, context):
        logging.info(f"Login request received for: {request.email}")
        db: Session = SessionLocal()
        try:
            # 1. Find user
            db_account = self.repo.get_account_by_email(
                db, email=request.email)
            if not db_account:
                context.set_details('Invalid credentials')
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                return wrappers_pb2.StringValue()

            # 2. Check password
            if not self.repo.verify_password(request.password, db_account.password):
                context.set_details('Invalid credentials')
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                return wrappers_pb2.StringValue()

            # 3. Create access token
            token = create_access_token(data={"sub": str(db_account.id)})

            return wrappers_pb2.StringValue(value=token)

        except Exception as e:
            logging.error(f"Login error: {e}")
            context.set_details('Internal server error')
            context.set_code(grpc.StatusCode.INTERNAL)
            return wrappers_pb2.StringValue()
        finally:
            db.close()

    def GetAccount(self, request, context):
        logging.info(f"GetAccount request received for ID: {request.value}")
        db: Session = SessionLocal()
        try:
            db_account = self.repo.get_account_by_id(db, user_id=request.value)

            if not db_account:
                context.set_details('Account not found')
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return account_pb2.AccountResponse()

            # 4. Map SQLAlchemy model to gRPC message
            account_msg = account_pb2.Account(
                id=db_account.id,
                name=db_account.name,
                email=db_account.email
            )
            return account_pb2.AccountResponse(account=account_msg)

        except Exception as e:
            logging.error(f"GetAccount error: {e}")
            context.set_details('Internal server error')
            context.set_code(grpc.StatusCode.INTERNAL)
            return account_pb2.AccountResponse()
        finally:
            db.close()

# --- Server Setup ---


def serve():
    # Make sure our tables are created
    create_db_and_tables()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    account_pb2_grpc.add_AccountServiceServicer_to_server(
        AccountService(), server)

    port = '50051'
    server.add_insecure_port(f'[::]:{port}')

    print(f"🚀 Account gRPC server started on port {port}...")
    logging.info(f"Server listening on [::]:{port}")

    server.start()
    try:
        while True:
            time.sleep(86400)  # Keep the server alive
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
