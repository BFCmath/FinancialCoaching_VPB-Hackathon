# VPBank Financial Coach Backend

A production-ready FastAPI backend that implements the multi-agent financial coaching system with MongoDB persistence, user authentication, and comprehensive RESTful API endpoints.

## 🏗️ Architecture Overview

This backend transforms the experimental agent testing lab into a production-ready application while maintaining 100% functional compatibility with the original agent system.

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Backend                       │
├─────────────────────────────────────────────────────────────┤
│  📱 REST API Layer (FastAPI)                               │
│  ├── Authentication (JWT)                                   │
│  ├── Jar Management                                         │
│  ├── Transaction Processing                                 │
│  ├── Fee Management                                         │
│  ├── Plan Management                                        │
│  └── Chat Interface (AI Orchestrator)                       │
├─────────────────────────────────────────────────────────────┤
│  🛠️ Service Layer (Business Logic)                         │
│  ├── JarManagementService                                   │
│  ├── TransactionService                                     │
│  ├── FeeManagementService                                   │
│  ├── PlanManagementService                                  │
│  ├── OrchestratorService (AI Agent Bridge)                  │
│  └── FinancialServices + Adapters                           │
├─────────────────────────────────────────────────────────────┤
│  🗄️ Data Access Layer (MongoDB)                            │
│  ├── User Management                                        │
│  ├── Financial Data Storage                                 │
│  ├── Conversation History                                   │
│  └── Agent Context                                          │
├─────────────────────────────────────────────────────────────┤
│  🤖 Agent System Integration                                │
│  └── Compatible with Original Lab Agents                    │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
backend/
│
├── 🚀 main.py                    # FastAPI application entry point
│
├── 📊 models/                    # Pydantic data models
│   ├── user.py                   # User authentication models
│   ├── jar.py                    # Budget jar models
│   ├── transaction.py            # Transaction models
│   ├── fee.py                    # Recurring fee models
│   ├── plan.py                   # Budget plan models
│   ├── conversation.py           # Chat conversation models
│   ├── user_settings.py          # User financial settings
│   └── token.py                  # JWT token models
│
├── 🌐 api/                       # REST API endpoints
│   ├── deps.py                   # API dependencies (auth, db)
│   └── routers/                  # API route handlers
│       ├── auth.py               # Authentication endpoints
│       ├── chat.py               # AI chat interface
│       ├── jars.py               # Jar management endpoints
│       ├── transactions.py       # Transaction endpoints
│       ├── fees.py               # Fee management endpoints
│       ├── plans.py              # Plan management endpoints
│       └── user_settings.py      # User settings endpoints
│
├── 🛠️ services/                  # Business logic layer
│   ├── adapters.py               # Lab agent compatibility adapters
│   ├── financial_services.py     # Core financial operations
│   ├── orchestrator_service.py   # AI agent orchestration
│   ├── security.py               # Authentication & security
│   └── service_responses.py      # Standardized service responses
│
├── 🗄️ db/                        # Database management
│   └── database.py               # MongoDB connection setup
│
├── ⚙️ core/                      # Configuration and settings
│   └── config.py                 # Application configuration
│
├── 🔧 utils/                     # Database utilities
│   └── db_utils.py               # Database operations (CRUD)
│
└── 🤖 agents/                    # AI Agent system
    ├── base_worker.py            # Base agent interface
    ├── classifier/               # Transaction classifier agent
    ├── fee/                      # Fee management agent
    ├── jar/                      # Jar management agent
    ├── knowledge/                # Knowledge base agent
    ├── orchestrator/             # Main orchestrator agent
    ├── plan/                     # Budget planning agent
    └── transaction_fetcher/       # Transaction fetching agent
```

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8+
- MongoDB (local or Atlas)
- Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd vpbank_financial_coach_backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create your environment configuration file:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
```

**`.env` Configuration:**

