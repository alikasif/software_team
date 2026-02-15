-- Seeder 001: Initial currencies and rates

INSERT INTO currencies (code, name) VALUES
  ('USD', 'US Dollar'),
  ('EUR', 'Euro'),
  ('GBP', 'British Pound'),
  ('JPY', 'Japanese Yen'),
  ('BTC', 'Bitcoin');

-- Example rates (not real-time)
INSERT INTO currency_rates (from_currency, to_currency, rate) VALUES
  ('USD', 'EUR', 0.92),
  ('EUR', 'USD', 1.09),
  ('USD', 'GBP', 0.78),
  ('GBP', 'USD', 1.28),
  ('USD', 'JPY', 150.0),
  ('JPY', 'USD', 0.0067),
  ('USD', 'BTC', 0.000025),
  ('BTC', 'USD', 40000.0);
