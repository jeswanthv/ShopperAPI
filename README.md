# Python Microservices: E-Commerce API (FastAPI, gRPC, Kafka, GraphQL)

This repository contains a complete e-commerce microservices backend built from scratch in Python. It demonstrates a modern, decoupled architecture using gRPC for internal communication, Kafka for event-driven data flow, and a GraphQL gateway as the public-facing API.

---

## 🚀 Project Status: Backend Completed / Ready for UI ✅

The entire backend infrastructure is operational. The project is now ready for a frontend application (React, Vue, Mobile) to be connected.

### Features Implemented:

- [x] **Core Infrastructure:** Docker Compose setup with PostgreSQL (x4), Kafka, Zookeeper, and Elasticsearch.
- [x] **Account Service:** gRPC service for secure user registration and login (JWT).
- [x] **Product Service:** FastAPI REST service for product management, Elasticsearch indexing, and Kafka event publishing.
- [x] **Recommender Service:** Hybrid service that consumes Kafka events to build a local dataset and serves recommendations via gRPC.
- [x] **Order Service:** gRPC service for order management; acts as an HTTP client to fetch product prices and a Kafka producer for order events.
- [x] **Payment Service:** Complex hybrid service handling transactions, consuming product events, and processing webhooks to update order status via gRPC.
- [x] **GraphQL Gateway:** A unified API Gateway (Strawberry) that federates requests to all backend microservices.

### 🔮 Future Enhancements (Phase 2):

- [ ] **Frontend UI:** Build a React/Next.js dashboard to visualize products and orders.
- [ ] **Authentication UI:** Login/Register forms consuming the GraphQL mutations.
- [ ] **Real-time Updates:** Use GraphQL Subscriptions for real-time order status updates.

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

Here is a **Developer Commands** section you can add to your `README.md`. It documents the `Makefile` commands we just set up, making it much easier for others (and future you) to run the project.

You can add this right after the **"Getting Started"** section.

````markdown
## ⚡ Quick Start (Makefile)

To simplify development, a `Makefile` is included to automate the setup, generation of gRPC code, and running of services.

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- `pip`

### Available Commands

| Command            | Description                                                                                                            |
| :----------------- | :--------------------------------------------------------------------------------------------------------------------- |
| **`make infra`**   | Starts the Docker infrastructure (Postgres, Kafka, Elasticsearch, Zookeeper).                                          |
| **`make install`** | Iterates through all service folders, creates virtual environments, and installs dependencies from `requirements.txt`. |
| **`make protos`**  | Compiles `.proto` files into Python gRPC code for all services.                                                        |
| **`make db`**      | Runs the database initialization scripts for Account, Order, Payment, and Recommender services.                        |
| **`make run`**     | Uses `honcho` to run **all 8 services** (servers + consumers) + the Frontend in a single terminal window.              |

### 🚀 The "Zero to Hero" Workflow

If you are setting this up on a fresh machine, run these commands in order:

1. **Start Infrastructure:**
   ```bash
   make infra
   ```
````

2.  **Setup Project:**

        ```bash
        make install
        make protos
        make db
        ```

    _(Wait a moment for databases to initialize)_

3.  **Run Everything:**

    ```bash
    make run
    ```

    _All backend logs will appear in this terminal with different colors. Press `Ctrl+C` to stop everything._

## 🚀 Getting Started(Verbose way)

### 1. Start Infrastructure

Run the following to start all databases (PostgreSQL, Elasticsearch) and the message broker (Kafka/Zookeeper).

```bash
docker-compose up -d
```

````

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
````

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

```

```
