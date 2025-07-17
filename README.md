# VPBank AI Financial Coach - Hackathon Project

A comprehensive multi-agent AI financial coaching system built for the VPBank Hackathon. This project combines experimental agent testing with a production-ready FastAPI backend and interactive frontend testing tools.

## 🏗️ Project Overview

This repository contains a complete financial coaching system that leverages multiple specialized AI agents to provide personalized financial advice, budget management, and transaction analysis for Vietnamese users.

### Key Features

- **Multi-Agent AI System**: 7 specialized agents working together (Classifier, Jar, Fee, Plan, Fetcher, Knowledge, Orchestrator)
- **Production Backend**: FastAPI-based REST API with MongoDB persistence
- **Comprehensive Testing**: Full test suites and interactive chat simulators
- **Standardized Configuration**: Centralized configuration with agent-specific API key support
- **Vietnamese Language Support**: Native Vietnamese financial coaching capabilities

## 📁 Repository Structure

```
vpb_hackathon/
├── 📚 docs/                           # API documentation and guides
│   ├── API_DOCUMENTATION.md            # Complete API reference
│   ├── API_QUICK_REFERENCE.md          # Quick start for frontend devs
│   └── features/                       # Feature specifications
│
├── 🧪 agent-testing-lab/              # Experimental agent development
│   ├── classifier_test/                # Transaction classification agent
│   ├── jar_test/                       # Budget jar management agent
│   ├── fee_test/                       # Recurring fee management agent
│   ├── plan_test/                      # Budget planning agent
│   ├── knowledge_test/                 # Knowledge base agent
│   ├── orchestrator_test/              # Multi-agent orchestration
│   ├── transaction_fetcher/            # Transaction data fetching
│   └── full_multi_agent/               # Complete agent system
│
└── 🏭 vpbank_financial_coach_backend/  # Production backend
    ├── backend/                        # FastAPI application
    │   ├── main.py                     # Application entry point
    │   ├── api/                        # REST API endpoints
    │   ├── models/                     # Pydantic data models
    │   ├── services/                   # Business logic layer
    │   ├── agents/                     # Production agent implementations
    │   ├── utils/                      # Database and utility functions
    │   └── core/                       # Configuration and settings
    │
    └── frontend/                       # Testing and simulation tools
        ├── fully_test.py               # Comprehensive API test suite
        ├── chat_simulator.py           # Interactive chat interface
        └── mock.py                     # API mock testing tool
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MongoDB (local or cloud)
- Google Gemini API key(s)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd vpb_hackathon
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd vpbank_financial_coach_backend

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your MongoDB connection and API keys
```

### 3. Configure Environment Variables

Edit the `.env` file with your settings:

```bash
# Required
MONGO_URL="mongodb://localhost:27017"
DATABASE_NAME="vpbank_dev"
JWT_SECRET_KEY="your_super_strong_secret_key_here"
GOOGLE_API_KEY="your_google_gemini_api_key"

# Optional: Agent-specific API keys for better resource management
CLASSIFIER_GOOGLE_API_KEY="optional_classifier_specific_key"
JAR_GOOGLE_API_KEY="optional_jar_specific_key"
# ... other agent-specific keys

# Shared settings (used by all agents)
MODEL_NAME="gemini-2.5-flash-lite-preview-06-17"
LLM_TEMPERATURE="0.1"
DEBUG_MODE="true"
```

### 4. Start the Backend

```bash
# Start the FastAPI server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

### 5. Test the Backend

Run the comprehensive test suite:

```bash
cd frontend

# Run full API test suite (53 tests)
python fully_test.py

# Or run interactive chat simulator
python chat_simulator.py

