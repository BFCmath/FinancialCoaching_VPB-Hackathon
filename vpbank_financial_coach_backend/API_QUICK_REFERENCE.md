# API Quick Reference for Frontend Team

## Authentication Required
All endpoints except `/auth/register` and `/auth/token` require:
```
Authorization: Bearer <jwt-token>
```

## Base URL: `/api`

## Quick Endpoint Reference

### Authentication
- `POST /auth/register` - Create account
- `POST /auth/token` - Login (form-data: username, password)
- `GET /auth/me` - Get current user info

### User Settings
- `GET /user/settings` - Get user financial settings
- `PUT /user/settings` - Update total income

### Jars (Budget Categories)
- `GET /jars/` - List all user jars
- `POST /jars/` - Create new jar (requires name, description, percent OR amount)

### Transactions
- `GET /transactions/` - List transactions (supports filtering)
- `POST /transactions/` - Create transaction (updates jar balance automatically)

### Recurring Fees
- `GET /fees/` - List recurring fees
- `POST /fees/` - Create recurring fee
- `DELETE /fees/{fee_name}` - Delete fee

### AI Chat
- `POST /chat/` - Chat with AI assistant

## Common Response Patterns

### Success (200/201)
```json
{
  // Resource data
}
```

### Error (4xx/5xx)
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Key Frontend Considerations

1. **JWT Token Management**: Store securely, handle 401 responses
2. **Jar Creation**: Must provide either `percent` (0.0-1.0) OR `amount`, not both
3. **Transaction Creation**: Automatically updates jar balances
4. **Date Formats**: Use "YYYY-MM-DD" for dates, "HH:MM" for times
5. **Error Handling**: Check for 400/404/409/500 status codes

See `API_DOCUMENTATION.md` for complete details, examples, and data models.
