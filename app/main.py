from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
import json

app = FastAPI(title="Sales Analytics Dashboard")

# Set up templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

DB_PATH = os.path.join(BASE_DIR, "..", "database", "sales.db")

def get_data(query: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    # 1. KPI Summary
    kpi_query = """
    SELECT
        ROUND(SUM(sales), 2)              AS total_revenue,
        ROUND(SUM(profit), 2)             AS total_profit,
        ROUND(SUM(profit) / SUM(sales) * 100, 2)  AS profit_margin_pct,
        ROUND(AVG(order_to_ship_days), 1) AS avg_ship_days
    FROM sales;
    """
    kpi_df = get_data(kpi_query)
    kpis = kpi_df.iloc[0].to_dict() if not kpi_df.empty else {}

    # 2. Line Chart: Sales by order_month
    line_query = """
    SELECT
        order_year || '-' || substr('00' || order_month, -2, 2) as month_key,
        order_month_name || ' ' || order_year as display_month,
        ROUND(SUM(sales), 2) AS monthly_revenue
    FROM sales
    GROUP BY order_year, order_month, order_month_name
    ORDER BY order_year, order_month;
    """
    line_df = get_data(line_query)
    fig_line = px.line(
        line_df, 
        x="display_month", 
        y="monthly_revenue", 
        title="Sales by Month",
        markers=True,
        labels={"display_month": "Month", "monthly_revenue": "Revenue ($)"}
    )
    # Apply a modern template
    fig_line.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    # 3. Bar Chart: Profit by sub_category
    bar_query = """
    SELECT
        sub_category,
        ROUND(SUM(profit), 2) AS total_profit
    FROM sales
    GROUP BY sub_category
    ORDER BY total_profit DESC;
    """
    bar_df = get_data(bar_query)
    fig_bar = px.bar(
        bar_df, 
        x="total_profit", 
        y="sub_category", 
        orientation='h', 
        title="Profit by Sub-Category",
        labels={"total_profit": "Profit ($)", "sub_category": "Sub-Category"}
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    # 4. Donut Chart: Sales by segment
    donut_query = """
    SELECT
        segment,
        ROUND(SUM(sales), 2) AS total_revenue
    FROM sales
    GROUP BY segment
    ORDER BY total_revenue DESC;
    """
    donut_df = get_data(donut_query)
    fig_donut = px.pie(
        donut_df, 
        values="total_revenue", 
        names="segment", 
        hole=0.5, 
        title="Sales by Segment"
    )
    fig_donut.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    # Convert figures to JSON for frontend rendering
    charts = {
        "line_chart": json.loads(fig_line.to_json()),
        "bar_chart": json.loads(fig_bar.to_json()),
        "donut_chart": json.loads(fig_donut.to_json())
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "kpis": kpis, 
            "charts": charts
        }
    )


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "ok"}
