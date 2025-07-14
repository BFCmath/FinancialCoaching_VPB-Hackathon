### **Phase 1: Context Confirmation & High-Level Strategy**

My understanding is that we are building a functional backend service, not just a mock. The "mock" aspect refers to using fast-to-develop local technologies (like a local database instance) that mirror the structure of future cloud services (like AWS RDS/DynamoDB and Cognito).

**Core Strategy:**
1.  **Decouple Logic from Server:** Keep the agent logic (`main.py`), business logic (`service.py`), and core utilities (`utils.py`) as intact as possible. The primary change will be modifying the data access layer within `utils.py` to talk to a real database instead of in-memory dictionaries.
2.  **API-First with FastAPI:** Expose all user-facing functionality through a well-defined FastAPI application. This API layer will be the single entry point for any front-end or client application.
3.  **Database-Driven State:** Move all state management (conversation history, user data, jars, transactions, agent locks) from Python global variables into a persistent database.
4.  **Stateless Authentication:** Implement JWT-based authentication, which is the industry standard for modern APIs and paves the way for using services like AWS Cognito.

---

### **Phase 2: Project Structure & Setup**

To ensure scalability, we should adopt a standard FastAPI project structure. I will modify your existing structure to be more robust.

**Proposed Folder Structure:**

```
/vpbank_financial_coach_backend/
├── agents/                  # Your existing agent logic (no changes needed initially)
│   ├── orchestrator/
│   │   └── main.py
│   └── base_worker.py
│
├── backend/                 # NEW: Main FastAPI application root
│   ├── api/                 # NEW: All API endpoint routers
│   │   ├── __init__.py
│   │   ├── routers/
│   │   │   ├── auth.py      # Endpoints for /register, /login
│   │   │   ├── chat.py      # Endpoint for the main agent interaction
│   │   │   ├── jars.py      # Endpoints for CRUD on Jars
│   │   │   ├── transactions.py # Endpoints for transactions
│   │   │   └── ... (fees, plans, etc.)
│   │   └── deps.py          # NEW: FastAPI dependencies (e.g., get_current_user)
│   │
│   ├── core/                # NEW: Configuration and core settings
│   │   ├── __init__.py
│   │   └── config.py        # App settings, DB URLs, secrets
│   │
│   ├── db/                  # NEW: Database connection and session management
│   │   ├── __init__.py
│   │   └── database.py      # Logic to connect to the database
│   │
│   ├── models/              # NEW: Pydantic models for DB objects & API requests/responses
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── jar.py
│   │   └── ... (transaction, fee, etc.)
│   │
│   ├── services/            # REFACTOR: Move your service.py here
│   │   └── __init__.py
│   │   └── financial_services.py # Renamed from service.py
│   │
│   ├── utils/               # REFACTOR: Move your utils.py here
│   │   └── __init__.py
│   │   └── db_utils.py      # Renamed from utils.py, will be modified for real DB
│   │
│   └── main.py              # NEW: Main FastAPI app instantiation
│
└── requirements.txt         # Project dependencies
```

---

### **Phase 3: Database - The Foundation**

This is the most critical change: replacing the in-memory storage with a real database. You prefer NoSQL, which is an excellent choice for much of this data.

**Technology Choice: MongoDB**
*   **Why?** It's a document-based NoSQL database that is extremely fast to develop with. Its flexible schema is perfect for `ConversationHistory` and `BudgetPlan`. It can also handle the more structured data (Jars, Transactions) effectively. AWS offers a managed MongoDB-compatible service called **DocumentDB**, making the future migration straightforward.
*   **Driver:** We will use `motor`, the official asynchronous driver for MongoDB, which integrates perfectly with FastAPI's async nature.

**Database Design & Migration Plan:**

1.  **Schema Definition (`backend/models/`):**
    *   We will translate the `dataclasses` from your `database.py` into Pydantic models. These models will serve a dual purpose: defining the structure for API requests/responses and for data stored in MongoDB.
    *   We will add a `User` model to store user credentials.
    *   Each model will include a `user_id` field to ensure data is partitioned per user.

