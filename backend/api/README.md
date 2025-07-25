# VPBank Financial Coach API Documentation

## Overview

This directory contains the FastAPI backend implementation for the VPBank AI Financial Coach. The API provides comprehensive financial management capabilities including user authentication, jar management, transaction tracking, recurring fees, budget planning, and AI-powered chat functionality.

## Architecture

### Core Components

1. **main.py** - FastAPI application entry point with middleware and routing setup
2. **deps.py** - Dependency injection for database and authentication
3. **routers/** - Individual API route handlers organized by functionality

## API Structure

### Authentication & Security
- **JWT Token-based Authentication**: All protected endpoints require valid JWT tokens
- **User Registration & Login**: Standard OAuth2 password flow implementation
- **Role-based Access**: User-specific data isolation

### Database Integration
- **MongoDB Integration**: Async MongoDB operations using Motor driver
- **Connection Management**: Robust database connection lifecycle with health checks
- **User Data Isolation**: All operations are user-scoped for security

## API Endpoints

### 1. Authentication Routes (`/api/auth`)

#### POST `/api/auth/register`
- **Purpose**: Create new user account
- **Request**: `UserCreate` model (username, email, password)
- **Response**: `UserPublic` model (excludes sensitive data)
- **Validation**: Checks for existing username/email conflicts

#### POST `/api/auth/token`
- **Purpose**: User login and JWT token generation
- **Request**: OAuth2 form data (username, password)
- **Response**: JWT access token with bearer type
- **Security**: Password verification with hashed storage

#### GET `/api/auth/me`
- **Purpose**: Get current user profile
- **Authentication**: Required (JWT token)
- **Response**: Current user's public profile data

### 2. Chat Interface (`/api/chat`)

#### POST `/api/chat/`
- **Purpose**: Process user messages through AI orchestrator
- **Request**: `ChatRequest` with message and optional context
- **Response**: AI-generated response with success status
- **Integration**: Routes to appropriate financial agents based on intent

### 3. Jar Management (`/api/jars`)

#### GET `/api/jars/`
- **Purpose**: List all user's financial jars
- **Response**: Array of `JarInDB` models
- **Features**: User-specific jar retrieval

#### POST `/api/jars/`
- **Purpose**: Create new financial jar
- **Request**: `JarCreate` model (name, description, percentage/amount)
- **Validation**: Checks for duplicate jar names
- **Integration**: Uses `JarManagementService` for business logic

### 4. Transaction Management (`/api/transactions`)

#### POST `/api/transactions/`
- **Purpose**: Create new transaction and update jar balance
- **Request**: `TransactionCreate` model
- **Logic**: 
  - Validates target jar exists
  - Creates transaction record
  - Updates jar's current balance and percentage
- **Features**: Automatic jar balance calculation

#### GET `/api/transactions/`
- **Purpose**: Query transactions with filtering
- **Filters**:
  - `jar_name`: Filter by specific jar
  - `start_date/end_date`: Date range filtering
  - `min_amount/max_amount`: Amount range filtering
  - `limit`: Result count limit (max 1000)
- **Response**: Sorted list of transactions (newest first)

### 5. Recurring Fees (`/api/fees`)

#### POST `/api/fees/`
- **Purpose**: Create recurring fee schedule
- **Request**: `RecurringFeeCreate` model
- **Logic**: 
  - Validates target jar exists
  - Calculates next occurrence date
  - Creates fee schedule
- **Features**: Pattern-based recurrence calculation

#### GET `/api/fees/`
- **Purpose**: List recurring fees with filtering
- **Filters**:
  - `active_only`: Show only active fees
  - `target_jar`: Filter by target jar
- **Response**: Sorted by next occurrence date

#### DELETE `/api/fees/{fee_name}`
- **Purpose**: Delete recurring fee by name
- **Response**: 204 No Content on success

### 6. Budget Planning (`/api/plans`)

#### POST `/api/plans/`
- **Purpose**: Create new budget plan
- **Request**: `BudgetPlanCreate` model
- **Validation**: Checks for duplicate plan names

#### GET `/api/plans/`
- **Purpose**: List budget plans with status filtering
- **Filters**: `status` - Filter by plan status (active, completed, etc.)
- **Response**: Sorted by creation date (newest first)

#### PUT `/api/plans/{plan_name}`
- **Purpose**: Update existing budget plan
- **Request**: `BudgetPlanUpdate` model (partial updates supported)
- **Features**: Only updates provided fields

#### DELETE `/api/plans/{plan_name}`
- **Purpose**: Delete budget plan by name
- **Response**: 204 No Content on success

### 7. User Settings (`/api/user`)

#### GET `/api/user/settings`
- **Purpose**: Retrieve user's financial settings
- **Features**: Creates default settings if none exist
- **Response**: `UserSettingsInDB` model

#### PUT `/api/user/settings`
- **Purpose**: Update user's financial settings (e.g., total income)
- **Request**: `UserSettingsUpdate` model
- **Impact**: Affects jar amount calculations

## Technical Implementation

### Database Operations
- **Async/Await Pattern**: All database operations are asynchronous
- **Error Handling**: Comprehensive HTTP exception handling
- **Data Validation**: Pydantic model validation for all inputs
- **MongoDB Integration**: Direct MongoDB operations for complex queries

### Security Features
- **JWT Authentication**: Stateless token-based authentication
- **Password Hashing**: Secure password storage with hashing
- **User Isolation**: All data operations are user-scoped
- **CORS Configuration**: Proper cross-origin resource sharing setup

### Service Integration
- **Financial Services**: Integration with jar, transaction, and fee services
- **Orchestrator Service**: AI-powered chat routing and processing
- **Calculation Services**: Business logic for financial calculations

### Data Models
- **Pydantic Models**: Type-safe request/response models
- **Database Models**: MongoDB document models with proper field mapping
- **Validation Rules**: Input validation and business rule enforcement

## Error Handling

### Standardized Error Responses

All API endpoints now use standardized error handling through the service layer:

#### Service Response Model
- **ServiceResult**: Base response model with status, message, data, and errors
- **Specialized Results**: `JarOperationResult`, `TransactionOperationResult`, etc.
- **Error Codes**: Consistent error codes mapped to appropriate HTTP status codes

#### HTTP Status Code Mapping
- **200**: Successful operations
- **201**: Resource creation
- **204**: Successful deletion
- **400**: Bad request (validation errors, invalid data)
- **401**: Unauthorized (authentication required)
- **404**: Resource not found
- **409**: Conflict (duplicate resources)
- **500**: Internal server error

#### Error Response Format
```json
{
  "detail": "Primary error message",
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Detailed error description",
      "field": "field_name"
    }
  ]
}
```

### Common Error Scenarios
- **Duplicate Resource Names**: Returns 409 Conflict with descriptive message
- **Missing Resources**: Returns 404 when referenced entities don't exist
- **Authentication Failures**: Returns 401 with proper error details
- **Validation Errors**: Returns 400 with field-specific error messages
- **Business Rule Violations**: Returns 400 with specific error codes

## Performance Considerations

### Database Optimization
- **Indexing**: MongoDB indexes on frequently queried fields
- **Query Limits**: Reasonable limits on result sets to prevent performance issues
- **Connection Pooling**: Efficient database connection management

### Response Optimization
- **Pagination**: Query limits for large result sets
- **Field Selection**: Efficient data retrieval with proper field mapping
- **Caching**: Database connection reuse and lifecycle management

## Development Guidelines

### Adding New Endpoints
1. Create route handler in appropriate router file
2. Define Pydantic models for request/response
3. Implement database operations in `db_utils.py`
4. Add proper error handling and validation
5. Update documentation

### Testing Recommendations
- Unit tests for individual route handlers
- Integration tests for database operations
- Authentication testing for protected endpoints
- Error scenario testing for edge cases

### Security Best Practices
- Always validate user ownership of resources
- Use proper HTTP status codes
- Implement rate limiting for production
- Sanitize user inputs
- Log security-relevant events

## Configuration

### Environment Variables
- `MONGO_URL`: MongoDB connection string
- `DATABASE_NAME`: Database name
- `JWT_SECRET_KEY`: JWT signing secret
- `GOOGLE_API_KEY`: API key for AI services

### CORS Configuration
- Currently configured for development (allows all origins)
- Should be restricted for production deployment

## Future Enhancements

### Planned Features
- Rate limiting implementation
- Enhanced user profile management
- Advanced financial analytics
- Real-time notifications for recurring fees
- Batch operations for bulk data management

### Performance Improvements
- Query optimization with proper indexing
- Response caching for frequently accessed data
- Database query performance monitoring
- API response time optimization

## Maintenance Notes

### Regular Tasks
- Monitor database performance and optimize queries
- Review and update security configurations
- Update dependency versions for security patches
- Review and optimize API response times

### Troubleshooting
- Check database connectivity for connection errors
- Verify JWT token configuration for authentication issues
- Review input validation for malformed request errors
- Check service integration for orchestrator communication issues
