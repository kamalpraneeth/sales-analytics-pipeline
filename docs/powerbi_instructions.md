# Power BI Dashboard Setup Instructions

> These instructions assume you have **Power BI Desktop** installed.  
> Download free from: https://powerbi.microsoft.com/desktop  
> You do not need a Power BI account to build and save locally.

---

## Step 1 — Connect to the Data

You have two options. **Option A (CSV) is simpler; Option B (SQLite) is more portfolio-impressive.**

### Option A — Connect to the Cleaned CSV (Simplest)

1. Open Power BI Desktop
2. Click **Home → Get Data → Text/CSV**
3. Navigate to `data/cleaned/superstore_cleaned.csv` and click **Open**
4. In the preview dialog, click **Load** (the data is already clean — no transforms needed)

### Option B — Connect to SQLite (Recommended for portfolio)

SQLite requires a free ODBC driver because Power BI doesn't have a native SQLite connector.

1. **Install SQLite ODBC Driver** (one-time setup):
   - Download from: http://www.ch-werner.de/sqliteodbc/
   - Run `sqliteodbc.exe` (Windows installer, ~2 MB)

2. **Create an ODBC DSN** (one-time setup):
   - Open **ODBC Data Sources (64-bit)** from Windows search
   - Click **Add** → select **SQLite3 ODBC Driver** → click **Finish**
   - Set Data Source Name: `SuperstoreSales`
   - Set Database Name: browse to `database/sales.db` → click **OK**

3. **Connect in Power BI**:
   - Click **Home → Get Data → More → ODBC**
   - Select DSN: `SuperstoreSales` → click **OK**
   - Expand the table list → check `sales` → click **Load**

---

## Step 2 — Apply a Theme (before building visuals)

1. In Power BI Desktop, click the **View** tab
2. Click **Themes → Browse for themes**
3. Download a free theme from **https://powerbi.tips/tools/themes-generator/**
   (recommended: a dark professional theme such as "Executive Dark" or "Midnight Blue")
4. Select the downloaded `.json` file → the report canvas updates immediately

---

## Step 3 — Build These 5 Visuals (exact specifications)

Build them on a **single report page** named `"Sales Overview"`.

---

### Visual 1 — KPI Cards (4 cards across the top)

| Card | Field | Format |
|------|-------|--------|
| Total Revenue | `SUM(sales)` | Currency, 0 decimals |
| Total Profit | `SUM(profit)` | Currency, 0 decimals |
| Profit Margin | `SUM(profit) / SUM(sales)` | Percentage, 1 decimal |
| Avg Ship Days | `AVERAGE(order_to_ship_days)` | Decimal, 1 place |

**How to add a KPI card:**
- Insert → Card (New)
- Drag the field into the "Fields" well
- Format → Callout value → set font size to 28+

---

### Visual 2 — Monthly Revenue Trend (Line Chart)

| Setting | Value |
|---------|-------|
| Visual type | Line chart |
| X-axis | `order_year` and `order_month` (drag both; Power BI auto-creates a date hierarchy) |
| Y-axis | `SUM(sales)` |
| Secondary Y-axis (optional) | `SUM(profit)` |
| Legend | *(none — keep it clean)* |
| Title | "Monthly Revenue & Profit Trend" |

**Tip:** Right-click the x-axis → "Show items with no data" OFF. Add a constant line at 0 on the profit axis to highlight loss months.

---

### Visual 3 — Profit by Sub-Category (Horizontal Bar Chart)

| Setting | Value |
|---------|-------|
| Visual type | Clustered bar chart |
| Y-axis | `sub_category` |
| X-axis | `SUM(profit)` |
| Legend | `category` (colours bars by Furniture / Office Supplies / Technology) |
| Sort | Sort by `SUM(profit)` descending |
| Title | "Profit by Sub-Category" |

**Why this matters:** This visual immediately reveals loss-making sub-categories (e.g., Tables, Bookcases) — a key talking point in interviews.

---

### Visual 4 — Sales by Region (Map or Bar Chart)

**Option A — Map visual** (more visually impressive):
| Setting | Value |
|---------|-------|
| Visual type | Map |
| Location | `region` (or `state` for granular map) |
| Bubble size | `SUM(sales)` |
| Tooltip | Add `SUM(profit)` and `profit_margin` |

**Option B — Bar chart** (faster to build, same insight):
| Setting | Value |
|---------|-------|
| Visual type | Clustered bar chart |
| Y-axis | `region` |
| X-axis | `SUM(sales)` |
| Tooltips | `SUM(profit)`, avg discount |

---

### Visual 5 — Customer Segment Donut Chart

| Setting | Value |
|---------|-------|
| Visual type | Donut chart |
| Legend | `segment` |
| Values | `SUM(sales)` |
| Detail labels | Percentage of total |
| Title | "Revenue by Customer Segment" |

---

## Step 4 — Add a Slicer (Date Filter)

1. Insert → Slicer
2. Field: `order_year`
3. Style: **Tile** (so years appear as clickable buttons)
4. This lets viewers filter all 5 visuals by year simultaneously.

---

## Step 5 — Arrange and Polish

Suggested layout:
```
┌──────────────────────────────────────────────┐
│  [KPI Card]  [KPI Card]  [KPI Card]  [KPI]   │
├──────────────────────┬───────────────────────┤
│  Monthly Trend Line  │  Sub-Category Bars    │
├──────────────────────┴───────────────────────┤
│  Region Map/Bar         │  Segment Donut     │
└──────────────────────────────────────────────┘
                     [Year Slicer]
```

**Polish tips:**
- Right-click canvas background → Format page → set Canvas background to a dark colour matching your theme
- Remove all visual borders and shadows for a cleaner look
- Pin the page title text box to the top-left: "Superstore Sales Analytics"

---

## Step 6 — Save and Export

- **Save** the `.pbix` file as `dashboard/superstore_dashboard.pbix`
- **Export PDF**: File → Export → Export to PDF (for sharing without Power BI)
- **Take a screenshot** of the finished dashboard and save as `docs/dashboard_preview.png` — add it to the README

---

## What to Say in an Interview

> "I built the ETL in Python, loaded the result into SQLite, then connected Power BI directly to the database using an ODBC connection. The dashboard shows four KPI cards at the top, a monthly revenue trend line, a sub-category profit bar chart that immediately calls out which product lines are loss-makers, and a segment donut. The whole pipeline can be re-run end-to-end with two Python commands."