```properties
# Database Configuration
MONGO_URL="mongodb://localhost:27017"
DATABASE_NAME="vpbank_dev"

# Authentication
JWT_SECRET_KEY="your_super_strong_randomly_generated_secret_key_here"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services (for chat functionality)
GOOGLE_API_KEY="your_google_gemini_api_key_here"

# Development Settings
DEBUG=true
ENVIRONMENT="development"

# CORS Settings (for frontend integration)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
```

**Environment Variable Descriptions:**

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `MONGO_URL` | MongoDB connection string | Yes | `mongodb://localhost:27017` |
| `DATABASE_NAME` | MongoDB database name | Yes | `vpbank_dev` |
| `JWT_SECRET_KEY` | Secret key for JWT token signing | Yes | Generate with `openssl rand -hex 32` |
| `JWT_ALGORITHM` | Algorithm for JWT tokens | No | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | No | `30` (default) |
| `GOOGLE_API_KEY` | Google Gemini API key for AI chat | Yes* | Get from Google AI Studio |
| `DEBUG` | Enable debug mode | No | `true` |
| `ENVIRONMENT` | Environment name | No | `development` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | No | Frontend URLs |

*Required for AI chat functionality

### 3. Database Setup

#### Option A: Local MongoDB

```bash
# Install MongoDB locally
# Windows: Download from https://www.mongodb.com/try/download/community
# macOS: brew install mongodb-community
# Ubuntu: sudo apt install mongodb

# Start MongoDB service
# Windows: net start MongoDB
# macOS: brew services start mongodb-community
# Ubuntu: sudo systemctl start mongod

# Verify MongoDB is running
mongosh
# Should connect successfully
```

#### Option B: MongoDB Atlas (Cloud)

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Get your connection string
4. Update `MONGO_URL` in `.env`:
   ```
   MONGO_URL="mongodb+srv://username:password@cluster.mongodb.net"
   ```

### 4. Generate JWT Secret Key

```bash
# Generate a secure JWT secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Or using OpenSSL
openssl rand -hex 32

# Copy the generated key to JWT_SECRET_KEY in .env
```

### 5. Get Google API Key (for AI Features)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to `GOOGLE_API_KEY` in `.env`

### 6. Run the Application

```bash
# Start the FastAPI development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Run with Python
python -m backend.main

# For production (using Gunicorn)
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 7. Verify Installation

Open your browser and navigate to:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

You should see the FastAPI interactive documentation.

## 📖 API Documentation

### Available Endpoints

The API provides comprehensive endpoints for financial management:

#### 🔐 Authentication (`/api/auth/`)
- `POST /register` - Create new user account
- `POST /token` - Login and get JWT access token
- `GET /me` - Get current user profile

#### 👤 User Settings (`/api/user/`)
- `GET /settings` - Get user financial settings
- `PUT /settings` - Update total income and preferences

#### 🏺 Jar Management (`/api/jars/`)
- `GET /` - List all user budget jars
- `POST /` - Create new budget jar

#### 💸 Transaction Management (`/api/transactions/`)
- `GET /` - Query transactions with filters
- `POST /` - Create new transaction (auto-updates jar balances)

#### 💳 Recurring Fees (`/api/fees/`)
- `GET /` - List recurring fees
- `POST /` - Create new recurring fee
- `DELETE /{fee_name}` - Delete recurring fee

#### 📋 Budget Plans (`/api/plans/`)
- `GET /` - List budget plans
- `POST /` - Create new budget plan
- `PUT /{plan_name}` - Update existing plan
- `DELETE /{plan_name}` - Delete plan

#### 💬 AI Chat (`/api/chat/`)
- `POST /` - Chat with AI financial coach

### Authentication

All endpoints (except `/auth/register` and `/auth/token`) require JWT authentication:

```bash
# Get access token
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Use token in subsequent requests
curl -H "Authorization: Bearer <your_token>" \
  http://localhost:8000/api/jars/