2.  **Database Connection (`backend/db/database.py`):**
    *   A simple module to establish and manage the connection to the MongoDB server using `motor`.

3.  **Data Logic Refactor (`backend/utils/db_utils.py`):**
    *   This is where the core work happens. We will rewrite every function from your original `utils.py`.
    *   **Example (`get_all_jars`):**
        *   **Old:** `return list(JARS_STORAGE.values())`
        *   **New:** `async def get_all_jars(db: AsyncIOMotorClient, user_id: str) -> List[Jar]: return await db["jars"].find({"user_id": user_id}).to_list(100)`
    *   All functions will become `async` and will take a database client and `user_id` as arguments. They will perform actual database queries instead of manipulating global lists.

4.  **Handling the Conversation Lock (`ACTIVE_AGENT_CONTEXT`):**
    *   This global variable represents session-specific state. It's not suitable for a multi-user environment.
    *   **Solution:** We will use a fast key-value store like **Redis**. For "fast develop first," we can simulate this with another MongoDB collection. When a follow-up is required, we store `{ "user_id": "...", "locked_agent": "budget_advisor", "ttl": "..." }`. AWS ElastiCache provides a managed Redis service for the future.

---

### **Phase 4: Login/Logout/Session - User Management**

For fast development, we will implement a standard token-based authentication system.

**Technology Choice: JWT (JSON Web Tokens)**
*   **Why?** It's a stateless, secure, and widely adopted standard. This avoids managing server-side sessions and scales horizontally. This is exactly how **AWS Cognito** works, so the migration will be seamless.

**Implementation Plan (`backend/api/routers/auth.py` & `backend/api/deps.py`):**

1.  **User Model:** Create a `User` model in `backend/models/user.py` with fields like `username`, `email`, `hashed_password`.
2.  **Endpoints:**
    *   `POST /api/auth/register`: Takes a username/email and password, hashes the password using `passlib`, and saves the new user to the database.
    *   `POST /api/auth/token`: Takes username and password, verifies them, and if successful, creates and returns a JWT access token.
3.  **Security Dependency:**
    *   Create a FastAPI dependency (`get_current_user` in `deps.py`). This function will be required by all protected endpoints.
    *   It will extract the JWT from the `Authorization: Bearer <token>` header, decode it, validate it, and fetch the corresponding user from the database. This makes the user object available to any endpoint that needs it.

---

### **Phase 5: API Endpoint Development**

We will now expose the functionality from `service.py` via FastAPI routers.

**Plan (`backend/api/routers/`):**

*   **Chat Endpoint (`chat.py`):**
    *   `POST /api/chat/`
        *   **Protected:** Requires a valid JWT.
        *   **Request Body:** `{ "message": "How much did I spend on play last month?" }`
        *   **Logic:**
            1.  Gets the `current_user` from the JWT dependency.
            2.  Fetches the user's conversation history from MongoDB.
            3.  Checks for an agent lock for that user in the lock collection/Redis.
            4.  Calls the `orchestrator.process_task(task, history)`.
            5.  Saves the new conversation turn to the database.
            6.  Returns the agent's response.

*   **Jar Management Endpoints (`jars.py`):**
    *   `POST /api/jars/`: Calls `JarManagementService.create_jar`.
    *   `GET /api/jars/`: Calls `JarManagementService.list_jars`.
    *   `PUT /api/jars/{jar_name}`: Calls `JarManagementService.update_jar`.
    *   `DELETE /api/jars/{jar_name}`: Calls `JarManagementService.delete_jar`.
    *   All these endpoints will be protected and will operate on the data of the currently logged-in user.

*   **Other Endpoints:**
    *   We will create similar CRUD endpoints for **Transactions**, **Fees**, and **Plans**, mapping them directly to the methods in your `financial_services.py` (the refactored `service.py`).
    *   `PUT /api/user/settings`: An endpoint to allow the user to change their `TOTAL_INCOME`. This will update a field in the `User` document in the database.

This detailed plan provides a clear, step-by-step path to transform your current mock application into a fully functional, scalable, and cloud-ready backend service. We can start with Phase 2 (Project Structure) and Phase 3 (Database) as they are the foundational pillars for the rest of the development.