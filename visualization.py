import pandas as pd
import json
import plotly.graph_objects as go
from urllib.request import urlopen
import plotly.express as px
import re
from datetime import datetime

df_city = pd.read_csv('https://media.githubusercontent.com/media/DioPedro/SCC0252-Projeto-Visualizacao/main/city.csv', index_col=0)
df_state = pd.read_csv('https://media.githubusercontent.com/media/DioPedro/SCC0252-Projeto-Visualizacao/main/state.csv', index_col=0)
df_region = pd.read_csv('https://media.githubusercontent.com/media/DioPedro/SCC0252-Projeto-Visualizacao/main/region.csv', index_col=0)

# Utilizamos de alguns geojson para a visualização geográfica, facilitando assim a formação da imagem
brazil_code = 100
with urlopen(f'https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-{brazil_code}-mun.json') as response:
    brazil_json = json.loads(response.read())

with urlopen('https://raw.githubusercontent.com/DioPedro/SCC0252-Projeto-Visualizacao/main/br_regions.json') as response:
    regions_json = json.loads(response.read())

with urlopen('https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson') as response:
    Brazil = json.load(response)

geo_dict = {
    'city': {
        'geo': 'city',
        'geojson': brazil_json,
        'featureidkey': 'properties.id',
        'locations': 'city_code',
    },
    'state': {
        'geo': 'state',
        'geojson': Brazil,
        'featureidkey': 'properties.name',
        'locations': 'full_state'
    },
    'region': {
        'geo': 'region',
        'geojson': regions_json,
        'featureidkey': 'properties.nome',
        'locations': 'region'
    }
}

analysis_features = {
    'cases',
    'deaths',
    'cases/population',
    'deaths/population',
    'cases per day/population',
    'deaths per day/population',
    'cases per day',
    'deaths per day'
}

temporal_unities = {
    'month',
    'semester',
    'year',
    'date'
}

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

def create_parallel(geo, df):
    new_df = df.copy()
    
    if geo == 'region':
        new_df['color_id'] = new_df.apply(lambda row: region_id[row.region], axis = 1)

    if geo == 'city':
        new_df['color_id'] = new_df.apply(lambda row: city_ids[str(row.city_code)] if str(row.city_code) in city_ids else None, axis = 1)
        new_df = new_df.dropna()
        new_df['color_id'] = new_df['color_id'].astype(int)

    if geo == 'state':
        new_df['color_id'] = new_df.apply(lambda row: state_ids[row.full_state], axis = 1)

    return px.parallel_coordinates(new_df,
                              color = new_df['color_id'],
                              dimensions = list(analysis_features),
                              color_continuous_scale = px.colors.sequential.Rainbow,
                              title = 'Parallel Coordinates')


# Função que possibilita a seleção do dataset, passando como parâmetro a feature e a análise temporal desejadas
# para a visualização

# geospecs: list of places
# time_specs: list of times
# time_range: (start, end) both ends are included
def select_analysis(features, time, geo, geo_specs=None, time_specs=None, time_range=None):
    data = geo_dict[geo]
    if geo == 'region':
        dataframe = df_region
    elif geo == 'state':
        dataframe = df_state
    else:
        dataframe = df_city
    
    if time_specs is not None and time_range is not None:
        print('Cannot add time_specs and time_range arguments in the same call')
        return None

    groupbied = dataframe.groupby([data['locations'], time])[features]
    check = False
    for feature in features:
        if re.match('^.*per day.*$', feature):
            check = True

    if check:    
        df = pd.DataFrame(groupbied.sum()).reset_index()
    else:
        df = pd.DataFrame(groupbied.max()).reset_index()

    if geo_specs:
        df = df.loc[df[data['geo']].isin(geo_specs)]

    if time_specs:
        df = df.loc[df[time].isin(time_specs)]

    if time_range:
        if time_range[0]:
            df = df.loc[(df[time] >= time_range[0])]
        if time_range[1]:
            df = df.loc[(df[time]) <= time_range[1]]

    return df

# Função que cria um título personalizado para o gráfico de acordo com os parâmetros escolhidos para sua geração

