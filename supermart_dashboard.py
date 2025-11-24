import pandas as pd
import numpy as np

from flask import Flask
import dash
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

# -------------------------------------------------
# 1. LOAD & PREPARE DATA
# -------------------------------------------------

DATA_FILE = "Supermart Grocery Sales - Retail Analytics Dataset.xlsx"

df = pd.read_excel(DATA_FILE)

# Clean column names (remove extra spaces)
df.columns = [c.strip() for c in df.columns]

# Ensure expected columns exist
expected_cols = {
    "Order ID", "Customer Name", "Category", "Sub Category",
    "City", "Order Date", "Region", "Sales",
    "Discount", "Profit", "State"
}
missing = expected_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing expected columns in dataset: {missing}")

# Convert date
df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

# Create extra time columns
df["Year"] = df["Order Date"].dt.year
df["MonthName"] = df["Order Date"].dt.month_name()
df["YearMonth"] = df["Order Date"].dt.to_period("M").astype(str)

# Drop rows where Sales/Profit are missing
df = df.dropna(subset=["Sales", "Profit", "Region"])

# -------------------------------------------------
# 2. KPI CALCULATIONS
# -------------------------------------------------

total_sales = df["Sales"].sum()
total_profit = df["Profit"].sum()
total_orders = df["Order ID"].nunique()
total_customers = df["Customer Name"].nunique()
avg_discount = df["Discount"].mean()

# -------------------------------------------------
# 3. PREPARE COMMON FIGURES
# -------------------------------------------------

# Monthly Sales Trend
month_sales = (
    df.groupby("YearMonth", as_index=False)["Sales"]
    .sum()
    .sort_values("YearMonth")
)
fig_monthly_sales = px.line(
    month_sales,
    x="YearMonth",
    y="Sales",
    title="Monthly Sales Trend",
    markers=True,
)

# Sales by Region
region_sales = (
    df.groupby("Region", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
)
fig_sales_region = px.bar(
    region_sales,
    x="Region",
    y="Sales",
    title="Sales by Region",
    text_auto=True,
)

# Profit by Region
region_profit = (
    df.groupby("Region", as_index=False)["Profit"]
    .sum()
    .sort_values("Profit", ascending=False)
)
fig_profit_region = px.bar(
    region_profit,
    x="Region",
    y="Profit",
    title="Profit by Region",
    text_auto=True,
)

# Sales by State (top 15)
state_sales = (
    df.groupby(["Region", "State"], as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(15)
)
fig_state_sales = px.bar(
    state_sales,
    x="State",
    y="Sales",
    color="Region",
    title="Top 15 States by Sales",
    text_auto=True,
)

# Sales by Category
cat_sales = (
    df.groupby("Category", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
)
fig_cat_sales = px.bar(
    cat_sales,
    x="Category",
    y="Sales",
    title="Sales by Category",
    text_auto=True,
)

# Treemap Category -> Sub Category
fig_treemap = px.treemap(
    df,
    path=["Category", "Sub Category"],
    values="Sales",
    title="Sales Distribution by Category & Sub Category",
)

# Top 10 Customers by Sales
cust_sales = (
    df.groupby("Customer Name", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)
fig_cust_sales = px.bar(
    cust_sales,
    x="Customer Name",
    y="Sales",
    title="Top 10 Customers by Sales",
    text_auto=True,
)

# Top 10 Cities by Sales
city_sales = (
    df.groupby("City", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)
fig_city_sales = px.bar(
    city_sales,
    x="City",
    y="Sales",
    title="Top 10 Cities by Sales",
    text_auto=True,
)

# -------------------------------------------------
# 4. DASH APP SETUP
# -------------------------------------------------

server = Flask(__name__)
app = Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
)

primary_color = "#252E3F"
accent_color = "#FF7F0E"
background_color = "#F4F4F9"
card_background = "#FFFFFF"

card_style = {
    "background-color": card_background,
    "border-radius": "10px",
    "box-shadow": "0px 3px 6px rgba(0, 0, 0, 0.1)",
    "padding": "12px",
    "height": "100%",
}

# KPI Cards
def kpi_card(title, value, suffix=""):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(title, className="card-title", style={"color": "#555"}),
                html.H3(f"{value}{suffix}", style={"color": accent_color}),
            ]
        ),
        style=card_style,
    )

total_sales_card = kpi_card("Total Sales", f"${total_sales:,.0f}")
total_profit_card = kpi_card("Total Profit", f"${total_profit:,.0f}")
total_orders_card = kpi_card("Total Orders", f"{total_orders:,}")
total_customers_card = kpi_card("Unique Customers", f"{total_customers:,}")
avg_discount_card = kpi_card("Average Discount", f"{avg_discount*100:.1f}", "%")

# -------------------------------------------------
# 5. PAGE LAYOUTS (TABS)
# -------------------------------------------------

def overview_layout():
    return dbc.Container(
        fluid=True,
        children=[
            dbc.Row(
                [
                    dbc.Col(total_sales_card, md=3, className="mb-3"),
                    dbc.Col(total_profit_card, md=3, className="mb-3"),
                    dbc.Col(total_orders_card, md=3, className="mb-3"),
                    dbc.Col(avg_discount_card, md=3, className="mb-3"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_monthly_sales), md=8, className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_cat_sales), md=4, className="mb-3"),
                ]
            ),
        ],
    )

