# Python Microservices: E-Commerce API (FastAPI, gRPC, Kafka)

This repository documents my journey building a complete e-commerce microservices backend from scratch in Python. The goal is to learn and implement a modern backend architecture using decoupled services, gRPC, and event-driven patterns with Kafka.

This project is a Python re-implementation of a popular Go-based microservices architecture.

---

## Account service Setup

## 🚀 How to Run the Service

### 1. Start the Database

From your `shopperAPI` project folder:

```bash
docker compose up -d
```

### 2.Run the Main Server

#### 1.Go to your `shopperAPI` root directory.

#### 2. Activate the virtual environment:

```
source account/venv/bin/activate
```

#### 3.Run the server as a module:

```
python -m account.main
```

### 3.Run the Test Client

#### 1.Open a new terminal and go to the `shopperAPI` root directory.

#### 2.Activate the virtual environment:

```
source account/venv/bin/activate
```

#### 3.Run the client as a module:

```
python -m account.client_test
```

## 🚀 Project Status: In Progress (Day 3 of 14)

This project is being built as part of an intensive 2-week learning sprint.

### Completed:

- [x] **Core Infrastructure:** `docker-compose.yaml` with PostgreSQL, Kafka, and Elasticsearch.
- [x] **Account Service:** A gRPC service for user registration and login, connected to PostgreSQL.
- [x] **Product Service:** A FastAPI REST service for creating products, saving them to Elasticsearch, and producing `product_created` events to Kafka.

### Next Steps:

- [ ] **Recommender Service:** Consume Kafka events and provide recommendations.
- [ ] **Order Service:** Handle order creation and service-to-service communication.
- [ ] **Payment Service:** Handle webhooks and update order status.
- [ ] **GraphQL Gateway:** Unify all services under a single API.

---

## 🏗️ System Architecture

This project consists of several independent services that communicate via gRPC (for direct requests) and Kafka (for events).

- **Account Service:** (Python, gRPC, PostgreSQL)
  - Manages user registration, login, and authentication (JWT).
- **Product Service:** (Python, FastAPI, Elasticsearch, Kafka Producer)
  - Manages the product catalog (create, read, search).
  - Saves products to Elasticsearch for fast text search.
  - Publishes events (e.g., `product_created`) to Kafka.
- **Recommender Service:** (Python, gRPC, Kafka Consumer)
  - Consumes events from Kafka to learn about user behavior.
  - Exposes a gRPC endpoint for product recommendations.
- **Order Service:** (Python, gRPC, PostgreSQL)
  - Handles order creation and history.
  - Communicates with the Product service to get product details.
- **Payment Service:** (Python, gRPC, FastAPI, Kafka
