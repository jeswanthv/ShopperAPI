# Python Microservices: E-Commerce API (FastAPI, gRPC, Kafka)

This repository documents my journey building a complete e-commerce microservices backend from scratch in Python. The goal is to learn and implement a modern backend architecture using decoupled services, gRPC, and event-driven patterns with Kafka.

This project is a Python re-implementation of a popular Go-based microservices architecture.

---

## 🚀 Project Status: In Progress (Day 11 of 14)

This project is being built as part of an intensive 2-week learning sprint.

### Completed:

- [x] **Core Infrastructure:** `docker-compose.yaml` with PostgreSQL (x4), Kafka, and Elasticsearch.
- [x] **Account Service:** A gRPC service for user registration and login.
- [x] **Product Service:** A FastAPI REST service for product CRUD and producing Kafka events.
- [x] **Recommender Service:** A gRPC service that consumes Kafka events to its own DB.
- [x] **Order Service:** A gRPC service that handles order creation and status updates.
- [x] **Payment Service:** A hybrid service that manages transactions and webhooks.
- [x] **Integration Loop:** The Payment service successfully calls the Order service via gRPC to update order status upon payment success.

### Next Steps:

- [ ] **GraphQL Gateway:** Unify all services under a single API.

---

## 🏗️ System Architecture

This project consists of several independent services that communicate via gRPC (for direct requests) and Kafka (for events).

- **Account Service:** (Python, gRPC, PostgreSQL)

  - **Port:** `50051` (gRPC)
  - **Database:** `account_db` (PostgreSQL on port 5432)
  - Manages user registration, login, and authentication (JWT).

- **Product Service:** (Python, FastAPI, Elasticsearch, Kafka Producer)

  - **Port:** `8002` (HTTP/FastAPI)
  - **Database:** `product_db` (Elasticsearch on port 9200)
  - Manages the product catalog (create, read, search).
  - Publishes events to the `product_events` Kafka topic.

- **Recommender Service:** (Python, gRPC, Kafka Consumer)

  - **Port:** `50052` (gRPC)
  - **Database:** `recommender_db` (PostgreSQL on port 5433)
  - Consumes events from `product_events` topic to build its own product database.
  - Exposes a gRPC endpoint for product recommendations.

- **Order Service:** (Python, gRPC, PostgreSQL, Kafka Producer)

  - **Port:** `50053` (gRPC)
  - **Database:** `order_db` (PostgreSQL on port 5434)
  - Handles order creation.
  - **Talks to:** `Product Service` (via HTTP) to get prices.
  - **Publishes:** `order_created` events to the `order_events` Kafka topic.
  - **Accepts:** `UpdateOrderStatus` RPC calls from the Payment service.

- **Payment Service:** (Python, gRPC, FastAPI, Kafka Consumer)

  - **Ports:** `50054` (gRPC) & `8003` (HTTP/FastAPI)
  - **Database:** `payment_db` (PostgreSQL on port 5435)
  - **Consumes:** `product_events` to maintain a local price list.
  - **gRPC API:** Exposes `CreateCheckoutSession`.
  - **FastAPI API:** Exposes `/webhook/payment` to receive payment status updates.
  - **Talks to:** `Order Service` (via gRPC) to update order status to "PAID".

- **GraphQL Gateway:** (Python, FastAPI, Strawberry)
  - _(In Progress)_

---

## 🛠️ Technology Stack

- **Python 3.10+**
- **Frameworks:**
  - **FastAPI:** For REST/HTTP services and webhooks.
  - **gRPC (`grpcio`):** For high-performance service-to-service communication.
- **HTTP Client:**
  - **`httpx`**: For synchronous & asynchronous service-to-service HTTP requests.
- **Database & Storage:**
  - **PostgreSQL** with **SQLAlchemy**: Primary database for `account`, `order`, `recommender`, and `payment` services.
  - **Elasticsearch**: Search database for the `product` service.
- **Messaging:**
  - **Kafka (`kafka-python`):** As an event bus for asynchronous communication.
- **GraphQL:**
  - **Strawberry**: For building the GraphQL API gateway.
- **DevOps:**
  - **Docker & Docker Compose**: To build, run, and network all services and databases.
- **Authentication:**
  - **`bcrypt`**: For password hashing.
  - **`python-jose`**: For JWT generation and validation.

---

## 🚀 Getting Started

### 1. Start the Infrastructure

All databases and message brokers are managed by Docker Compose.

```bash
# This starts PostgreSQL (x4), Kafka, and Elasticsearch
docker-compose up -d
```

### 2\. Prepare Each Service

Each service runs in its own terminal and has its own virtual environment. Ensure you `pip install -r requirements.txt` in each service's directory.

**One-Time DB Setup:**

- **Account:** `cd account && source venv/bin/activate && python database.py`
- **Recommender:** `cd recommender && source venv/bin/activate && python app/db/session.py`
- **Order:** `cd order && source venv/bin/activate && python database.py`
- **Payment:** `cd payment && source venv/bin/activate && python database.py`

**Generate gRPC Code:**

- **Account:** `cd account && python -m grpc_tools.protoc -I=./proto --python_out=. --grpc_python_out=. ./proto/account.proto`
- **Recommender:** `cd recommender && mkdir -p generated/pb && python -m grpc_tools.protoc -I=. --python_out=./generated/pb --grpc_python_out=./generated/pb recommender.proto`
- **Order:** `cd order && python -m grpc_tools.protoc -I=./proto --python_out=. --grpc_python_out=. ./proto/order.proto`
- **Payment:** `cd payment && python -m grpc_tools.protoc -I=./proto --python_out=. --grpc_python_out=. ./proto/payment.proto`
  - _Note: Payment service also requires generating code for `order.proto` to act as a client._

### 3\. Run the Microservices

**Terminal 1: Account Service (gRPC)**

```bash
cd account
source venv/bin/activate
python main.py
```

> 🚀 Account gRPC server started on port 50051...

**Terminal 2: Product Service (FastAPI)**

```bash
cd product
source venv/bin/activate
uvicorn main:app --port 8002 --reload
```

> INFO: Uvicorn running on https://www.google.com/search?q=http://127.0.0.1:8002 (Press CTRL+C to quit)

**Terminal 3: Recommender Consumer (Kafka)**

```bash
cd recommender
source venv/bin/activate
python app/entry/sync.py
```

> Kafka consumer connected, listening for 'product_events'...

**Terminal 4: Recommender Server (gRPC)**

```bash
cd recommender
source venv/bin/activate
python app/entry/main.py
```

> gRPC server started on port 50052

**Terminal 5: Order Service (gRPC)**

```bash
cd order
source venv/bin/activate
python main.py
```

> 🚀 Order gRPC server started on port 50053...

**Terminal 6: Payment Consumer (Kafka)**

```bash
cd payment
source venv/bin/activate
python consumer.py
```

> INFO:root:Kafka consumer connected, listening for 'product_events'...

**Terminal 7: Payment Server (gRPC + FastAPI)**

```bash
cd payment
source venv/bin/activate
python main.py
```

> INFO:root:🚀 Payment gRPC server started on port 50054...
> INFO:root:🚀 Payment FastAPI server started on port 8003...
