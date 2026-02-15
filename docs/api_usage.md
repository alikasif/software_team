# API Usage Guide

## Base URLs
- Health endpoint: `GET /health`
- API v1 base path: `/api/v1`

Local default server URL:
- `http://localhost:8000`

## Current API Surface (Scaffold)
Routers are mounted under:
- `/api/v1/auth`
- `/api/v1/users`
- `/api/v1/groups`
- `/api/v1/expenses`
- `/api/v1/balances`
- `/api/v1/settlements`
- `/api/v1/history`

At the moment, modules provide route namespaces and tags. Endpoint-level handlers are expected to be added by implementation tasks.

## Expected MVP Usage Flows

### 1) User/Auth Flow
1. Register/login via auth endpoints.
2. Receive access/refresh token pair.
3. Call protected endpoints with bearer access token.

### 2) Group Flow
1. Create group.
2. Add members.
3. Create expenses in that group.

### 3) Expense + Split Flow
1. Submit expense payload (group, payer, amount, participants).
2. Provide split method (`equal`, `percentage`, or `exact`) and method-specific participant fields.
3. Backend validates split payload and persists immutable ledger entries in one transaction.

### 4) Balance + Settle-Up Flow
1. Query balances for user/group views.
2. Submit settle-up request between payer and payee.
3. Backend records settlement as ledger-affecting entry and updates derived balance state.

## Split Rules (Contract Expectations)

### Equal
- Participants share the total evenly.
- Rounding reconciliation must be deterministic so totals match exactly.

### Percentage
- Each participant has a percentage allocation.
- Percentages must sum to exactly `100` before persistence.
- Computed participant amounts must sum to expense total after deterministic reconciliation.

### Exact
- Each participant supplies an explicit amount.
- Exact amounts must sum to the expense total before persistence.

### Validation Invariants
- Participant set must be valid for target group membership.
- Amount fields are positive and currency-safe.
- Invalid split payloads fail before any DB write.

## Settle-Up Behavior (Contract Expectations)
- Settle-up records a payment from one user to another for a specific amount.
- A successful settlement reduces outstanding net obligation between those parties.
- Settlement operations are atomic and ledger-backed.
- Over-settling and invalid counterparties must be rejected by validation rules.

## Idempotency Expectations
- Financial POST operations should require `Idempotency-Key` support:
  - Expense creation
  - Settlement creation
- Reusing the same key with the same payload should return the original successful result without duplicate writes.
- Reusing the same key with a mismatched payload should be rejected.
- Idempotency records should be persisted and scoped so duplicate submissions are safe across retries.

## Concurrency & Consistency Notes
- Expense and settlement writes must execute inside DB transactions.
- Critical financial mutations should use targeted row locking (for example `FOR UPDATE`) where needed.
- Ledger should be immutable; balances are derived.
- Serialization/lock conflict retries may be required for high-contention paths.
- Concurrency tests should assert no double-write, no lost update, and deterministic post-state.

## OpenAPI Contract
- Source of contract truth: `shared/api/openapi.yaml`
- Current file is a scaffold and should be expanded as endpoint handlers are implemented.