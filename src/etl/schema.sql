PRAGMA foreign_keys = ON;

-- 1. Companies
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL
);

-- 2. Profit and Loss
CREATE TABLE IF NOT EXISTS profitandloss (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    sales REAL,
    operating_profit REAL,
    net_profit REAL,
    eps REAL,
    opm_percentage REAL,
    dividend_payout_ratio_pct REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 3. Balance Sheet
CREATE TABLE IF NOT EXISTS balancesheet (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    borrowings REAL,
    total_assets REAL,
    equity REAL,
    reserves REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 4. Cash Flow
CREATE TABLE IF NOT EXISTS cashflow (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 5. Analysis
CREATE TABLE IF NOT EXISTS analysis (
    company_id TEXT PRIMARY KEY,
    analysis_text TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 6. Documents
CREATE TABLE IF NOT EXISTS documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER,
    document_url TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 7. Pros and Cons
CREATE TABLE IF NOT EXISTS prosandcons (
    company_id TEXT PRIMARY KEY,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 8. Sectors
CREATE TABLE IF NOT EXISTS sectors (
    company_id TEXT PRIMARY KEY,
    broad_sector TEXT,
    sub_sector TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 9. Stock Prices
CREATE TABLE IF NOT EXISTS stock_prices (
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 10. Financial Ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    net_profit_margin REAL,
    operating_profit_margin REAL,
    return_on_equity REAL,
    return_on_capital REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    free_cash_flow REAL,
    revenue_cagr REAL,
    pat_cagr REAL,
    eps_cagr REAL,
    asset_turnover REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
-- 11. Market Cap

CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 12. Peer Groups

CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

