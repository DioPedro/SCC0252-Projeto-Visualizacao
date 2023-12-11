# Import packages
from dash import Dash, dcc, html, callback, Output, Input
from visualization import create_map, create_animated_line, create_parallel, analysis_features, temporal_unities, select_analysis, geo_dict
import plotly.express as px
from datetime import date

# Initialize the app
app = Dash(__name__)

geo_options = {'city', 'region', 'state'}

# Creating city_ids which will be used to color the parallel coordinates
city_ids = {}
for idx, city in enumerate(geo_dict['city']['geojson']['features']):
    if city['properties']['id'] not in city_ids:
        city_ids[city['properties']['id']] = idx + 1

# Creating the state_ids
state_ids = {}
for idx, state in enumerate(geo_dict['state']['geojson']['features']):
    if state['properties']['name'] not in state_ids:
        state_ids[state['properties']['name']] = idx + 1
        
region_id = {
        'Norte': 1,
        'Nordeste': 2,
        'Centro-Oeste': 3,
        'Sudeste': 4,
        'Sul': 5
    }

def adapt_df_parallel(geo, df):
    new_df = df.copy()
    
    if geo == 'region':
        new_df['color_id'] = new_df.apply(lambda row: region_id[row.region], axis = 1)

    if geo == 'city':
        new_df['color_id'] = new_df.apply(lambda row: city_ids[str(row.city_code)] if str(row.city_code) in city_ids else None, axis = 1)
        new_df = new_df.dropna()
        new_df['color_id'] = new_df['color_id'].astype(int)

    if geo == 'state':
        new_df['color_id'] = new_df.apply(lambda row: state_ids[row.full_state], axis = 1)

    return new_df

# App layout
app.layout = html.Div([
    html.H1(children='Brazil Covid Analysis', style = {"text-align": "center", "margin":"20px 0px 20px 0px"}
    ),

    html.Div(
        children = [
            html.P("MUDAR O TEXTO DO SITE E COLOCAR EXPLICAÇÕES AQUI")
        ],
        style = {"background":"fafafa", "width":"80%", "margin": "auto auto", "padding":"40px 40px 40px 40px", "boder-radius": "5px"}),

    html.Div([
        html.Label(['Feature']),
        dcc.Dropdown(options=list(analysis_features), value='cases', id='feature'),
    ], style={'display': 'inline-block', 'margin-right': '10px','margin-left': '60px', 'width':'20%'}),

    html.Div([
        html.Label(['Time Unit']),
        dcc.Dropdown(options=list(temporal_unities), value='semester', id='time'),
    ], style={'display': 'inline-block', 'margin-right': '10px', 'width':'20%'}),

    html.Div([
        html.Label(['Geographical Unit']),
        dcc.Dropdown(options=list(geo_options), value='region', id='geo'),
    ], style={'display': 'inline-block', 'width':'20%'}),
    
    html.Div([
        html.Label(['Choose Month']),
        dcc.DatePickerSingle(
            id='month_picker',
            min_date_allowed=date(2020, 3, 27),
            max_date_allowed=date(2021, 5, 23),
            display_format='MM-YYYY'
        ),
    ], style={'display': 'inline-block', 'width':'20%'}),
    
    dcc.Loading(
        id="loading-vis",
        type="circle",
        children=html.Div([
            html.H2(children='Map Visualization', style = {'margin-left': '30px'}),
            dcc.Graph(id="map"),

            html.H2(children='Line Visualization', style = {'margin-left': '30px'}),
            dcc.Graph(id="line"),
            
            html.H2(children="Parallel Coordinates Visualization", style = {'margin-left': '30px'}),
            dcc.Graph(id="parallel")
        ],
        )
    )
],
style = {"font-family": "Courier New"}
)

@callback(
    [Output('map', 'figure'),
     Output('line', 'figure'),
     Output('parallel', 'figure')
    ],
    [Input('feature', 'value'),
     Input('time', 'value'),
     Input('geo', 'value'),
     Input('month_picker', 'date')])
def get_visualizations(feature, time, geo, date_value):
    date_string = None
    if date_value is not None:  
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%Y-%m')
    df = select_analysis(feature, time, geo, geo_specs=None, time_specs=None, time_range=None)
    
    if time == 'month' and date_string is not None:
        parallel_df = select_analysis(list(analysis_features), time, geo, geo_specs=None, time_specs=[date_string], time_range=None)
    else:
        parallel_df = select_analysis(list(analysis_features), time, geo, geo_specs=None, time_specs=None, time_range=None)
    
    return create_map(feature, time, geo, df), create_animated_line(feature, time, geo, df), create_parallel(geo, parallel_df)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)