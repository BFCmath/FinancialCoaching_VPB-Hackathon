# VPBank AI Financial Coach API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Base Information](#base-information)
3. [Authentication](#authentication)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication-endpoints)
   - [Chat Agent](#chat-agent-endpoints)
   - [User Settings](#user-settings-endpoints)
   - [Jar Management](#jar-management-endpoints)
   - [Transaction Management](#transaction-management-endpoints)
   - [Fee Management](#fee-management-endpoints)
   - [Plan Management](#plan-management-endpoints)
7. [Request Response Examples](#request-response-examples)
8. [Rate Limiting & Best Practices](#rate-limiting--best-practices)

## Overview

The VPBank AI Financial Coach API is a RESTful backend service that powers a multi-agent financial assistant. It provides comprehensive financial management features including budget jar management, transaction tracking, recurring fee management, and AI-powered financial coaching through chat interactions.

### Key Features
- **Multi-agent AI System**: Orchestrated intelligent agents for different financial tasks
- **Budget Jar System**: Virtual budget jars for expense categorization
- **Transaction Management**: Comprehensive transaction tracking and analysis
- **Recurring Fee Management**: Automated recurring payment tracking
- **Financial Planning**: Budget plan creation and management
- **Real-time Chat**: AI-powered financial coaching and assistance
- **User Authentication**: Secure JWT-based authentication system

## Base Information

### Base URL

```text
https://your-api-domain.com/api
```

### API Version

```text
v1.0.0
```

### Content-Type
All requests and responses use `application/json` content type.

### CORS
The API supports CORS for web frontend integration.

## Authentication

The API uses JWT (JSON Web Token) based authentication. All protected endpoints require a valid JWT token in the Authorization header.

### Authentication Flow
1. Register a new account or login with existing credentials
2. Receive a JWT access token
3. Include the token in the Authorization header for all subsequent requests

### Authorization Header Format

```text
Authorization: Bearer <your-jwt-token>
```

### Token Expiration
JWT tokens have a configurable expiration time. When a token expires, you'll receive a 401 Unauthorized response and need to obtain a new token.

## Data Models

### User Models

#### UserPublic

```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "email": "user@example.com",
  "username": "john_doe"
}
```

#### UserCreate

```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "a_strong_password"
}
```

#### Token

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Jar Models

#### JarInDB (Response Model)
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a3",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "name": "Necessities",
  "description": "For essential living costs like rent and groceries.",
  "percent": 0.55,
  "amount": 2750.00,
  "current_percent": 0.33,
  "current_amount": 1650.00
}
```

#### JarCreate (Request Model)
```json
{
  "name": "Necessities",
  "description": "For essential living costs like rent and groceries.",
  "percent": 0.55,  // Optional: percentage allocation (0.0-1.0)
  "amount": 2750.00  // Optional: fixed amount allocation
}
```

#### JarUpdate (Request Model)
```json
{
  "name": "Essentials",  // Optional
  "description": "Updated description for essential costs.",  // Optional
  "percent": 0.60,  // Optional
  "amount": 3000.00  // Optional
}
```

### Transaction Models

#### TransactionInDB (Response Model)
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a4",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "amount": 75.50,
  "jar": "necessities",
  "description": "Grocery shopping at supermarket",
  "date": "2025-07-14",
  "time": "14:30",
  "source": "manual_input",
  "transaction_datetime": "2025-07-14T14:30:00Z"
}
```

#### TransactionCreate (Request Model)
```json
{
  "amount": 75.50,
  "jar_name": "necessities",
  "description": "Grocery shopping at supermarket",
  "date": "2025-07-14",
  "time": "14:30",
  "source": "manual_input"
}
```

### Fee Models

#### RecurringFeeInDB (Response Model)
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a5",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "name": "Netflix Subscription",
  "amount": 15.99,
  "description": "Monthly Netflix streaming subscription.",
  "target_jar": "play",
  "pattern_type": "monthly",
  "pattern_details": [5],
  "created_date": "2025-07-14T10:00:00Z",
  "next_occurrence": "2025-08-05T10:00:00Z",
  "is_active": true
}
```

#### RecurringFeeCreate (Request Model)
```json
{
  "name": "Netflix Subscription",
  "amount": 15.99,
  "description": "Monthly Netflix streaming subscription.",
  "target_jar": "play",
  "pattern_type": "monthly",
  "pattern_details": [5]
}
```

#### RecurringFeeUpdate (Request Model)
```json
{
  "amount": 16.99,  // Optional
  "description": "Updated Netflix subscription.",  // Optional
  "target_jar": "entertainment",  // Optional
  "pattern_type": "monthly",  // Optional
  "pattern_details": [10],  // Optional
  "is_active": false  // Optional
}
```

### Plan Models

#### BudgetPlanInDB (Response Model)
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a6",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "name": "Save for Vacation",
  "detail_description": "A plan to save $2000 for a trip to Japan next year.",
  "day_created": "2025-07-14",
  "status": "active",
  "jar_recommendations": "Suggest increasing 'long_term_savings' jar by 5%"
}
```

#### BudgetPlanCreate (Request Model)
```json
{
  "name": "Save for Vacation",
  "detail_description": "A plan to save $2000 for a trip to Japan next year.",
  "day_created": "2025-07-14",
  "status": "active",
  "jar_recommendations": "Suggest increasing 'long_term_savings' jar by 5%"
}
```

#### BudgetPlanUpdate (Request Model)
```json
{
  "name": "Save for Japan Trip",  // Optional
  "detail_description": "Updated plan description.",  // Optional
  "status": "completed",  // Optional
  "jar_recommendations": "Updated recommendations."  // Optional
}
```

### User Settings Models

#### UserSettingsInDB (Response Model)
```json
{
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "total_income": 5000.0
}
```

#### UserSettingsUpdate (Request Model)
```json
{
  "total_income": 5500.0
}
```

### Chat Models

#### ChatRequest (Request Model)
```json
{
  "message": "How much did I spend on play last month?",
  "context": {  // Optional
    "additional_info": "any relevant context"
  }
}
```

#### ChatResponse (Response Model)
```json
{
  "response": "Based on your transaction history, you spent $350 on play activities last month.",
  "success": true,
  "context": {  // Optional
    "analyzed_transactions": 15,
    "time_period": "July 2025"
  }
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400
}
```

### Common HTTP Status Codes

| Status Code | Description | Common Scenarios |
|-------------|-------------|------------------|
| 200 | OK | Successful GET requests |
| 201 | Created | Successful POST requests that create resources |
| 204 | No Content | Successful DELETE requests |
| 400 | Bad Request | Validation errors, missing required fields |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Request validation failed |
| 500 | Internal Server Error | Server-side errors |

### Error Code Mapping

The API uses standardized error codes that map to appropriate HTTP status codes:

| Service Error Code | HTTP Status | Description |
|-------------------|-------------|-------------|
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource already exists |
| VALIDATION_ERROR | 400 | Input validation failed |
| INVALID_PERCENTAGE | 400 | Percentage value out of range |
| INVALID_NAME | 400 | Invalid name format |
| ALLOCATION_EXCEEDED | 400 | Budget allocation exceeds 100% |
| MISSING_REQUIRED_FIELDS | 400 | Required fields missing |
| PARAMETER_MISMATCH | 400 | Parameter combination invalid |

### Validation Error Response Example
```json
{
  "detail": "A jar with the name 'Necessities' already exists.",
  "status_code": 400
}
```

### Multiple Validation Errors Example
```json
{
  "detail": "Validation failed for jar creation. Details: Invalid percentage value; Name already exists",
  "status_code": 400
}
```

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "a_strong_password"
}
```

**Response (201 Created):**
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "email": "user@example.com",
  "username": "john_doe"
}
```

**Possible Errors:**
- `400 Bad Request`: Username or email already exists
- `422 Unprocessable Entity`: Validation errors

---

#### POST /api/auth/token
Authenticate a user and return a JWT access token.

**Request Body (form-data):**
```
username: john_doe
password: a_strong_password
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Possible Errors:**
- `401 Unauthorized`: Incorrect username or password

---

#### GET /api/auth/me
Get the profile of the currently authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "email": "user@example.com",
  "username": "john_doe"
}
```

**Possible Errors:**
- `401 Unauthorized`: Invalid or expired token

### Chat Agent Endpoints

#### POST /api/chat/
Handle a user's chat message through the AI orchestrator service.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "message": "How much did I spend on play last month?",
  "context": {
    "additional_info": "any relevant context"
  }
}
```

**Response (200 OK):**
```json
{
  "response": "Based on your transaction history, you spent $350 on play activities last month. This represents 7% of your total monthly budget. Your play jar currently has $150 remaining for this month.",
  "success": true,
  "context": {
    "analyzed_transactions": 15,
    "time_period": "July 2025",
    "agent_used": "transaction_fetcher"
  }
}
```

**Features:**
- Multi-agent AI system routing requests to appropriate specialized agents
- Natural language understanding in English and Vietnamese
- Context-aware conversations
- Financial analysis and recommendations
- Integration with all financial data (jars, transactions, fees, plans)

**Possible Errors:**
- `401 Unauthorized`: Invalid or expired token
- `500 Internal Server Error`: AI service unavailable

### User Settings Endpoints

#### GET /api/user/settings
Retrieve the financial settings for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "total_income": 5000.0
}
```

**Note:** If no settings exist, default values are created automatically.

---

#### PUT /api/user/settings
Update the financial settings for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "total_income": 5500.0
}
```

**Response (200 OK):**
```json
{
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "total_income": 5500.0
}
```

**Possible Errors:**
- `400 Bad Request`: No settings provided to update
- `401 Unauthorized`: Invalid or expired token

### Jar Management Endpoints

#### GET /api/jars/
Get all jars for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "id": "60d5ecf3e7b3c2a4c8f3b3a3",
    "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
    "name": "Necessities",
    "description": "For essential living costs like rent and groceries.",
    "percent": 0.55,
    "amount": 2750.00,
    "current_percent": 0.33,
    "current_amount": 1650.00
  },
  {
    "id": "60d5ecf3e7b3c2a4c8f3b3a4",
    "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
    "name": "Play",
    "description": "For entertainment and leisure activities.",
    "percent": 0.10,
    "amount": 500.00,
    "current_percent": 0.07,
    "current_amount": 350.00
  }
]
```

---

#### POST /api/jars/
Create a new jar for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Emergency Fund",
  "description": "For unexpected expenses and emergencies.",
  "percent": 0.20
}
```

**Alternative Request (with fixed amount):**
```json
{
  "name": "Emergency Fund",
  "description": "For unexpected expenses and emergencies.",
  "amount": 1000.00
}
```

**Response (201 Created):**
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a5",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "name": "Emergency Fund",
  "description": "For unexpected expenses and emergencies.",
  "percent": 0.20,
  "amount": 1000.00,
  "current_percent": 0.0,
  "current_amount": 0.0
}
```

**Jar Creation Rules:**
- Must provide either `percent` OR `amount`, not both
- `percent` must be between 0.0 and 1.0 (0% to 100%)
- `amount` must be positive
- Jar names must be unique per user
- Total allocation across all jars cannot exceed 100%

**Possible Errors:**
- `400 Bad Request`: Jar with same name already exists
- `400 Bad Request`: Invalid allocation parameters
- `409 Conflict`: Resource conflict

### Transaction Management Endpoints

#### GET /api/transactions/
Query transactions for the current user with optional filters.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `jar_name` (optional): Filter by jar name
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `min_amount` (optional): Filter by minimum transaction amount
- `max_amount` (optional): Filter by maximum transaction amount
- `limit` (optional): Number of transactions to return (1-1000, default: 50)

**Example Request:**
```
GET /api/transactions/?jar_name=necessities&start_date=2025-07-01&end_date=2025-07-31&min_amount=10&limit=20
```

**Response (200 OK):**
```json
[
  {
    "id": "60d5ecf3e7b3c2a4c8f3b3a4",
    "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
    "amount": 75.50,
    "jar": "necessities",
    "description": "Grocery shopping at supermarket",
    "date": "2025-07-14",
    "time": "14:30",
    "source": "manual_input",
    "transaction_datetime": "2025-07-14T14:30:00Z"
  }
]
```

---

#### POST /api/transactions/
Create a new transaction and update the corresponding jar's balance.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "amount": 75.50,
  "jar_name": "necessities",
  "description": "Grocery shopping at supermarket",
  "date": "2025-07-14",
  "time": "14:30",
  "source": "manual_input"
}
```

**Transaction Source Options:**
- `vpbank_api`: From VPBank API integration
- `manual_input`: Manually entered by user
- `text_input`: Extracted from text input
- `image_input`: Extracted from image/receipt

**Response (201 Created):**
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a4",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "amount": 75.50,
  "jar": "necessities",
  "description": "Grocery shopping at supermarket",
  "date": "2025-07-14",
  "time": "14:30",
  "source": "manual_input",
  "transaction_datetime": "2025-07-14T14:30:00Z"
}
```

**Automatic Updates:**
- The target jar's current balance is automatically updated
- Current percentage is recalculated based on total income

**Possible Errors:**
- `404 Not Found`: Target jar not found
- `400 Bad Request`: Invalid transaction data
- `401 Unauthorized`: Invalid token

### Fee Management Endpoints

#### GET /api/fees/
List recurring fees for the current user with optional filters.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `active_only` (optional): Filter for only active fees (default: true)
- `target_jar` (optional): Filter fees by target jar name

**Example Request:**
```
GET /api/fees/?active_only=true&target_jar=play
```

**Response (200 OK):**
```json
[
  {
    "id": "60d5ecf3e7b3c2a4c8f3b3a5",
    "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
    "name": "Netflix Subscription",
    "amount": 15.99,
    "description": "Monthly Netflix streaming subscription.",
    "target_jar": "play",
    "pattern_type": "monthly",
    "pattern_details": [5],
    "created_date": "2025-07-14T10:00:00Z",
    "next_occurrence": "2025-08-05T10:00:00Z",
    "is_active": true
  }
]
```

---

#### POST /api/fees/
Create a new recurring fee for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Netflix Subscription",
  "amount": 15.99,
  "description": "Monthly Netflix streaming subscription.",
  "target_jar": "play",
  "pattern_type": "monthly",
  "pattern_details": [5]
}
```

**Pattern Types and Details:**
- `daily`: pattern_details not used
- `weekly`: pattern_details contains days of week (0=Monday, 6=Sunday)
- `monthly`: pattern_details contains days of month (1-31)

**Response (201 Created):**
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a5",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "name": "Netflix Subscription",
  "amount": 15.99,
  "description": "Monthly Netflix streaming subscription.",
  "target_jar": "play",
  "pattern_type": "monthly",
  "pattern_details": [5],
  "created_date": "2025-07-14T10:00:00Z",
  "next_occurrence": "2025-08-05T10:00:00Z",
  "is_active": true
}
```

**Automatic Calculations:**
- `next_occurrence` is automatically calculated based on pattern
- `created_date` is set to current timestamp

**Possible Errors:**
- `400 Bad Request`: Fee with same name already exists
- `404 Not Found`: Target jar not found
- `422 Unprocessable Entity`: Invalid pattern configuration

---

#### DELETE /api/fees/{fee_name}
Delete a recurring fee by its name.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `fee_name`: The name of the fee to delete

**Response (204 No Content):**
No response body.

**Possible Errors:**
- `404 Not Found`: Fee not found
- `401 Unauthorized`: Invalid token

### Plan Management Endpoints

#### GET /api/plans/
List budget plans for the current user with optional status filter.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (optional): Filter plans by status (`active`, `completed`, `paused`)

**Example Request:**
```
GET /api/plans/?status=active
```

**Response (200 OK):**
```json
[
  {
    "id": "60d5ecf3e7b3c2a4c8f3b3a6",
    "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
    "name": "Save for Vacation",
    "detail_description": "A plan to save $2000 for a trip to Japan next year.",
    "day_created": "2025-07-14",
    "status": "active",
    "jar_recommendations": "Suggest increasing 'long_term_savings' jar by 5%"
  }
]
```

---

#### POST /api/plans/
Create a new budget plan for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Save for Vacation",
  "detail_description": "A plan to save $2000 for a trip to Japan next year.",
  "day_created": "2025-07-14",
  "status": "active",
  "jar_recommendations": "Suggest increasing 'long_term_savings' jar by 5%"
}
```

**Response (201 Created):**
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a6",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "name": "Save for Vacation",
  "detail_description": "A plan to save $2000 for a trip to Japan next year.",
  "day_created": "2025-07-14",
  "status": "active",
  "jar_recommendations": "Suggest increasing 'long_term_savings' jar by 5%"
}
```