```

For complete API documentation, see:
- **Interactive Docs**: http://localhost:8000/docs
- **Detailed Guide**: `API_DOCUMENTATION.md`
- **Quick Reference**: `API_QUICK_REFERENCE.md`

## 🧪 Testing the API

### Manual Testing Examples

#### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

#### 2. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

#### 3. Create a Budget Jar

```bash
# Save your token from step 2
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8000/api/jars/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Necessities",
    "description": "Essential expenses like rent and groceries",
    "percent": 0.55
  }'
```

#### 4. Add a Transaction

```bash
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.00,
    "jar_name": "necessities",
    "description": "Grocery shopping",
    "date": "2025-07-15",
    "time": "14:30",
    "source": "manual_input"
  }'
```

#### 5. Chat with AI Assistant

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How much have I spent this month?",
    "context": {}
  }'
```

### Using Postman or Insomnia

1. Import the API from: http://localhost:8000/openapi.json
2. Set up environment variables for base URL and token
3. Use the collection to test all endpoints

## 🔧 Development

### Project Configuration

The application uses environment-based configuration managed in `backend/core/config.py`:

```python
# Access configuration in your code
from backend.core.config import settings

# Database URL
db_url = settings.mongodb_url

# JWT settings
secret_key = settings.jwt_secret_key
```

### Database Operations

All database operations are centralized in `backend/utils/db_utils.py`:

```python
# Example: Get user jars
from backend.utils.db_utils import get_all_jars_for_user

jars = await get_all_jars_for_user(db, user_id)
```

### Adding New Endpoints

1. **Create Model** (in `models/`):
   ```python
   # models/new_model.py
   from pydantic import BaseModel
   
   class NewResourceCreate(BaseModel):
       name: str
       description: str
   ```

2. **Add Database Functions** (in `utils/db_utils.py`):
   ```python
   async def create_new_resource(db, user_id, resource_data):
       # Implementation
       pass
   ```

3. **Create Service** (in `services/`):
   ```python
   # services/new_service.py
   class NewResourceService:
       @staticmethod
       async def create_resource(db, user_id, data):
           return await db_utils.create_new_resource(db, user_id, data)
   ```

4. **Add Router** (in `api/routers/`):
   ```python
   # api/routers/new_resource.py
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.post("/")
   async def create_resource(resource: NewResourceCreate):
       # Implementation
       pass
   ```

5. **Register Router** (in `main.py`):
   ```python
   from .api.routers import new_resource
   
   app.include_router(new_resource.router, prefix="/api/new-resource", tags=["New Resource"])
   ```

### Running in Development Mode

```bash
# Run with auto-reload (development)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run with debug logging
DEBUG=true uvicorn backend.main:app --reload

# Run on different port
uvicorn backend.main:app --reload --port 8080
```

## 🚀 Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install production dependencies
pip install gunicorn

# Run with multiple workers
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With environment file
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --env-file .env
```

### Environment Variables for Production

```properties
# Production .env
MONGO_URL="mongodb+srv://user:pass@cluster.mongodb.net/vpbank_prod"
DATABASE_NAME="vpbank_production"
JWT_SECRET_KEY="super_secure_production_key"
DEBUG=false
ENVIRONMENT="production"
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

### Using Docker (Future)

```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ ./backend/
CMD ["gunicorn", "backend.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check MongoDB status
mongosh

# Test connection string
python -c "
from pymongo import MongoClient
client = MongoClient('your_mongo_url')
print(client.server_info())
"
```

#### Import Errors
```bash
# Ensure you're in the right directory
cd vpbank_financial_coach_backend

# Check Python path
python -c "import sys; print(sys.path)"

# Run from project root
python -m backend.main
```

#### JWT Token Issues
```bash
# Verify your JWT secret is set
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('JWT_SECRET_KEY:', os.getenv('JWT_SECRET_KEY'))
"
```