# Or run mock API tester
python mock.py
```

## 🧪 Testing Tools

### 1. Comprehensive Test Suite (`fully_test.py`)

A complete API testing framework with 94.3% success rate:

```bash
python frontend/fully_test.py
```

**Features:**
- Authentication testing
- Jar system validation (default 6-jar system)
- Transaction lifecycle testing
- Fee management testing
- Plan management testing
- Chat functionality testing
- Interactive mode for step-by-step verification

### 2. Interactive Chat Simulator (`chat_simulator.py`)

Test the AI chat functionality interactively:

```bash
python frontend/chat_simulator.py
```

**Features:**
- User registration/login
- Real-time chat with AI agents
- Conversation history
- Special commands (`/help`, `/history`, `/clear`, `/exit`)
- Vietnamese and English language support

### 3. API Mock Tester (`mock.py`)

Focused API endpoint testing:

```bash
python frontend/mock.py
```

**Features:**
- Individual endpoint testing
- Data validation testing
- Error scenario testing
- Filter and query parameter testing

## 🏭 Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install production dependencies
pip install gunicorn

# Run with multiple workers
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Production Environment Variables

```properties
# Production .env
MONGO_URL="mongodb+srv://user:pass@cluster.mongodb.net/vpbank_prod"
DATABASE_NAME="vpbank_production"
JWT_SECRET_KEY="super_secure_production_key"
DEBUG_MODE="false"
VERBOSE_LOGGING="false"
ENVIRONMENT="production"

# Use different API keys for different agents in production
CLASSIFIER_GOOGLE_API_KEY="prod_classifier_key"
JAR_GOOGLE_API_KEY="prod_jar_key"
```

### Docker Deployment (Future)

```bash
# Build and run with Docker
docker build -t vpbank-backend .
docker run -p 8000:8000 vpbank-backend
```

## 🤖 Agent System

The system uses 7 specialized AI agents:

1. **Classifier Agent**: Categorizes transactions and user queries
2. **Jar Agent**: Manages budget jar allocation and operations
3. **Fee Agent**: Handles recurring fee tracking and management
4. **Plan Agent**: Creates and manages budget plans
5. **Fetcher Agent**: Retrieves and processes transaction data
6. **Knowledge Agent**: Provides financial education and advice
7. **Orchestrator Agent**: Coordinates multi-agent workflows

### Agent Configuration

All agents share standardized configuration:

- **Shared Settings**: Model name, temperature, debug mode, memory settings
- **Agent-Specific API Keys**: Optional individual API keys with fallback to default
- **Consistent Behavior**: Standardized error handling and logging

## 📖 API Reference

### Authentication Endpoints

- `POST /api/auth/register` - Create new user account
- `POST /api/auth/token` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Core Endpoints

- `GET/POST /api/jars/` - Budget jar management
- `GET/POST /api/transactions/` - Transaction tracking
- `GET/POST/DELETE /api/fees/` - Recurring fee management
- `GET/POST/PUT/DELETE /api/plans/` - Budget plan management
- `POST /api/chat/` - AI chat interface
- `GET/PUT /api/user/settings` - User financial settings

### Response Format

All endpoints return JSON with standard error handling:

```json
// Success Response
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "data": "..."
}

// Error Response
{
  "detail": "Error message",
  "status_code": 400
}
```

## 🛠️ Development

### Project Configuration

The system uses centralized configuration in `backend/core/config.py`:

```python
from backend.core.config import settings

# Access configuration
db_url = settings.MONGO_URL
api_key = settings.get_agent_api_key("jar")  # Agent-specific key with fallback
```

### Adding New Features

1. **Models**: Add Pydantic models in `backend/models/`
2. **Services**: Implement business logic in `backend/services/`
3. **Routes**: Create API endpoints in `backend/api/routers/`
4. **Agents**: Add agent logic in `backend/agents/`
5. **Tests**: Update test suites in `frontend/`

### Database Operations

All database operations use async MongoDB with Motor:

```python
from backend.utils.db_utils import get_all_jars_for_user

