import grpc
import random
import string

from .proto.pb import account_pb2, account_pb2_grpc
from google.protobuf import wrappers_pb2


def run_test():
    channel = grpc.insecure_channel('localhost:50051')
    stub = account_pb2_grpc.AccountServiceStub(channel)

    # Generate a random email
    random_id = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=6))
    email = f"test_{random_id}@example.com"
    password = "password123"
    name = "Test User"

    print(f"--- 1. Registering {email} ---")
    try:
        register_request = account_pb2.RegisterRequest(
            name=name,
            email=email,
            password=password
        )
        response = stub.Register(register_request)
        print(
            f"✅ Register successful. Token (truncated): {response.value[:20]}...")

        # Save the token for the next test
        token = response.value
    except grpc.RpcError as e:
        print(f"❌ Register failed: {e.details()}")
        return

    print(f"\n--- 2. Logging in {email} ---")
    try:
        login_request = account_pb2.LoginRequest(
            email=email,
            password=password
        )
        response = stub.Login(login_request)
        print(
            f"✅ Login successful. Token (truncated): {response.value[:20]}...")
    except grpc.RpcError as e:
        print(f"❌ Login failed: {e.details()}")

    print(f"\n--- 3. Testing Login with wrong password ---")
    try:
        login_request = account_pb2.LoginRequest(
            email=email,
            password="wrongpassword"
        )
        stub.Login(login_request)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            print(f"✅ Correctly failed with: {e.details()}")
        else:
            print(f"❌ Test failed unexpectedly: {e.details()}")


if __name__ == '__main__':
    run_test()