**Possible Errors:**
- `400 Bad Request`: Plan with same name already exists
- `422 Unprocessable Entity`: Validation errors

---

#### PUT /api/plans/{plan_name}
Update an existing budget plan by its name.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `plan_name`: The name of the plan to update

**Request Body:**
```json
{
  "name": "Save for Japan Trip",
  "detail_description": "Updated plan to save $2500 for a trip to Japan next year.",
  "status": "active",
  "jar_recommendations": "Increase 'long_term_savings' jar to 25% of income"
}
```

**Response (200 OK):**
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a6",
  "user_id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "name": "Save for Japan Trip",
  "detail_description": "Updated plan to save $2500 for a trip to Japan next year.",
  "day_created": "2025-07-14",
  "status": "active",
  "jar_recommendations": "Increase 'long_term_savings' jar to 25% of income"
}
```

**Possible Errors:**
- `400 Bad Request`: No update data provided
- `404 Not Found`: Plan not found

---

#### DELETE /api/plans/{plan_name}
Delete a budget plan by its name.

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameters:**
- `plan_name`: The name of the plan to delete

**Response (204 No Content):**
No response body.

**Possible Errors:**
- `404 Not Found`: Plan not found
- `401 Unauthorized`: Invalid token

## Request Response Examples

### Complete User Workflow Example

#### 1. User Registration
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "alice@example.com",
  "username": "alice_smith",
  "password": "SecurePass123!"
}
```

