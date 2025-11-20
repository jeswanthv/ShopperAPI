# Python Microservices: E-Commerce API (FastAPI, gRPC, Kafka, GraphQL)

This repository contains a complete e-commerce microservices backend built from scratch in Python. It demonstrates a modern, decoupled architecture using gRPC for internal communication, Kafka for event-driven data flow, and a GraphQL gateway as the public-facing API.

This project is a Python re-implementation of a popular Go-based microservices architecture, built as part of an intensive 2-week learning sprint.

---

## 🚀 Project Status: Completed ✅

All planned services and integrations have been implemented.

### Features Implemented:

- [x] **Core Infrastructure:** Docker Compose setup with PostgreSQL (x4), Kafka, Zookeeper, and Elasticsearch.
- [x] **Account Service:** gRPC service for secure user registration and login (JWT).
- [x] **Product Service:** FastAPI REST service for product management, Elasticsearch indexing, and Kafka event publishing.
- [x] **Recommender Service:** Hybrid service that consumes Kafka events to build a local dataset and serves recommendations via gRPC.
- [x] **Order Service:** gRPC service for order management; acts as an HTTP client to fetch product prices and a Kafka producer for order events.
- [x] **Payment Service:** Complex hybrid service handling transactions, consuming product events, and processing webhooks to update order status via gRPC.
- [x] **GraphQL Gateway:** A unified API Gateway (Strawberry) that federates requests to all backend microservices.

---

## 🏗️ System Architecture

The system uses a **Gateway Pattern**. Clients communicate only with the GraphQL Gateway, which routes requests to backend services using gRPC or HTTP. Asynchronous tasks (like recommendations or data syncing) are handled via Kafka events.

### Service Breakdown

| Service         | Type      | Port             | Database | Responsibility                                          |
| :-------------- | :-------- | :--------------- | :------- | :------------------------------------------------------ |
| **Gateway**     | GraphQL   | `8080`           | -        | Unified entry point; aggregates data from all services. |
| **Account**     | gRPC      | `50051`          | Postgres | User auth & management.                                 |
| **Product**     | HTTP      | `8002`           | Elastic  | Product catalog & search.                               |
| **Recommender** | gRPC      | `50052`          | Postgres | Product recommendations (ML).                           |
| **Order**       | gRPC      | `50053`          | Postgres | Order processing & history.                             |
| **Payment**     | gRPC/HTTP | `50054` / `8003` | Postgres | Payments & Webhook processing.                          |

---

## 🛠️ Technology Stack

- **Language:** Python 3.10+
- **Frameworks:**
  - **FastAPI:** High-performance web framework for REST and GraphQL.
  - **gRPC (`grpcio`):** Internal service-to-service communication.
  - **Strawberry:** GraphQL library for Python.
- **Data:**
  - **PostgreSQL:** Relational data (SQLAlchemy ORM).
  - **Elasticsearch:** Full-text search engine.
- **Messaging:**
  - **Apache Kafka:** Event streaming platform (`kafka-python`).
- **Infrastructure:**
  - **Docker & Docker Compose:** Container orchestration.

---

## 🚀 Getting Started

### 1. Start Infrastructure

Run the following to start all databases (PostgreSQL, Elasticsearch) and the message broker (Kafka/Zookeeper).

```bash
docker-compose up -d
```

### 2\. Setup Services

Open separate terminals for each service. For the first run, install dependencies and setup the database in each folder:

```bash
# Example for one service (repeat for account, product, etc.)
cd service_name
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run DB setup script (if applicable)
python database.py
```

### 3\. Run the Microservices

You will need **8 terminals** to run the full stack (servers + consumers).

1.  **Account Service:**
    `cd account && python main.py`
2.  **Product Service:**
    `cd product && uvicorn main:app --port 8002 --reload`
3.  **Recommender Consumer:**
    `cd recommender && python app/entry/sync.py`
4.  **Recommender Server:**
    `cd recommender && python app/entry/main.py`
5.  **Order Service:**
    `cd order && python main.py`
6.  **Payment Consumer:**
    `cd payment && python consumer.py`
7.  **Payment Server:**
    `cd payment && python main.py`
8.  **GraphQL Gateway:**
    `cd graphql && uvicorn main:app --port 8080 --reload`

---

## 🎮 Usage (GraphQL Playground)

Once everything is running, open your browser to:
👉 **http://localhost:8080/graphql**

You can use the interactive Playground to test the entire flow:

**1. Create a User**

```graphql
mutation {
  register(name: "Test User", email: "user@test.com", password: "password123") {
    token
  }
}
```

**2. Get Recommendations**

```graphql
query {
  recommendations(userId: "1") {
    id
    name
    price
  }
}
```

**3. Create an Order**

```graphql
mutation {
  createOrder(
    accountId: 1
    products: [{ productId: "YOUR_PRODUCT_ID", quantity: 1 }]
  ) {
    id
    totalPrice
    status
  }
}
```

**4. Pay for Order**

```graphql
mutation {
  checkout(
    userId: 1
    orderId: 1
    email: "user@test.com"
    products: [{ productId: "YOUR_PRODUCT_ID", quantity: 1 }]
  ) {
    checkoutUrl
  }
}
```

_(Click the returned `checkoutUrl` to simulate a successful payment\!)_
