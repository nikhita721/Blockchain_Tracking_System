"""
Web dashboard for visualizing blockchain data
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import threading
import time

from database import DatabaseManager
from config import DASH_HOST, DASH_PORT, DASH_DEBUG, DATABASE_PATH

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Blockchain Tracking Dashboard"

# Initialize database manager
db_manager = DatabaseManager()

# Dashboard layout
app.layout = html.Div([
    html.Div([
        html.H1("🔗 Blockchain Tracking Dashboard", 
                style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),
        
        html.Div([
            html.Div([
                html.H3("📊 Network Statistics", style={'color': '#34495e'}),
                html.Div(id="network-stats", style={'fontSize': 16})
            ], className="four columns", style={'backgroundColor': '#ecf0f1', 'padding': 20, 'margin': 10, 'borderRadius': 10}),
            
            html.Div([
                html.H3("💰 High Value Transactions", style={'color': '#34495e'}),
                html.Div(id="high-value-txs", style={'fontSize': 14})
            ], className="four columns", style={'backgroundColor': '#ecf0f1', 'padding': 20, 'margin': 10, 'borderRadius': 10}),
            
            html.Div([
                html.H3("⏰ Real-time Activity", style={'color': '#34495e'}),
                html.Div(id="realtime-activity", style={'fontSize': 14})
            ], className="four columns", style={'backgroundColor': '#ecf0f1', 'padding': 20, 'margin': 10, 'borderRadius': 10})
        ], className="row"),
        
        html.Div([
            html.H3("📈 Transaction Volume Over Time", style={'color': '#34495e', 'textAlign': 'center'}),
            dcc.Graph(id="transaction-volume-chart")
        ], style={'backgroundColor': '#ecf0f1', 'padding': 20, 'margin': 10, 'borderRadius': 10}),
        
        html.Div([
            html.H3("🧱 Recent Blocks", style={'color': '#34495e', 'textAlign': 'center'}),
            dcc.Graph(id="blocks-chart")
        ], style={'backgroundColor': '#ecf0f1', 'padding': 20, 'margin': 10, 'borderRadius': 10}),
        
        html.Div([
            html.H3("💸 Transaction Fees Analysis", style={'color': '#34495e', 'textAlign': 'center'}),
            dcc.Graph(id="fees-chart")
        ], style={'backgroundColor': '#ecf0f1', 'padding': 20, 'margin': 10, 'borderRadius': 10}),
        
        html.Div([
            html.H3("📋 Recent Transactions", style={'color': '#34495e', 'textAlign': 'center'}),
            dash_table.DataTable(
                id="transactions-table",
                columns=[
                    {"name": "Hash", "id": "hash", "type": "text"},
                    {"name": "Time", "id": "time", "type": "datetime"},
                    {"name": "Value (BTC)", "id": "value_btc", "type": "numeric", "format": {"specifier": ".8f"}},
                    {"name": "Fee (sats)", "id": "fee", "type": "numeric"}
                ],
                style_cell={'textAlign': 'left', 'fontSize': 12, 'fontFamily': 'Arial'},
                style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'value_btc', 'filter_query': '{value_btc} > 1'},
                        'backgroundColor': '#f39c12',
                        'color': 'white',
                    }
                ],
                page_size=10,
                sort_action="native"
            )
        ], style={'backgroundColor': '#ecf0f1', 'padding': 20, 'margin': 10, 'borderRadius': 10}),
        
        # Auto-refresh component
        dcc.Interval(
            id='interval-component',
            interval=5*1000,  # Update every 5 seconds
            n_intervals=0
        )
    ], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#bdc3c7', 'minHeight': '100vh', 'padding': 20})
])

@app.callback(
    Output('network-stats', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_network_stats(n):
    try:
        stats = db_manager.get_network_statistics()
        
        return html.Div([
            html.P(f"📊 Total Transactions: {stats['transaction_count']:,}"),
            html.P(f"🧱 Total Blocks: {stats['block_count']:,}"),
            html.P(f"📏 Latest Block Height: {stats['latest_height']:,}"),
            html.P(f"💰 Average Fee: {stats['average_fee']:.0f} sats"),
            html.P(f"📈 Last Hour: {stats['transactions_last_hour']} txs, {stats['blocks_last_hour']} blocks")
        ])
    except Exception as e:
        return html.P(f"Error loading stats: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('high-value-txs', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_high_value_transactions(n):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            df = pd.read_sql_query("""
                SELECT hash, total_output_value, time 
                FROM transactions 
                WHERE total_output_value > 100000000 
                ORDER BY created_at DESC 
                LIMIT 5
            """, conn)
        
        if df.empty:
            return html.P("No high-value transactions yet")
        
        transactions = []
        for _, row in df.iterrows():
            btc_value = row['total_output_value'] / 100_000_000
            tx_time = datetime.fromtimestamp(row['time']).strftime('%H:%M:%S')
            transactions.append(
                html.P(f"💎 {btc_value:.2f} BTC at {tx_time}", 
                       style={'margin': 5, 'fontSize': 12})
            )
        
        return html.Div(transactions)
    except Exception as e:
        return html.P(f"Error: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('realtime-activity', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_realtime_activity(n):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            # Get activity from last 5 minutes
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM transactions 
                WHERE created_at > datetime('now', '-5 minutes')
            """)
            recent_txs = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE created_at > datetime('now', '-5 minutes')
            """)
            recent_blocks = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT hash FROM transactions 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            latest_tx = cursor.fetchone()
            latest_tx_hash = latest_tx[0][:16] + "..." if latest_tx else "None"
        
        return html.Div([
            html.P(f"🔄 Last 5 min: {recent_txs} transactions"),
            html.P(f"🧱 Last 5 min: {recent_blocks} blocks"),
            html.P(f"🆕 Latest TX: {latest_tx_hash}"),
            html.P(f"⏰ Updated: {datetime.now().strftime('%H:%M:%S')}")
        ])
    except Exception as e:
        return html.P(f"Error: {str(e)}", style={'color': 'red'})

@app.callback(
    Output('transaction-volume-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_transaction_volume_chart(n):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            df = pd.read_sql_query("""
                SELECT 
                    datetime(created_at, 'localtime') as time,
                    COUNT(*) as tx_count,
                    SUM(total_output_value) / 100000000.0 as total_btc
                FROM transactions 
                WHERE created_at > datetime('now', '-1 hour')
                GROUP BY datetime(created_at, 'localtime', 'start of minute')
                ORDER BY time
            """, conn)
        
        if df.empty:
            return {"data": [], "layout": {"title": "No data available"}}
        
        df['time'] = pd.to_datetime(df['time'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['tx_count'],
            mode='lines+markers',
            name='Transactions per minute',
            line=dict(color='#3498db', width=2)
        ))
        
        fig.update_layout(
            title="Transaction Activity (Last Hour)",
            xaxis_title="Time",
            yaxis_title="Transactions per Minute",
            hovermode='x unified'
        )
        
        return fig
    except Exception as e:
        return {"data": [], "layout": {"title": f"Error: {str(e)}"}}

@app.callback(
    Output('blocks-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_blocks_chart(n):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            df = pd.read_sql_query("""
                SELECT height, n_tx, size, time
                FROM blocks 
                ORDER BY created_at DESC 
                LIMIT 20
            """, conn)
        
        if df.empty:
            return {"data": [], "layout": {"title": "No block data available"}}
        
        df = df.sort_values('height')  # Sort by height for proper display
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['height'],
            y=df['n_tx'],
            name='Transactions',
            marker_color='#e74c3c'
        ))
        
        fig.update_layout(
            title="Transactions per Block (Recent 20 Blocks)",
            xaxis_title="Block Height",
            yaxis_title="Number of Transactions"
        )
        
        return fig
    except Exception as e:
        return {"data": [], "layout": {"title": f"Error: {str(e)}"}}

@app.callback(
    Output('fees-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_fees_chart(n):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            df = pd.read_sql_query("""
                SELECT fee
                FROM transactions 
                WHERE fee > 0 AND created_at > datetime('now', '-1 hour')
                ORDER BY created_at DESC
                LIMIT 1000
            """, conn)
        
        if df.empty:
            return {"data": [], "layout": {"title": "No fee data available"}}
        
        fig = px.histogram(
            df, 
            x='fee', 
            nbins=50,
            title="Transaction Fee Distribution (Last Hour)",
            labels={'fee': 'Fee (satoshis)', 'count': 'Number of Transactions'}
        )
        
        fig.update_traces(marker_color='#9b59b6')
        
        return fig
    except Exception as e:
        return {"data": [], "layout": {"title": f"Error: {str(e)}"}}

@app.callback(
    Output('transactions-table', 'data'),
    Input('interval-component', 'n_intervals')
)
def update_transactions_table(n):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            df = pd.read_sql_query("""
                SELECT 
                    hash,
                    time,
                    total_output_value / 100000000.0 as value_btc,
                    fee
                FROM transactions 
                ORDER BY created_at DESC 
                LIMIT 50
            """, conn)
        
        if df.empty:
            return []
        
        # Format the time column
        df['time'] = pd.to_datetime(df['time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Truncate hash for display
        df['hash'] = df['hash'].str[:16] + "..."
        
        return df.to_dict('records')
    except Exception as e:
        return [{"hash": f"Error: {str(e)}", "time": "", "value_btc": 0, "fee": 0}]

def run_dashboard():
    """Run the dashboard server"""
    print(f"Starting dashboard at http://{DASH_HOST}:{DASH_PORT}")
    app.run_server(host=DASH_HOST, port=DASH_PORT, debug=DASH_DEBUG)

if __name__ == "__main__":
    run_dashboard()