Response:
```json
{
  "id": "60d5ecf3e7b3c2a4c8f3b3a2",
  "email": "alice@example.com",
  "username": "alice_smith"
}
```

#### 2. User Login
```http
POST /api/auth/token
Content-Type: application/x-www-form-urlencoded

username=alice_smith&password=SecurePass123!
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZV9zbWl0aCIsImV4cCI6MTY5MDQ3MjQwMH0.example_signature",
  "token_type": "bearer"
}
```

#### 3. Set Up User Income
```http
PUT /api/user/settings
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "total_income": 6000.0
}
```

#### 4. Create Budget Jars
```http
POST /api/jars/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Necessities",
  "description": "Essential expenses like rent, groceries, utilities",
  "percent": 0.55
}
```

```http
POST /api/jars/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Play",
  "description": "Entertainment and leisure activities",
  "percent": 0.10
}
```

#### 5. Add Transactions
```http
POST /api/transactions/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "amount": 85.30,
  "jar_name": "necessities",
  "description": "Weekly grocery shopping at Whole Foods",
  "date": "2025-07-14",
  "time": "09:15",
  "source": "manual_input"
}
```

#### 6. Set Up Recurring Fees
```http
POST /api/fees/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Spotify Premium",
  "amount": 10.99,
  "description": "Monthly music streaming subscription",
  "target_jar": "play",
  "pattern_type": "monthly",
  "pattern_details": [1]
}
```

