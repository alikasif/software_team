# Digital Wallet Service: Implementation Plan

## Modules/Components
- User Service: Account creation, authentication, personal info management
- Wallet Service: Multi-currency, balance management, currency conversion
- Payment Method Service: Add/remove credit cards, bank accounts
- Transaction Service: Fund transfers (user-to-user, external), transaction history, statements
- API Layer: RESTful endpoints for all services
- Database Layer: Persistent storage for users, wallets, payment methods, transactions, currency rates
- Concurrency/Consistency Layer: Ensure atomicity and consistency for concurrent transactions
- Scalability/Infrastructure: Support for horizontal scaling, load balancing, and monitoring

## Dependencies & Data Flows
- User Service ↔ Database (user info, credentials)
- Wallet Service ↔ User Service (ownership), Database (balances, currencies)
- Payment Method Service ↔ User Service (ownership), Database (payment details)
- Transaction Service ↔ Wallet Service, Payment Method Service, Database (transaction records)
- Currency Conversion ↔ Wallet Service, External API (for rates)
- API Layer ↔ All services (exposes endpoints)
- Concurrency/Consistency ↔ Transaction & Wallet Services

## API Contracts (Key Endpoints)
- User: POST /users, GET /users/{id}, PATCH /users/{id}, POST /auth/login
- Wallet: GET /wallets/{user_id}, POST /wallets/transfer, GET /wallets/{user_id}/transactions, POST /wallets/convert
- Payment Method: POST /users/{id}/payment-methods, DELETE /users/{id}/payment-methods/{pm_id}, GET /users/{id}/payment-methods
- Transaction: GET /transactions/{id}, GET /users/{id}/transactions, POST /transactions/external
- Currency: GET /currencies, GET /currencies/rates

## TypeScript/OpenAPI Types (examples)
- User: { id: string; name: string; email: string; ... }
- Wallet: { id: string; userId: string; balances: { [currency: string]: number } }
- PaymentMethod: { id: string; userId: string; type: 'card'|'bank'; details: object }
- Transaction: { id: string; from: string; to: string; amount: number; currency: string; status: string; timestamp: string }
- CurrencyRate: { from: string; to: string; rate: number }

## Agent Assignments
- Python Backend Agent: API, business logic, concurrency, API contract output to shared/api/
- Database Agent: Schema, migrations, queries
- Frontend Agent: UI/UX, consume API contract from shared/api/
- Docs Agent: API and user documentation
- Test Agent: Automated and concurrency tests
- Reviewer Agents: Code and architecture review (backend, database, frontend)
- GitHub Agent: Periodic pushes and version control

## Key Architectural Decisions
- Modular monolith for initial implementation, scalable to microservices
- RESTful API (OpenAPI spec)
- ACID-compliant database for transactions
- Use of concurrency primitives (locks, transactions) for consistency
- Multi-currency support with real-time conversion rates

---

All agents should coordinate via shared/api/ for API contracts and shared/task_list.json for task tracking. Backend must output OpenAPI/TypeScript contracts for frontend consumption. Database schema must be finalized before backend implementation. Frontend must wait for API contract. All code must be committed via GitHub agent.