def region_layout():
    return dbc.Container(
        fluid=True,
        children=[
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_sales_region), md=6, className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_profit_region), md=6, className="mb-3"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_state_sales), md=12, className="mb-3"),
                ]
            ),
        ],
    )

def category_layout():
    return dbc.Container(
        fluid=True,
        children=[
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_cat_sales), md=5, className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_treemap), md=7, className="mb-3"),
                ]
            ),
        ],
    )

def customer_city_layout():
    return dbc.Container(
        fluid=True,
        children=[
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_cust_sales), md=6, className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_city_sales), md=6, className="mb-3"),
                ]
            ),
        ],
    )

# Main layout with Tabs
app.layout = dbc.Container(
    fluid=True,
    style={"background-color": background_color, "min-height": "100vh", "padding": "20px"},
    children=[
        # Header
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3("Supermart Sales Dashboard", style={"color": primary_color}),
                            html.P(
                                "Use the tabs below to navigate between different analysis views.",
                                style={"margin-bottom": 0},
                            ),
                        ]
                    ),
                    style=card_style,
                ),
                width=12,
            ),
            className="mb-3",
        ),

        # Tabs
        dbc.Row(
            dbc.Col(
                dcc.Tabs(
                    id="main-tabs",
                    value="tab-overview",
                    children=[
                        dcc.Tab(label="Overview", value="tab-overview"),
                        dcc.Tab(label="Region Analysis", value="tab-region"),
                        dcc.Tab(label="Category & Sub-Category", value="tab-category"),
                        dcc.Tab(label="Customer & City", value="tab-customer-city"),
                    ],
                ),
                width=12,
            ),
            className="mb-3",
        ),

        # Page content
        dbc.Row(
            dbc.Col(
                html.Div(id="tab-content"),
                width=12,
            )
        ),
    ],
)

# -------------------------------------------------
# 6. CALLBACK TO SWITCH PAGES
# -------------------------------------------------

@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
)
def render_tab_content(tab):
    if tab == "tab-overview":
        return overview_layout()
    elif tab == "tab-region":
        return region_layout()
    elif tab == "tab-category":
        return category_layout()
    elif tab == "tab-customer-city":
        return customer_city_layout()
    else:
        return html.Div("Unknown tab selected.")

# -------------------------------------------------
# 7. RUN APP
# -------------------------------------------------

if __name__ == "__main__":
    # debug=False for cleaner, more "production" look (no dev tools bar)
    app.run(debug=False, host="127.0.0.1", port=8060)