#### 7. Chat with AI Assistant
```http
POST /api/chat/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "message": "How am I doing with my budget this month? Do I have room to increase my entertainment spending?",
  "context": {
    "request_type": "budget_analysis"
  }
}
```

Response:
```json
{
  "response": "Great question! Based on your July spending patterns, you're doing well with your budget. Here's your current status:\n\n• Necessities: $1,245 spent of $3,300 allocated (38% used)\n• Play: $78 spent of $600 allocated (13% used)\n\nYou definitely have room to increase entertainment spending! You have $522 remaining in your Play jar this month. Consider that you also have recurring fees like Spotify ($10.99) coming up.\n\nWould you like me to suggest some specific entertainment activities within your remaining budget?",
  "success": true,
  "context": {
    "agent_used": "budget_advisor",
    "analysis_period": "July 2025",
    "jars_analyzed": ["necessities", "play"],
    "suggestions_available": true
  }
}
```

### Error Handling Examples

#### Validation Error Example
```http
POST /api/jars/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Emergency",
  "description": "Emergency fund",
  "percent": 1.5
}
```

Response (400 Bad Request):
```json
{
  "detail": "Validation failed for percent: Percentage value must be between 0.0 and 1.0 (0% to 100%)",
  "status_code": 400
}
```

#### Resource Not Found Example
```http
POST /api/transactions/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "amount": 50.0,
  "jar_name": "nonexistent_jar",
  "description": "Test transaction",
  "date": "2025-07-14",
  "time": "10:00",
  "source": "manual_input"
}
```

