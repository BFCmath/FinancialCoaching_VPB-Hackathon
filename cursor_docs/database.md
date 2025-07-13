# VPBank AI Financial Coach - Database Design Specifications

## 📊 Data Structures & Production Database Recommendations

### 1. JARS - Budget Categories
```python
{
  "name": str,                # Jar identifier (PRIMARY KEY)
  "description": str,         # Human description  
  "percent": float,          # Budget allocation (0.0-1.0)
  "current_percent": float   # Current balance (0.0-1.0)
  "current_amount": float,   # Current amount in dollars
  "amount": float            # Budget amount in dollars
}
```

**Production Database: PostgreSQL (SQL)**
- **Why SQL**: Fixed schema, ACID compliance for financial calculations, percentage constraints
- **Rationale**: Budget jars have strict relationships with transactions/fees, require precise decimal calculations
- **Constraints**: CHECK constraints for percent validation (0.0-1.0), UNIQUE on name
- **Indexes**: Primary key on name, index on percent for budget queries

### 2. TRANSACTIONS - Financial Records
```python
{
  "amount": float,           # Transaction amount (DECIMAL precision required)
  "jar": str,               # Reference to jar name (FOREIGN KEY)
  "description": str,       # Transaction description
  "date": str,             # Date (YYYY-MM-DD) - Use DATE type
  "time": str,             # Time (HH:MM) - Use TIME type  
  "source": str            # vpbank_api, manual_input, text_input, image_input
}
```

**Production Database: PostgreSQL (SQL) + TimescaleDB Extension**
- **Why SQL + Time-Series**: High-volume financial data with time-based queries, ACID compliance critical
- **Rationale**: Financial transactions require strict consistency, complex date/amount range queries
- **Benefits**: TimescaleDB optimizes time-series queries, automatic partitioning by date
- **Constraints**: FOREIGN KEY to jars(name), CHECK amount > 0, source ENUM
- **Indexes**: Composite indexes on (date, jar), (amount, date), (source, date)

### 3. FEES - Recurring Payment Schedules  
```python
class RecurringFee:
  name: str                      # Fee identifier (PRIMARY KEY)
  amount: float                  # Fee amount (DECIMAL)
  description: str               # Fee description
  target_jar: str                # Reference to jar (FOREIGN KEY)
  pattern_type: str              # "daily", "weekly", "monthly" (ENUM)
  pattern_details: List[int]     # [1,3,5] for Mon/Wed/Fri (JSON/ARRAY)
  created_date: datetime         # Creation timestamp
  next_occurrence: datetime      # Next payment date (INDEXED)
  is_active: bool               # Active status
```

**Production Database: PostgreSQL (SQL)**
- **Why SQL**: Complex scheduling logic needs ACID compliance, date arithmetic, JSON support for pattern_details
- **Rationale**: Payment schedules require precise date calculations and strong consistency
- **PostgreSQL Features**: Native JSON support for pattern_details, advanced date functions
- **Constraints**: FOREIGN KEY to jars(name), CHECK pattern_type IN enum values
- **Indexes**: Index on next_occurrence for schedule processing, composite on (is_active, next_occurrence)

### 4. BUDGET PLANS - Financial Planning Documents
```python
class BudgetPlan:
  name: str                      # Plan identifier (PRIMARY KEY)
  detail_description: str        # Plan description (TEXT)
  day_created: str              # Creation date
  status: str                   # "active", "completed", "paused" (ENUM)
  jar_recommendations: str      # Jar adjustment proposals (TEXT/JSON)
```

**Production Database: PostgreSQL (SQL) + MongoDB (Hybrid)**
- **Primary: PostgreSQL** for structured data (name, status, dates)
- **Secondary: MongoDB** for jar_recommendations (complex, evolving text/JSON)
- **Why Hybrid**: Core planning data needs ACID compliance, but recommendations are document-like
- **Rationale**: Plans have structured metadata but flexible recommendation content
- **Alternative**: Pure PostgreSQL with JSONB for jar_recommendations

### 5. KNOWLEDGE BASE - App Documentation
```python
APP_INFO: str  # JSON string containing app documentation
```

