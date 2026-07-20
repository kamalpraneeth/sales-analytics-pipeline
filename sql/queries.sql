-- =============================================================================
-- Sales Analytics Pipeline — SQL Analysis Queries
-- Database: database/sales.db   Table: sales
-- =============================================================================
-- How to run these queries:
--   Option A (SQLite CLI):
--       sqlite3 database/sales.db
--       .read sql/queries.sql
--   Option B (Python):
--       import sqlite3, pandas as pd
--       conn = sqlite3.connect('database/sales.db')
--       df = pd.read_sql_query("<paste query here>", conn)
--   Option C (DB Browser for SQLite): paste each block into the SQL editor
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- Q1: OVERALL KPI SUMMARY
-- Business question: What are the headline numbers for the entire dataset?
-- Used for: KPI cards in Power BI (Total Revenue, Total Profit, Margin %)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    COUNT(DISTINCT order_id)          AS total_orders,
    COUNT(*)                          AS total_line_items,
    ROUND(SUM(sales), 2)              AS total_revenue,
    ROUND(SUM(profit), 2)             AS total_profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2)  AS overall_profit_margin_pct,
    ROUND(AVG(discount) * 100, 2)    AS avg_discount_pct,
    ROUND(AVG(order_to_ship_days), 1) AS avg_ship_days
FROM sales;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q2: MONTHLY REVENUE TREND
-- Business question: How has revenue grown (or declined) month over month?
-- Used for: Line chart in Power BI — x-axis = order_month_name, y = revenue
-- Note: ORDER BY year+month numerically so "Jan 2021" sorts before "Feb 2021"
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    order_year,
    order_month,
    order_month_name,
    COUNT(DISTINCT order_id)    AS orders,
    ROUND(SUM(sales), 2)        AS monthly_revenue,
    ROUND(SUM(profit), 2)       AS monthly_profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2) AS profit_margin_pct
FROM sales
GROUP BY order_year, order_month, order_month_name
ORDER BY order_year, order_month;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q3: TOP 10 PRODUCTS BY PROFIT
-- Business question: Which specific products drive the most absolute profit?
-- Used for: Horizontal bar chart (Product Name vs Profit)
-- Note: profit_margin shown alongside so you can spot high-revenue/low-margin items
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    product_name,
    sub_category,
    category,
    ROUND(SUM(sales), 2)    AS total_revenue,
    ROUND(SUM(profit), 2)   AS total_profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2) AS profit_margin_pct,
    SUM(quantity)           AS units_sold
FROM sales
GROUP BY product_name, sub_category, category
ORDER BY total_profit DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q4: SALES & PROFIT BY REGION
-- Business question: Which geographic regions are most profitable?
-- Used for: Map visual or bar chart in Power BI
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    region,
    COUNT(DISTINCT order_id)    AS total_orders,
    ROUND(SUM(sales), 2)        AS total_revenue,
    ROUND(SUM(profit), 2)       AS total_profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2) AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct
FROM sales
GROUP BY region
ORDER BY total_profit DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q5: CUSTOMER SEGMENT ANALYSIS
-- Business question: Which customer segments (Consumer / Corporate / Home Office)
--                    generate the most value, and how do their behaviours differ?
-- Used for: Donut/pie chart or grouped bar chart in Power BI
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    segment,
    COUNT(DISTINCT customer_id)  AS unique_customers,
    COUNT(DISTINCT order_id)     AS total_orders,
    ROUND(SUM(sales), 2)         AS total_revenue,
    ROUND(SUM(profit), 2)        AS total_profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2) AS profit_margin_pct,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM sales
GROUP BY segment
ORDER BY total_profit DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q6: SUB-CATEGORY PROFITABILITY RANKING
-- Business question: Within each category, which sub-categories are money-makers
--                    vs money-losers?
-- Used for: Sorted bar chart in Power BI (colour-coded by profit)
-- Key insight: look for sub-categories with high sales but negative profit
--              (signals discount/cost problems)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2)    AS total_revenue,
    ROUND(SUM(profit), 2)   AS total_profit,
    ROUND(SUM(profit) / SUM(sales) * 100, 2) AS profit_margin_pct,
    SUM(quantity)           AS units_sold,
    ROUND(AVG(discount) * 100, 2) AS avg_discount_pct,
    -- Flag as profitable or loss-making for easy filtering in Power BI
    CASE WHEN SUM(profit) > 0 THEN 'Profitable' ELSE 'Loss-Making' END AS profit_status
FROM sales
GROUP BY category, sub_category
ORDER BY total_profit DESC;