Response (404 Not Found):
```json
{
  "detail": "Jar 'nonexistent_jar' not found for this user.",
  "status_code": 404
}
```

#### Conflict Error Example
```http
POST /api/jars/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Necessities",
  "description": "Duplicate jar name",
  "percent": 0.20
}
```

Response (400 Bad Request):
```json
{
  "detail": "A jar with the name 'Necessities' already exists.",
  "status_code": 400
}
```

## Rate Limiting & Best Practices

### Rate Limiting
Currently, the API does not implement rate limiting, but it's recommended to:
- Limit chat requests to 60 per minute per user
- Limit other API calls to 1000 per hour per user
- Implement exponential backoff for failed requests

### Best Practices

#### Authentication
- Store JWT tokens securely (not in localStorage for web apps)
- Implement token refresh logic before expiration
- Clear tokens on logout

#### API Usage
- Use appropriate HTTP methods (GET for reading, POST for creating, PUT for updating, DELETE for removing)
- Include proper error handling for all possible HTTP status codes
- Implement retry logic with exponential backoff for 5xx errors
- Use query parameters for filtering and pagination

#### Data Management
- Always validate user input before sending to API
- Handle decimal numbers properly for financial calculations
- Use ISO date formats for date fields
- Normalize jar names (lowercase, underscore-separated) for consistency

