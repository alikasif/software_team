
-- Users table
CREATE TABLE users (
	id SERIAL PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	email VARCHAR(255) UNIQUE NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Currencies table
CREATE TABLE currencies (
	code CHAR(3) PRIMARY KEY, -- e.g. USD, EUR
	name VARCHAR(50) NOT NULL
);

-- Currency rates table
CREATE TABLE currency_rates (
	id SERIAL PRIMARY KEY,
	from_currency CHAR(3) NOT NULL REFERENCES currencies(code),
	to_currency CHAR(3) NOT NULL REFERENCES currencies(code),
	rate DECIMAL(18,8) NOT NULL,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Wallets table
CREATE TABLE wallets (
	id SERIAL PRIMARY KEY,
	user_id INTEGER NOT NULL REFERENCES users(id),
	currency CHAR(3) NOT NULL REFERENCES currencies(code),
	balance DECIMAL(18,2) NOT NULL DEFAULT 0,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	UNIQUE(user_id, currency)
);

-- Payment methods table
CREATE TABLE payment_methods (
	id SERIAL PRIMARY KEY,
	user_id INTEGER NOT NULL REFERENCES users(id),
	type VARCHAR(20) NOT NULL, -- 'card' or 'bank'
	details JSONB NOT NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE transactions (
	id SERIAL PRIMARY KEY,
	from_wallet_id INTEGER REFERENCES wallets(id),
	to_wallet_id INTEGER REFERENCES wallets(id),
	payment_method_id INTEGER REFERENCES payment_methods(id),
	amount DECIMAL(18,2) NOT NULL,
	currency CHAR(3) NOT NULL REFERENCES currencies(code),
	status VARCHAR(20) NOT NULL,
	type VARCHAR(20) NOT NULL, -- 'internal', 'external', etc.
	description TEXT,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