**Production Database: Elasticsearch + Redis Cache**
- **Why Search Engine**: Documentation needs full-text search, semantic search capabilities
- **Rationale**: Knowledge base is read-heavy with complex search requirements
- **Architecture**: Elasticsearch for search, Redis for frequently accessed content
- **Benefits**: Natural language queries, relevance scoring, fast retrieval
- **Alternative**: MongoDB with text indexes for simpler setup

### 6. CONVERSATION HISTORY - Chat Logs with Context
```python
{
  "user_input": str,            # User's input (TEXT)
  "agent_output": str,          # Agent's response (TEXT)  
  "agent_list": List[str],      # Agents involved (JSON ARRAY)
  "tool_call_list": List[str],  # Tools called (JSON ARRAY)
  "timestamp": datetime,        # Conversation timestamp
  "session_id": str            # Session identifier (for grouping)
}
```

**Production Database: MongoDB (NoSQL)**
- **Why NoSQL**: Semi-structured data, flexible schema for tool calls, high write volume
- **Rationale**: Conversation logs have varying structure, need fast writes, eventual consistency OK
- **Benefits**: Natural JSON storage, flexible schema evolution, horizontal scaling
- **Indexes**: Compound index on (session_id, timestamp), text index on user_input/agent_output

## 🏗️ Recommended Production Architecture

### Primary Database Stack
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │    MongoDB      │    │  Elasticsearch │
│                 │    │                 │    │                 │
│ • Jars          │    │ • Conversation  │    │ • Knowledge     │
│ • Transactions  │    │   History       │    │   Base          │
│ • Fees          │    │ • Plan Docs     │    │ • Search Index  │
│ • Plans (meta)  │    │   (optional)    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Caching Layer
```
┌─────────────────┐
│     Redis       │
│                 │
│ • Active Agent  │
│   Context       │
│ • Frequent      │
│   Queries       │
│ • Session Data  │
└─────────────────┘
```

### Justification by Data Characteristics

| Data Type | Volume | Consistency | Schema | Queries | Database Choice |
|-----------|--------|-------------|--------|---------|-----------------|
| Jars | Low | **High** | Fixed | Simple | **PostgreSQL** |
| Transactions | **High** | **High** | Fixed | Complex Time-series | **PostgreSQL + TimescaleDB** |
| Fees | Medium | **High** | Semi-fixed | Date calculations | **PostgreSQL** |
| Plans | Medium | Medium | **Flexible** | Mixed | **PostgreSQL + MongoDB** |
| Knowledge | Low | Low | **Flexible** | **Full-text search** | **Elasticsearch** |
| Conversations | **High** | Low | **Flexible** | Sequential/Text | **MongoDB** |

## 🔧 Implementation Strategy

### Phase 1: Core Financial Data (PostgreSQL)
- Implement jars, transactions, fees in PostgreSQL
- Set up proper constraints and indexes
- Implement ACID-compliant financial calculations

### Phase 2: Conversation System (MongoDB)
- Implement conversation history in MongoDB
- Set up session management and context tracking
- Implement conversation lock pattern storage

### Phase 3: Knowledge & Search (Elasticsearch)
- Index app documentation in Elasticsearch  
- Implement semantic search capabilities
- Set up Redis caching for frequent queries

### Phase 4: Optimization
- Add TimescaleDB for transaction time-series optimization
- Implement proper sharding and replication
- Set up monitoring and backup strategies

## 🚨 Critical Design Decisions

### Financial Data Integrity
- **ACID Compliance**: All financial operations (jars, transactions, fees) require strict consistency
- **Decimal Precision**: Use DECIMAL types for all monetary values, never FLOAT
- **Audit Trail**: All financial changes must be logged with timestamps and user context

### Conversation Lock Storage
```sql
-- Active agent context table
CREATE TABLE active_agent_contexts (
    session_id VARCHAR(255) PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);
```

### Cross-Database Consistency
- **Financial References**: Maintain referential integrity between jars and transactions
- **Conversation References**: Store agent/tool names as strings with validation
- **Backup Strategy**: Synchronized backups across all databases for consistency

This hybrid approach balances the strict consistency needs of financial data with the flexibility requirements of conversation logs and knowledge management.