#### Performance
- Cache user settings and jar information locally
- Batch transaction creation when possible
- Use query parameters to limit response sizes
- Implement pagination for large datasets

#### Security
- Never log or store passwords
- Validate all input data
- Use HTTPS in production
- Implement proper CORS policies

### Frontend Integration Guidelines

#### React/Vue.js Example Hook
```javascript
// Example useAPI hook for frontend integration
const useAPI = () => {
  const [token, setToken] = useState(localStorage.getItem('auth_token'));
  
  const apiCall = async (endpoint, method = 'GET', data = null) => {
    const config = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      ...(data && { body: JSON.stringify(data) })
    };
    
    const response = await fetch(`/api${endpoint}`, config);
    
    if (response.status === 401) {
      // Handle token expiration
      setToken(null);
      localStorage.removeItem('auth_token');
      // Redirect to login
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }
    
    return response.json();
  };
  
  return { apiCall, token, setToken };
};
```

#### Error Handling Component
```javascript
const APIErrorHandler = ({ error, retry }) => {
  const getErrorMessage = (error) => {
    if (error.status === 401) return "Please log in again";
    if (error.status === 403) return "Permission denied";
    if (error.status === 404) return "Resource not found";
    if (error.status >= 500) return "Server error. Please try again later.";
    return error.detail || "An error occurred";
  };
  
  return (
    <div className="error-container">
      <p>{getErrorMessage(error)}</p>
      {error.status >= 500 && (
        <button onClick={retry}>Retry</button>
      )}
    </div>
  );
};
```

### Testing Recommendations

#### Unit Testing
- Test API integration functions
- Mock API responses for consistent testing
- Test error handling scenarios
- Validate request payload formatting

#### Integration Testing
- Test complete user workflows
- Verify authentication flows
- Test edge cases and error conditions
- Validate data persistence

#### Example Test Cases
```javascript
describe('Jar Management API', () => {
  test('should create jar successfully', async () => {
    const jarData = {
      name: 'Test Jar',
      description: 'Test description',
      percent: 0.20
    };
    
    const response = await apiCall('/jars/', 'POST', jarData);
    expect(response.name).toBe('Test Jar');
    expect(response.percent).toBe(0.20);
  });
  
  test('should handle duplicate jar name error', async () => {
    const jarData = {
      name: 'Existing Jar',
      description: 'Test description',
      percent: 0.20
    };
    
    await expect(apiCall('/jars/', 'POST', jarData))
      .rejects.toThrow('A jar with the name \'Existing Jar\' already exists');
  });
});
```

---

## Conclusion

This API provides comprehensive financial management capabilities through a modern, RESTful interface. The multi-agent AI system enables sophisticated financial coaching while maintaining simple, intuitive endpoints for basic CRUD operations.

For additional support or questions about the API, please refer to the source code documentation or contact the development team.

**API Version:** 1.0.0  
**Last Updated:** July 14, 2025  
**Documentation Status:** Complete and Exhaustive
