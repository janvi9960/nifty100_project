-- 1. Total number of companies
SELECT COUNT(*) AS total_companies
FROM companies;


-- 2. Companies with their sectors
SELECT c.id, c.company_name, s.broad_sector, s.sub_sector
FROM companies c
LEFT JOIN sectors s ON c.id = s.company_id
ORDER BY c.id;


-- 3. Companies with the highest sales
SELECT company_id, year, sales
FROM profitandloss
WHERE sales IS NOT NULL
ORDER BY sales DESC
LIMIT 10;


-- 4. Companies with the highest net profit
SELECT company_id, year, net_profit
FROM profitandloss
WHERE net_profit IS NOT NULL
ORDER BY net_profit DESC
LIMIT 10;


-- 5. Companies with the highest operating profit margin
SELECT company_id, year, opm_percentage
FROM profitandloss
WHERE opm_percentage IS NOT NULL
ORDER BY opm_percentage DESC
LIMIT 10;


-- 6. Companies with the highest market capitalization
SELECT company_id, year, market_cap_crore
FROM market_cap
ORDER BY market_cap_crore DESC
LIMIT 10;


-- 7. Average net profit by year
SELECT year, ROUND(AVG(net_profit), 2) AS avg_net_profit
FROM profitandloss
WHERE net_profit IS NOT NULL
GROUP BY year
ORDER BY year;


-- 8. Companies with the highest borrowings
SELECT company_id, year, borrowings
FROM balancesheet
WHERE borrowings IS NOT NULL
ORDER BY borrowings DESC
LIMIT 10;


-- 9. Companies with positive free cash flow
SELECT company_id, year, free_cash_flow
FROM financial_ratios
WHERE free_cash_flow > 0
ORDER BY free_cash_flow DESC
LIMIT 10;


-- 10. Stock price records by company
SELECT company_id, COUNT(*) AS price_records
FROM stock_prices
GROUP BY company_id
ORDER BY price_records DESC;