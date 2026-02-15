# Runbook

## 1. Environment Setup
1. Install Python 3.11+ and PostgreSQL.
2. Create virtual environment.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Create local env file:
   - copy `.env.example` to `.env`
5. Verify `DATABASE_URL` points to a reachable database.

## 2. Start the Service
- Run API server:
  - `uvicorn app.main:app --reload`
- Verify service health:
  - `GET http://localhost:8000/health`

## 3. Migration Operations
- Create migration:
  - `alembic revision -m "<message>"`
- Apply migrations:
  - `alembic upgrade head`
- Rollback one step:
  - `alembic downgrade -1`

## 4. Test Operations
- Run all tests:
  - `pytest`
- Run only integration tests:
  - `pytest tests/integration`
- Run only concurrency tests:
  - `pytest tests/concurrency`

## 5. Financial Behavior Expectations

### Split Rules
- `equal`: divide evenly with deterministic rounding reconciliation.
- `percentage`: allocations must sum to 100.
- `exact`: participant amounts must sum to the expense total.
- Invalid split payloads fail pre-write.

### Settle-Up Behavior
- Settlement is an atomic financial event between payer and payee.
- Successful writes must be reflected in derived balances.
- Ledger entries remain immutable.

### Idempotency
- Expense/settlement POSTs should be idempotent by `Idempotency-Key`.
- Duplicate key + same payload returns original result.
- Duplicate key + different payload is rejected.

### Concurrency Consistency
- Use transactional boundaries for all financial writes.
- Apply targeted locking for contested balance-affecting rows.
- Use retry strategy for serialization/lock conflicts where needed.
- Validate consistency by concurrency tests (no duplicate write, no lost update).

## 6. Operational Notes
- Current codebase is in scaffold stage for many domain endpoints.
- Treat behavior above as MVP contract expectations until handlers are fully implemented and contract-tested.
- Keep this runbook synchronized with `shared/api/openapi.yaml` and task progress in `shared/task_list.json`.