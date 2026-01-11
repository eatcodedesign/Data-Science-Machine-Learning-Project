import os
import pandas as pd
from dash import Dash, html, dcc, Input, Output
import plotly.express as px

# Locate data file relative to this script
DATA_PATH = os.path.join(os.path.dirname(__file__), "spacex_launch_dash.csv")

# Read the data
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Could not find data file at {DATA_PATH}. Make sure 'spacex_launch_dash.csv' is in the project folder.")

spacex_df = pd.read_csv(DATA_PATH)

# --- Data Pre-processing ---
# Add friendly outcome label column for charts
spacex_df['class'] = spacex_df['class'].astype(int)
spacex_df['Outcome'] = spacex_df['class'].map({1: 'Success', 0: 'Failure'})

# Make Outcome an ordered categorical for consistent ordering in plots (Success=Green, Failure=Red)
spacex_df['Outcome'] = pd.Categorical(spacex_df['Outcome'], categories=['Failure', 'Success'], ordered=True)

# Color mapping for Outcome labels
OUTCOME_COLORS = {'Success': '#00cc96', 'Failure': '#EF553B'}

# Calculate Payload stats for the slider
min_payload = int(spacex_df['Payload Mass (kg)'].min())
max_payload = int(spacex_df['Payload Mass (kg)'].max())
q1 = int(spacex_df['Payload Mass (kg)'].quantile(0.25))
q2 = int(spacex_df['Payload Mass (kg)'].quantile(0.50))
q3 = int(spacex_df['Payload Mass (kg)'].quantile(0.75))

# --- App Layout ---
app = Dash(__name__)
app.title = "SpaceX Launch Records Dashboard"

# Build dropdown options
site_options = [{'label': 'All Sites', 'value': 'ALL'}] + [
    {'label': s, 'value': s} for s in sorted(spacex_df['Launch Site'].unique())
]

app.layout = html.Div(children=[
    html.H1('SpaceX Launch Records Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'fontSize': '40px'}),

    html.Div([
        dcc.Dropdown(
            id='site-dropdown',
            options=site_options,
            value='ALL',
            placeholder="Select a Launch Site here",
            searchable=True
        ),
    ], style={'width': '80%', 'margin': '0 auto'}), # Centered dropdown with width constraint

    html.Br(),

    html.Div(dcc.Graph(id='success-pie-chart')),
    
    html.Br(),

    html.Div([
        html.P("Payload range (Kg):", style={'fontSize': '20px'}),
        dcc.RangeSlider(
            id='payload-slider',
            min=min_payload,
            max=max_payload,
            step=1000, # Increased step slightly for performance
            value=[min_payload, max_payload],
            marks={
                min_payload: str(min_payload),
                q1: str(q1),
                q2: str(q2),
                q3: str(q3),
                max_payload: str(max_payload)
            }
        ),
    ], style={'width': '90%', 'margin': '0 auto'}), # Add margins for better aesthetics

    html.Br(),
    
    html.Div(dcc.Graph(id='success-payload-scatter-chart'))
])

# --- Callbacks ---

# Pie chart callback
@app.callback(
    Output('success-pie-chart', 'figure'),
    Input('site-dropdown', 'value')
)
def build_pie(site_dropdown):
    if site_dropdown == 'ALL':
        # Show total successful launches by site
        success_counts = spacex_df[spacex_df['class'] == 1].groupby('Launch Site').size().reset_index(name='counts')
        fig = px.pie(success_counts, names='Launch Site', values='counts', 
                     title='Total Successful Launches by Site',
                     hole=0.3) # Donut style
    else:
        # Show success vs failure for the selected site
        specific = spacex_df[spacex_df['Launch Site'] == site_dropdown]
        fig = px.pie(specific, names='Outcome',
                     title=f'Success vs Failure for {site_dropdown}',
                     color_discrete_map=OUTCOME_COLORS,
                     hole=0.3) # Donut style
    
    fig.update_layout(title_x=0.5) # Center title
    return fig

# Scatter callback (site + payload)
@app.callback(
    Output('success-payload-scatter-chart', 'figure'),
    [Input('site-dropdown', 'value'),
     Input('payload-slider', 'value')]
)
def update_scatter(site_dropdown, payload_range):
    low, high = payload_range
    
    # Filter by Payload
    mask = (spacex_df['Payload Mass (kg)'] >= low) & (spacex_df['Payload Mass (kg)'] <= high)
    df_filtered = spacex_df[mask]
    
    # Filter by Site if not ALL
    if site_dropdown != 'ALL':
        df_filtered = df_filtered[df_filtered['Launch Site'] == site_dropdown]

    fig = px.scatter(df_filtered, x="Payload Mass (kg)", y="Outcome",
                     color="Outcome",
                     symbol="Booster Version Category",
                     color_discrete_map=OUTCOME_COLORS,
                     hover_data=['Flight Number', 'Launch Site', 'Payload Mass (kg)'],
                     title="Payload vs. Launch Outcome",
                     opacity=0.65) # Add opacity to see overlaps

    # Ensure categorical y-axis uses the defined order
    fig.update_yaxes(categoryorder='array', categoryarray=['Failure', 'Success'])
    
    # Visual Polish
    fig.update_traces(marker=dict(size=12)) # Larger markers
    fig.update_layout(title_x=0.5) # Center title
    
    return fig

if __name__ == '__main__':
    # 'use_reloader=False' is kept for compatibility with Jupyter/Windows environments
    app.run(debug=True, host='127.0.0.1', port=8050, use_reloader=False)