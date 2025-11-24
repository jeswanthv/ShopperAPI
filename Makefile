# Define the services directories
PYTHON := /opt/homebrew/bin/python3
SERVICES := account product recommender order payment gateway

.PHONY: all install protos db run help

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies for all services"
	@echo "  make protos     - Generate gRPC code for all services (with import fixes)"
	@echo "  make db         - Initialize databases (create tables)"
	@echo "  make infra      - Start Docker infrastructure (Postgres, Kafka, Elastic)"
	@echo "  make run        - Run all services locally using Honcho"

# --- 1. Installation ---
install:
	@echo "📦 Installing dependencies for all services..."
	@echo ">> Checking for Honcho..."
	@which honcho > /dev/null || (echo "❌ Honcho not found. Please run: pipx install honcho" && exit 1)
	@for service in $(SERVICES); do \
		echo ">> Installing $$service..."; \
		cd $$service && $(PYTHON) -m venv venv && . venv/bin/activate && pip install -r requirements.txt; \
		cd ..; \
	done

# --- 2. Proto Generation ---
protos:
	@echo "🔄 Generating gRPC code..."
	
	# Account
	@echo ">> Account Protos..."
	@cd account && . venv/bin/activate && mkdir -p proto/pb && \
		python -m grpc_tools.protoc -I=./proto --python_out=./proto/pb --grpc_python_out=./proto/pb ./proto/account.proto && \
		sed -i '' 's/^import \(.*_pb2\)/from . import \1/' ./proto/pb/*_pb2_grpc.py
	
	# Recommender
	@echo ">> Recommender Protos..."
	@cd recommender && . venv/bin/activate && mkdir -p proto/pb && \
		python -m grpc_tools.protoc -I=proto --python_out=./proto/pb --grpc_python_out=./proto/pb recommender.proto && \
		sed -i '' 's/^import \(.*_pb2\)/from . import \1/' ./proto/pb/*_pb2_grpc.py
	
	# Order
	@echo ">> Order Protos..."
	@cd order && . venv/bin/activate && mkdir -p proto/pb && \
		python -m grpc_tools.protoc -I=./proto --python_out=./proto/pb --grpc_python_out=./proto/pb ./proto/order.proto && \
		sed -i '' 's/^import \(.*_pb2\)/from . import \1/' ./proto/pb/*_pb2_grpc.py
	
	# Payment 
	@echo ">> Payment Protos..."
	@cd payment && . venv/bin/activate && mkdir -p proto/pb && \
		cp ../order/proto/order.proto proto/ && \
		python -m grpc_tools.protoc -I=./proto --python_out=./proto/pb --grpc_python_out=./proto/pb ./proto/payment.proto ./proto/order.proto && \
		sed -i '' 's/^import \(.*_pb2\)/from . import \1/' ./proto/pb/*_pb2_grpc.py
	
	# Gateway 
	@echo ">> Gateway Protos..."
	@cd gateway && . venv/bin/activate && mkdir -p protos/pb && \
		cp ../account/proto/account.proto protos/ && \
		cp ../order/proto/order.proto protos/ && \
		cp ../payment/proto/payment.proto protos/ && \
		cp ../recommender/proto/recommender.proto protos/ && \
		python -m grpc_tools.protoc -I=./protos --python_out=./protos/pb --grpc_python_out=./protos/pb protos/*.proto && \
		sed -i '' 's/^import \(.*_pb2\)/from . import \1/' ./protos/pb/*_pb2_grpc.py
	
	@echo "✅ Protos generated."

# --- 3. Database Init ---
db:
	@echo "🗄️  Initializing databases..."
	@. account/venv/bin/activate && python -m account.database
	@. recommender/venv/bin/activate && cd recommender && python -m app.db.session
	@. order/venv/bin/activate && python -m order.database
	@. payment/venv/bin/activate && python -m payment.database
	@echo "✅ Databases initialized."

# --- 4. Infrastructure ---
infra:
	@echo "🐳 Starting Docker Infrastructure..."
	@docker compose up -d
	@echo "✅ Infrastructure running."

# --- 5. Run Everything ---
run:
	@echo "🚀 Starting the E-Commerce Microservices Mesh..."
	@honcho start