#### AI Chat Not Working
```bash
# Check Google API key
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('GOOGLE_API_KEY:', os.getenv('GOOGLE_API_KEY')[:10] + '...' if os.getenv('GOOGLE_API_KEY') else 'Not set')
"
```

### Debug Mode

Enable debug mode in `.env`:
```properties
DEBUG=true
```

This provides:
- Detailed error messages
- Request/response logging
- Enhanced stack traces

### Logs

```bash
# View application logs (if configured)
tail -f logs/app.log

# Check uvicorn logs
uvicorn backend.main:app --log-level debug
```

## 📚 Key Features

### ✅ Multi-Agent AI System
- **Orchestrator Service**: Routes user requests to appropriate specialized agents
- **Transaction Classifier**: Automatically categorizes expenses into budget jars
- **Knowledge Base**: Provides financial education and app guidance
- **Budget Advisor**: Creates personalized financial plans and recommendations
- **Fee Manager**: Handles recurring payments and subscriptions

### 🔒 Production-Ready Security
- **JWT Authentication**: Secure token-based authentication with configurable expiration
- **User Isolation**: Complete data separation between users
- **Input Validation**: Comprehensive Pydantic model validation
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Environment-based Config**: Secure configuration management

### 🗄️ Robust Data Management
- **MongoDB Integration**: Scalable NoSQL database with async operations
- **Data Consistency**: ACID transactions where needed
- **Automatic Calculations**: Real-time jar balance updates
- **Historical Tracking**: Complete transaction and conversation history

### 🎯 Advanced Financial Features
- **Smart Jar System**: Flexible budget allocation with percentage or fixed amounts
- **Automatic Categorization**: AI-powered transaction classification
- **Recurring Fee Management**: Automated tracking of subscriptions and bills
- **Budget Planning**: Comprehensive financial planning with goal tracking
- **Transaction Analytics**: Advanced querying and filtering capabilities

## 🔗 Integration Points

### Frontend Integration
- **REST API**: Standard HTTP endpoints with JSON payloads
- **JWT Authentication**: Token-based auth compatible with modern frontend frameworks
- **CORS Support**: Configured for React, Vue, Angular, and other SPA frameworks
- **OpenAPI Documentation**: Auto-generated API documentation for frontend teams

### Agent System Integration
- **Lab Compatibility**: 100% compatible with original agent testing lab
- **Adapter Pattern**: Service adapters maintain sync interfaces for agents
- **Conversation Management**: Persistent chat history and context
- **Agent Communication**: Inter-agent communication and data sharing

## 📈 Performance Considerations

### Database Optimization
- **Connection Pooling**: Async MongoDB connection management
- **Indexed Queries**: Optimized database queries with proper indexing
- **Pagination Support**: Built-in pagination for large datasets

### API Performance
- **Async Operations**: Non-blocking request handling
- **Response Caching**: Configurable caching for frequently accessed data
- **Request Validation**: Early validation to prevent unnecessary processing

## 🤝 Contributing

### Development Setup
1. Fork and clone the repository
2. Follow the setup instructions above
3. Create a feature branch
4. Make your changes
5. Test thoroughly
6. Submit a pull request

### Code Standards
- Follow PEP 8 Python style guide
- Use type hints for all function parameters and return values
- Write comprehensive docstrings
- Add tests for new functionality
- Maintain backward compatibility with the agent system

---

## 📞 Support

For questions, issues, or contributions:

1. **Documentation**: Check `API_DOCUMENTATION.md` for complete API reference
2. **Quick Reference**: See `API_QUICK_REFERENCE.md` for frontend integration
3. **Issues**: Create GitHub issues for bugs or feature requests
4. **Development**: Follow the contributing guidelines above

---

**Built with ❤️ for VPBank Hackathon 2025**

*This backend provides a production-ready foundation for the VPBank Financial Coach application while maintaining complete compatibility with the original multi-agent system.*