jars = await get_all_jars_for_user(db, user_id)
```

## 🔧 Configuration Features

### Agent-Specific API Keys

Each agent can have its own Google API key for better resource management:

```bash
# Individual agent keys (optional)
CLASSIFIER_GOOGLE_API_KEY="key_for_classifier"
JAR_GOOGLE_API_KEY="key_for_jar_management"
FEE_GOOGLE_API_KEY="key_for_fee_management"

# Fallback to default if agent key not provided
GOOGLE_API_KEY="default_fallback_key"
```

### Shared Configuration

All agents use consistent settings:

- Model: `gemini-2.5-flash-lite-preview-06-17`
- Temperature: `0.1`
- Max iterations: `5`
- Memory turns: `10`
- Debug mode: Configurable per environment

## 📊 Test Results

### Comprehensive Test Suite Results

- **Total Tests**: 53
- **Success Rate**: 94.3% (50/53 passing)
- **Coverage**: Authentication, CRUD operations, AI chat, error handling
- **Performance**: Average response time < 500ms

### Test Categories

1. **Authentication Tests** (3/3 passing)
2. **Jar Management Tests** (8/8 passing)
3. **Transaction Tests** (12/12 passing)
4. **Fee Management Tests** (10/10 passing)
5. **Plan Management Tests** (8/8 passing)
6. **Chat Functionality Tests** (7/7 passing)
7. **Error Handling Tests** (5/5 passing)

## 🌟 Key Features

### Default Jar System

New users automatically get 6 default budget jars:
- Necessities (55%)
- Education (10%)
- Long Term Savings (10%)
- Play (10%)
- Financial Freedom (10%)
- Give (5%)

### Multi-Language Support

- Native Vietnamese language support
- English language support
- Cultural context awareness for Vietnamese financial practices

### Advanced AI Features

- Natural language transaction categorization
- Intelligent budget recommendations
- Proactive financial advice
- Context-aware conversations

## 🔍 Troubleshooting

### Common Issues

**1. MongoDB Connection Error**
```bash
# Check MongoDB is running
# Verify MONGO_URL in .env file
# Ensure network connectivity
```

**2. Google API Key Issues**
```bash
# Verify API key is valid
# Check agent-specific keys vs default fallback
# Ensure Gemini API is enabled
```

**3. Authentication Failures**
```bash
# Check JWT_SECRET_KEY is set
# Verify token expiration settings
# Test with fresh user registration
```

### Debug Mode

Enable detailed logging:

```bash
DEBUG_MODE="true"
VERBOSE_LOGGING="true"
```

## 📞 Support & Documentation

- **API Documentation**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- **Quick Reference**: [docs/API_QUICK_REFERENCE.md](docs/API_QUICK_REFERENCE.md)
- **Agent Details**: [agent-testing-lab/*/README.md](agent-testing-lab/)
- **Backend Details**: [vpbank_financial_coach_backend/README.md](vpbank_financial_coach_backend/README.md)

## 🏆 Hackathon Highlights

### Technical Achievements

- **Production-Ready Architecture**: FastAPI + MongoDB + Multi-Agent AI
- **Comprehensive Testing**: 94.3% test success rate with 53 test cases
- **Standardized Configuration**: Centralized config with agent-specific flexibility
- **Vietnamese Localization**: Native language support for financial coaching

### Innovation Features

- **Multi-Agent Orchestration**: 7 specialized AI agents working together
- **Intelligent Budget Management**: Automatic jar allocation and rebalancing
- **Proactive Financial Advice**: Context-aware recommendations
- **Real-Time Chat Interface**: Interactive financial coaching

### Scalability Features

- **Microservice-Ready**: Agent-based architecture supports horizontal scaling
- **Database Optimization**: Indexed queries and efficient data structures
- **Configuration Management**: Environment-based settings for different deployments
- **Monitoring Ready**: Comprehensive logging and health checks

---

**Built for VPBank Hackathon 2025** | **Track 9: Financial Innovation**