def create_title(feature, time, geo, geo_specs, time_specs, time_range):
    grammar_geo = {
        'city': 'cities',
        'state': 'states',
        'region': 'regions'
    }

    title = feature.capitalize() + ' by ' + geo.capitalize() + ' and ' + time.capitalize()
    if geo_specs:
        geos = geo_specs[:3]
        title += ' in the '
        if len(geos) > 1:
            title += grammar_geo[geo]
        else:
            title += geo
        title += ' of ' + ', '.join(geos)
        if len(geo_specs) > 3:
            title += ", ..."

    if time_specs:
        times = time_specs[:3]
        title += ' in the ' + time.capitalize() + 's of '
        title += ', '.join(times)
        if len(time_specs) > 3:
            title += ", ..."

    if time_range:
        if time_range[0] is None:
            title += ' until the ' + time.capitalize() + ' of ' + time_range[1]
        elif time_range[1] is None:
            title += ' starting from the ' + time.capitalize() + ' of ' + time_range[0]
        else:
            title += ' between the ' + time.capitalize() + 's of ' + time_range[0] + ' and ' + time_range[1]

    return title

def create_map(feature, time, geo, df, geo_specs=None, time_specs=None, time_range=None):
    fig = px.choropleth(df, geojson = geo_dict[geo]["geojson"], featureidkey = geo_dict[geo]["featureidkey"],
                            locations=geo_dict[geo]['locations'], color=feature,
                            color_continuous_scale="Viridis",
                            animation_frame = time,
                            range_color = (df[feature].min(), df[feature].max()))
    fig.update_geos(fitbounds = "locations", visible = False)
    fig.update_layout(title_text = create_title(feature, time, geo, geo_specs, time_specs, time_range))

    return fig

def create_animated_line(feature, time, geo, df, geo_specs=None, time_specs=None, time_range=None):
    time_uniques = df[time].unique()
    geo_uniques = df[geo].unique()

    frames = []
    for spec_time in time_uniques:
        frame_data = []
        for spec_geo in geo_uniques:
            geo_frame_data = go.Scatter(x=df.loc[(df[time] <= spec_time) & (df[geo] == spec_geo)][time],
                                        y=df.loc[(df[time] <= spec_time) & (df[geo] == spec_geo)][feature],
                                        mode='lines',
                                        name=spec_geo)
            frame_data.append(geo_frame_data)
        curr_frame = go.Frame(data=frame_data)
        frames.append(curr_frame)

    data = []
    for region in geo_uniques:
        region_data = go.Scatter(x=df.loc[(df[time] <= time_uniques[0]) & (df[geo] == region)][time],
                                y=df.loc[(df[time] <= time_uniques[0]) & (df[geo] == region)][feature],
                                name=region,
                                mode='lines')
        data.append(region_data)
        
    xaxis = {"title": time, "range": [time_uniques[0], time_uniques[len(time_uniques)-1]]}
    if time == 'semester':
        xaxis = {"title": time, "categoryarray": ['2020-01', '2020-02', '2021-01'], "type": "category", "autorange": False}

    figure = go.Figure(
        data=data,
        layout={"title": create_title(feature, time, geo, geo_specs, time_specs, time_range),
                "updatemenus": [
                    {
                        "type": "buttons",
                        "buttons": [{
                            "label": "Play",
                            "method": "animate",
                            "args": [None]}]},
                    ],
                "xaxis": xaxis,
                "yaxis": {"title": feature, "range": [df[feature].min(), df[feature].max()]}
                },
        frames = frames
    )

    return figure

def create_parallel_coordinates(geo, df):
    region_id = {
        'Norte': 1,
        'Nordeste': 2,
        'Centro-Oeste': 3,
        'Sudeste': 4,
        'Sul': 5
    }

    if geo == 'region':
        df['color_id'] = df.apply(lambda row: region_id[row.region], axis = 1)

    if geo == 'city':
        df['color_id'] = df.apply(lambda row: city_ids[str(row.city_code)] if str(row.city_code) in city_ids else None, axis = 1)
        df = df.dropna()
        df['color_id'] = df['color_id'].astype(int)

    if geo == 'state':
        df['color_id'] = df.apply(lambda row: state_ids[row.full_state], axis = 1)

    fig = px.parallel_coordinates(df,
                              color = df['color_id'],
                              dimensions = list(analysis_features),
                              color_continuous_scale = px.colors.sequential.Rainbow,
                              title = 'Parallel Coordinates')
    
    return fig