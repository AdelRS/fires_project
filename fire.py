import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from urllib.request import urlopen
import json
import plotly.figure_factory as ff

df = pd.read_csv('final.csv', low_memory=False)

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
)
scl = [0,"rgb(255, 0, 0)"],[0.2,"rgb(255, 25, 0)"],[0.4,"rgb(255, 85, 0)"],\
[0.6,"rgb(255, 157, 0)"],[0.8,"rgb(255, 225, 0)"],[1,"rgb(246, 255, 0)"]



# Callback para los mapas y el gráfico de líneas paralelas++++++++++++++++++++++
@app.callback(
    [Output('map','figure'),
    Output('paral','figure'),
    Output('donut','figure')],
    [Input('year_picker','value'),
    Input('map_type','value')]
)
def update_figure(year_picker, map_type):
    px.set_mapbox_access_token("pk.eyJ1IjoiYWRlbHIiLCJhIjoiY2thczR3aGppMDRnMzJxbzM4YjlpcWdvaCJ9.uMo36J0VlZEK5khoJZIP-g")
    filtered_df = df[(df['FIRE_YEAR'] >= year_picker[0]) & (df['FIRE_YEAR'] <= year_picker[1])]

    if map_type == 'fire_all':
        fig = go.Figure(go.Scattermapbox(
            lat=filtered_df['LATITUDE'],
            lon=filtered_df['LONGITUDE'],
            text = 'Cause: ' + filtered_df['STAT_CAUSE_DESCR'].astype(str),
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=3,
                color = df['COLOR'],
                colorscale = scl,
                cmin = 0,
                cmax = 1,
                opacity=0.5
                )))

        fig.update_layout(
            hovermode='closest',
            margin=dict(l=20, r=20, t=20, b=20),
            mapbox=dict(
                accesstoken="pk.eyJ1IjoiYWRlbHIiLCJhIjoiY2thczR3aGppMDRnMzJxbzM4YjlpcWdvaCJ9.uMo36J0VlZEK5khoJZIP-g",
                bearing=0,
                center=dict(
                    lat=39.50,
                    lon=-98.35
                    ),
                    pitch=0,
                    zoom=2.7
            ),
            title_text='<b>Total fires: </b>'+ str(filtered_df['LATITUDE'].count()) + ' / ' + '<b>Burned area (acres): </b>' + str(round((filtered_df['FIRE_SIZE'].sum()/1000000), 2)) + 'M',
            title_font_size=11)

    elif map_type == 'fire_den':
        fig = px.density_mapbox(lat=filtered_df['LATITUDE'], lon=filtered_df['LONGITUDE'], z=filtered_df['FIRE_SIZE'],
                                 radius=10, center = {"lat": 37.0902, "lon": -95.7129}, zoom=2.7
                                 #,animation_frame=df['FIRE_YEAR']
                                 )
        fig.update_layout(mapbox_style="stamen-terrain", margin={"r":0,"t":0,"l":0,"b":0})

    elif map_type == 'burn_counties':
        df_counties_map = filtered_df.groupby(['FIPS_CODE','FIPS_NAME'], as_index=False)['FIRE_SIZE'].sum()
        df_counties_map.columns = ['Fips code', 'Region', 'Acres']
        with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
            counties = json.load(response)

        fig = px.choropleth_mapbox(df_counties_map, geojson=counties, locations='Fips code', color='Acres',
                                   color_continuous_scale="Viridis",
                                   range_color=(0, 2200000),
                                   mapbox_style="carto-positron",
                                   zoom=2.7, center = {"lat": 37.0902, "lon": -95.7129},
                                   opacity=0.6, labels={"color": "Acres"},
                                   hover_data=['Region']
                                  )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    elif map_type == 'avg_size':
        fig = ff.create_hexbin_mapbox(
            data_frame=filtered_df, lat="LATITUDE", lon="LONGITUDE",
            zoom=2.7, center = {"lat": 37.0902, "lon": -95.7129},
            mapbox_style="carto-positron",
            nx_hexagon=125, opacity=0.6, labels={"color": "Acres"},
            color="FIRE_SIZE", agg_func=np.mean, color_continuous_scale="Cividis",
            range_color=[0,1000]
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    elif map_type == 'number_fire':
        fig = ff.create_hexbin_mapbox(
            data_frame=filtered_df, lat="LATITUDE", lon="LONGITUDE", nx_hexagon=125,
            zoom=2.7, center = {"lat": 37.0902, "lon": -95.7129},
            color_continuous_scale="Cividis", labels={"color": "Fires"},
            opacity=0.6, min_count=1,
            show_original_data=False, original_data_marker=dict(opacity=0.1, size=1, color="deeppink")
        )
        fig.update_layout(margin=dict(b=0, t=0, l=0, r=0))

    elif map_type == 'total_area':
        fig = ff.create_hexbin_mapbox(
            data_frame=filtered_df, lat="LATITUDE", lon="LONGITUDE",
            zoom=2.7, center = {"lat": 37.0902, "lon": -95.7129},
            nx_hexagon=125, opacity=0.6, labels={"color": "Acres"},
            color="FIRE_SIZE", agg_func=np.sum, color_continuous_scale="Magma"
        )
        fig.update_layout(margin=dict(b=0, t=0, l=0, r=0))

    fig_paral = go.Figure(data=
        go.Parcoords(
            line = dict(color = df['STAT_CAUSE_CODE'],
                       colorscale =  [[0,'purple'],[0.5,'lightseagreen'],[1,'gold']]),
            dimensions = list([
                dict(tickvals = [9, 1, 5, 4, 2, 7, 8, 6, 3, 11, 12, 10, 13],
                     constraintrange = [1],
                     ticktext = ['Miscellaneous', 'Lightning', 'Debris Burning', 'Campfire', 'Equipment Use', 'Arson', 'Children', 'Railroad', 'Smoking', 'Powerline', 'Structure', 'Fireworks', 'Missing/Undefined'],
                     label = 'Fire cause', values = df['STAT_CAUSE_CODE']),
                dict(range = [0,df['FIRE_SIZE'].max()],
                     constraintrange = [200000,df['FIRE_SIZE'].max()],
                     ticktext = [df['FIRE_SIZE_CLASS'].unique().tolist()],
                     label = 'Fire size', values = df['FIRE_SIZE']),
                dict(tickvals = [11, 8, 7, 9, 4, 1, 6, 10, 2, 12, 3, 5],
                     ticktext = ['USFS', 'PRIVATE', 'MISSING/NOT SPECIFIED', 'STATE', 'FEDERAL', 'BIA', 'FWS', 'TRIBAL', 'BLM', 'NPS', 'BOR', 'FOREIGN'],
                     label = 'Owner of land', values = df['OWNER_CODE']),
                dict(label = 'Day of year', values = df['DISCOVERY_DOY'])
            ])
        )
    )

    fig_paral.update_layout(
        plot_bgcolor = 'white',
        paper_bgcolor = 'white'
    )

    fig_donut = px.sunburst(filtered_df, path=['REGION', 'STATE', 'STAT_CAUSE_DESCR'], values='FIRE_SIZE'
                            #color='FIRE_SIZE')
                            #color_continuous_scale='RdBu'
                            )
    fig_donut.update_layout(margin=dict(b=0, t=0, l=0, r=0))

    return fig, fig_paral, fig_donut

# FIN Callback para los mapas+++++++++++++++++++++++++++++++++++++++++++++++++++

# Callback para la tabla y los gráficos de agencias afectadas+++++++++++++++++++
@app.callback([
    Output('BIA_fires','children'),
    Output('FS_fires','children'),
    Output('FWS_fires','children'),
    Output('NPS_fires','children'),
    Output('BLM_fires','children'),
    Output('BIA_size','children'),
    Output('FS_size','children'),
    Output('FWS_size','children'),
    Output('NPS_size','children'),
    Output('BLM_size','children'),
    Output('BIA_ratio','children'),
    Output('FS_ratio','children'),
    Output('FWS_ratio','children'),
    Output('NPS_ratio','children'),
    Output('BLM_ratio','children'),
    Output('BIA_graph_fire','figure'),
    Output('FS_graph_fire','figure'),
    Output('FWS_graph_fire','figure'),
    Output('NPS_graph_fire','figure'),
    Output('BLM_graph_fire','figure')],
    Input('year_picker','value')
)
def update_agencys(year_picker):
    filtered_df = df[(df['FIRE_YEAR'] >= year_picker[0]) & (df['FIRE_YEAR'] <= year_picker[1])]
    df_table = filtered_df.groupby('OWNER_DESCR', as_index = False)['FIRE_SIZE'].count()
    df_table.columns = ['OWNER_DESCR', 'count']
    #print(df1.loc[df1['OWNER_DESCR'] == 'BIA', 'count'])
    BIA_fires = df_table.loc[df_table['OWNER_DESCR'] == 'BIA', 'count']
    FS_fires = df_table.loc[df_table['OWNER_DESCR'] == 'USFS', 'count']
    FWS_fires = df_table.loc[df_table['OWNER_DESCR'] == 'FWS', 'count']
    NPS_fires = df_table.loc[df_table['OWNER_DESCR'] == 'NPS', 'count']
    BLM_fires = df_table.loc[df_table['OWNER_DESCR'] == 'BLM', 'count']

    df_table = filtered_df.groupby('OWNER_DESCR', as_index = False)['FIRE_SIZE'].sum()
    df_table.columns = ['OWNER_DESCR', 'sum']
    BIA_size = round((df_table.loc[df_table['OWNER_DESCR'] == 'BIA', 'sum'])/1000000,4)
    FS_size = round((df_table.loc[df_table['OWNER_DESCR'] == 'USFS', 'sum'])/1000000,4)
    FWS_size = round((df_table.loc[df_table['OWNER_DESCR'] == 'FWS', 'sum'])/1000000,4)
    NPS_size = round((df_table.loc[df_table['OWNER_DESCR'] == 'NPS', 'sum'])/1000000,4)
    BLM_size = round((df_table.loc[df_table['OWNER_DESCR'] == 'BLM', 'sum'])/1000000,4)

    BIA_ratio = round((BIA_size*1000000/BIA_fires),2)
    FS_ratio = round((FS_size*1000000/FS_fires),2)
    FWS_ratio = round((FWS_size*1000000/FWS_fires),2)
    NPS_ratio = round((NPS_size*1000000/NPS_fires),2)
    BLM_ratio = round((BLM_size*1000000/BLM_fires),2)

    df_table = filtered_df[(filtered_df['OWNER_DESCR'] == 'BIA')]
    df_table = df_table.groupby('FIRE_YEAR', as_index = False)['FIRE_SIZE'].count()
    BIA_graph_fire = go.Figure(data=go.Scatter(x=df_table['FIRE_YEAR'], y=df_table['FIRE_SIZE']))
    BIA_graph_fire.update_layout(margin=dict(b=2, t=2, l=0, r=0), height=83, xaxis=dict(showticklabels = False), yaxis=dict(showticklabels = False))

    df_table = filtered_df[(filtered_df['OWNER_DESCR'] == 'USFS')]
    df_table = df_table.groupby('FIRE_YEAR', as_index = False)['FIRE_SIZE'].count()
    FS_graph_fire = go.Figure(data=go.Scatter(x=df_table['FIRE_YEAR'], y=df_table['FIRE_SIZE']))
    FS_graph_fire.update_layout(margin=dict(b=2, t=2, l=0, r=0), height=83, xaxis=dict(showticklabels = False), yaxis=dict(showticklabels = False))

    df_table = filtered_df[(filtered_df['OWNER_DESCR'] == 'FWS')]
    df_table = df_table.groupby('FIRE_YEAR', as_index = False)['FIRE_SIZE'].count()
    FWS_graph_fire = go.Figure(data=go.Scatter(x=df_table['FIRE_YEAR'], y=df_table['FIRE_SIZE']))
    FWS_graph_fire.update_layout(margin=dict(b=2, t=2, l=0, r=0), height=83, xaxis=dict(showticklabels = False), yaxis=dict(showticklabels = False))

    df_table = filtered_df[(filtered_df['OWNER_DESCR'] == 'NPS')]
    df_table = df_table.groupby('FIRE_YEAR', as_index = False)['FIRE_SIZE'].count()
    NPS_graph_fire = go.Figure(data=go.Scatter(x=df_table['FIRE_YEAR'], y=df_table['FIRE_SIZE']))
    NPS_graph_fire.update_layout(margin=dict(b=2, t=2, l=0, r=0), height=83, xaxis=dict(showticklabels = False), yaxis=dict(showticklabels = False))

    df_table = filtered_df[(filtered_df['OWNER_DESCR'] == 'BLM')]
    df_table = df_table.groupby('FIRE_YEAR', as_index = False)['FIRE_SIZE'].count()
    BLM_graph_fire = go.Figure(data=go.Scatter(x=df_table['FIRE_YEAR'], y=df_table['FIRE_SIZE']))
    BLM_graph_fire.update_layout(margin=dict(b=2, t=2, l=0, r=0), height=83, xaxis=dict(showticklabels = False), yaxis=dict(showticklabels = False))

    return BIA_fires, FS_fires, FWS_fires, NPS_fires, BLM_fires, BIA_size, FS_size, FWS_size, NPS_size, BLM_size, BIA_ratio, FS_ratio, FWS_ratio, NPS_ratio, BLM_ratio, BIA_graph_fire, FS_graph_fire, FWS_graph_fire, NPS_graph_fire, BLM_graph_fire

# FIN Callback para la tabla y los gráficos de agencias afectadas+++++++++++++++

# Callback gráfico de calor y barras según clasificación tamaño incendios y propietario del suelo.
@app.callback(Output('2d_fires_owner','figure')
                ,
                Input('year_picker','value'),
)

def update_figure(year_picker):
    filtered_df = df[(df['FIRE_YEAR'] >= year_picker[0]) & (df['FIRE_YEAR'] <= year_picker[1])]
    fig_2d_fires_owner = px.density_heatmap(filtered_df, x="FIRE_SIZE_CLASS", y="OWNER_DESCR", marginal_x="histogram", marginal_y="histogram")
    fig_2d_fires_owner.update_layout(title_text='<b>USA codes (acres):A<=0.25, B=0.26-9.9, C=10.0-99.9, D=100-299, E=300-999, F=1000-4999,G=5000+</b>',
                                    title_font_size=11,
                                    title_x=0.5,
                                    title_xanchor='center',
                                    xaxis_title="USA fire size classification",
                                    yaxis_title="Land owner",
                                    margin=dict(b=0, t=15, l=0, r=0),
                                    font=dict(
                                        family="Courier New, monospace",
                                        size=14
                                    ))
    return fig_2d_fires_owner
# FIN Callback gráfico de calor y barras según clasificación tamaño incendios y propietario del suelo.

@app.callback(Output('displot','figure')
                ,
                [Input('year_picker','value'),
                Input('displot_option','value')]
)

def update_figure(year_picker, displot_option):
    filtered_df = df[(df['FIRE_YEAR'] >= year_picker[0]) & (df['FIRE_YEAR'] <= year_picker[1])]
    if displot_option == 'burned_owner':
        fig_displot = px.histogram(filtered_df, x="DISCOVERY_DOY", y="FIRE_SIZE", color="OWNER_DESCR",
                                    marginal="box", # or violin, rug
                                    hover_data=filtered_df.columns)
        fig_displot.update_layout(margin=dict(b=85, t=0, l=0, r=0),
                                title_font_size=11,
                                title_x=0.5,
                                title_xanchor='center',
                                xaxis_title="Days of year",
                                yaxis_title="Burned area",
                                font=dict(
                                    family="Courier New, monospace",
                                    size=14)
        )

    elif displot_option == 'burned_cause':
        fig_displot = px.histogram(filtered_df, x="DISCOVERY_DOY", y="FIRE_SIZE", color="STAT_CAUSE_DESCR",
                                    marginal="box", # or violin, rug
                                    hover_data=filtered_df.columns)
        fig_displot.update_layout(margin=dict(b=85, t=0, l=0, r=0),
                                title_font_size=11,
                                title_x=0.5,
                                title_xanchor='center',
                                xaxis_title="Days of year",
                                yaxis_title="Fire cause",
                                font=dict(
                                    family="Courier New, monospace",
                                    size=14)
        )
    return fig_displot


@app.callback(Output('squares','figure')
                ,
                [Input('year_picker','value'),
                Input('squares_option','value')])

def update_figure(year_picker, squares_option):

    filtered_df = df[(df['FIRE_YEAR'] >= year_picker[0]) & (df['FIRE_YEAR'] <= year_picker[1])]
    df_squares = filtered_df.groupby('STATE', as_index = False)['FIRE_SIZE'].sum()
    df_squares.columns = ['STATE', 'BURNED AREA']
    df_squares1 = filtered_df.groupby('STATE', as_index = False)['FIRE_SIZE'].count()
    df_squares1.columns = ['STATE', 'FIRES']

    if squares_option == 'area_states':
        fig_squares = px.treemap(df_squares, path=['STATE'], values='BURNED AREA',
                                 color='BURNED AREA',
                                 hover_data=['STATE'],
                                 color_continuous_scale='Inferno',
                                 color_continuous_midpoint=np.average(df_squares['BURNED AREA'], weights=df_squares['BURNED AREA']))


    elif squares_option == 'fires_states':
        fig_squares = px.treemap(df_squares1, path=['STATE'], values='FIRES',
                                color='FIRES',
                                hover_data=['STATE'],
                                color_continuous_scale='Inferno',
                                color_continuous_midpoint=np.average(df_squares1['FIRES'], weights=df_squares1['FIRES']))
    return fig_squares

# Layout section: BOOTSTRAP
#-------------------------------------------------------------------------------
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src=("https://i.ibb.co/djgFkPr/logo1.png"),
                        style = {'height':'32px','margin':'2px'},
                        #height="40px",
                        className='float-right'),
                        #width=1
                        xs=3, sm=3, md=2, lg=1, xl=1
                ),
        dbc.Col(html.H2("U.S. WILDFIRES DASHBOARD",
                        className='float-left text-left'),
                #width=9
                xs=7, sm=7, md=12, lg=9, xl=9
                ),
        dbc.Col(html.Div("Credential ID:5ZRTTXB7HFUR",
                        className='float-right text-right'),
                width=2)
    ]),


    dbc.Row([
        dbc.Col(dcc.RangeSlider(id='year_picker',
                        min = 1992,
                        max = 2015,
                        #marks = {i:str(i) for i in range(1992,2016)},
                        marks={
                            1992: '1992',
                            1993: '93',
                            1994: '94',
                            1995: '95',
                            1996: '96',
                            1997: '97',
                            1998: '98',
                            1999: '99',
                            2000: '00',
                            2001: '01',
                            2002: '02',
                            2003: '03',
                            2004: '04',
                            2005: '05',
                            2006: '06',
                            2007: '07',
                            2008: '08',
                            2009: '09',
                            2010: '10',
                            2011: '11',
                            2012: '12',
                            2013: '13',
                            2014: '14',
                            2015: '2015'
                            },
                        value = [2007,2010],
                        className='py-2'
                        ),
                #width=6
                xs=12, sm=12, md=12, lg=6, xl=6
            )#,

                #dbc.Col([
                    #html.Div(
                        #html.P(children='IMPACT ON MAIN AGENCIES INVOLVED'),
                                #style = {'height':'50px','margin':'1px'},
                                #className='text-center font-weight-bolder'
                    #)
                #],
                #width=6
                #xs=12, sm=12, md=12, lg=6, xl=6
                #)

    ]),

    dbc.Row([
        dbc.Col([
            html.Div(
                dcc.Dropdown(id='map_type', value='fire_all',
                                #labelClassName='mr-3 text-dark',
                                className='text-center',
                                options=[
                                    {'label':'Total number of fires and burned area', 'value':'fire_all'},
                                    {'label':'Fires density by fire size', 'value':'fire_den'},
                                    {'label':'Burned area by Counties', 'value':'burn_counties'},
                                    {'label':'Hexbeam - Average by fires size', 'value':'avg_size'},
                                    {'label':'Hexbeam - Number of fires', 'value':'number_fire'},
                                    {'label':'Hexbeam - Burned area', 'value':'total_area'}
                                    ]
                ),
                className='py-3'
            ),
            html.Div(
                dcc.Graph(id='map'), className='shadow'
                    )

        ],
        #width=6
        xs=12, sm=12, md=12, lg=6, xl=6
        ),

        dbc.Col([
            html.Div(
                html.P(children='Agency'),
                        style = {'height':'50px','margin':'1px'},
                        className='alert-primary text-center font-weight-bolder'
            ),
            html.Div(
                html.Img(src=("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Seal_of_the_United_States_Bureau_of_Indian_Affairs.svg/200px-Seal_of_the_United_States_Bureau_of_Indian_Affairs.svg.png"),
                                height="85px",
                                className="rounded mx-auto d-block py-1",
                                title='Bureau of Indian Affairs'
                )
            ),
            html.Div(
                html.Img(src=("https://foundationforwomenwarriors.org/wp-content/uploads/2018/07/Forest-Service-Logo.png"),
                                height="85px",
                                className="rounded mx-auto d-block py-1",
                                title='United States Forest Service'
                )
            ),
            html.Div(
                html.Img(src=("https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Seal_of_the_United_States_Fish_and_Wildlife_Service.svg/1200px-Seal_of_the_United_States_Fish_and_Wildlife_Service.svg.png"),
                                height="85px",
                                className="rounded mx-auto d-block py-1",
                                title='United States Fish and Wildlife Service'
                )
            ),
            html.Div(
                html.Img(src=("https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Logo_of_the_United_States_National_Park_Service.svg/1200px-Logo_of_the_United_States_National_Park_Service.svg.png"),
                                height="85px",
                                className="rounded mx-auto d-block py-1",
                                title='National Park Service'
                )
            ),
            html.Div(
                html.Img(src=("https://www.goldprospectors.org/Portals/0/EasyDNNnews/759/img-blm-logo.png"),
                                height="85px",
                                className="rounded mx-auto d-block py-1",
                                title='Bureau of Land Management'

                )
            )
        ],
        #width=1
        xs=2, sm=2, md=2, lg=1, xl=1
        ),

        dbc.Col([
            html.Div(
                html.P(children='Number of fires'),
                        style = {'height':'50px','margin':'1px'},
                        className='alert-primary text-center font-weight-bolder'
            ),
            html.Div(
                html.H4(id='BIA_fires'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='FS_fires'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='FWS_fires'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='NPS_fires'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='BLM_fires'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            )
        ],
        #width=1
        xs=2, sm=2, md=2, lg=1, xl=1
        ),

        dbc.Col([
            html.Div(
                html.P(children='Area (million acres)'),
                        style = {'height':'50px','margin':'1px'},
                        className='alert-primary text-center font-weight-bolder'
            ),
            html.Div(
                html.H4(id='BIA_size'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='FS_size'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='FWS_size'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='NPS_size'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='BLM_size'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            )
        ],
        #width=1
        xs=2, sm=2, md=2, lg=1, xl=1
        ),

        dbc.Col([
            html.Div(
                html.P(children='Avg acres by fire'),
                        style = {'height':'50px','margin':'1px'},
                        className='alert-primary text-center font-weight-bolder'
            ),
            html.Div(
                html.H4(id='BIA_ratio'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='FS_ratio'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='FWS_ratio'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='NPS_ratio'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            ),
            html.Div(
                html.H4(id='BLM_ratio'
                ),
                style = {'height':'83px','margin':'1px'},
                className="shadow-sm alert-light card-body text-center"
            )
        ],
        #width=1
        xs=2, sm=2, md=2, lg=1, xl=1
        ),

        dbc.Col([
            html.Div(
                html.P(children='Annual trend'),
                        style = {'height':'50px','margin':'1px'},
                        className='alert-primary text-center font-weight-bolder'
            ),
            html.Div(
                dcc.Graph(id='BIA_graph_fire', config={'displayModeBar': False})
            ),
            html.Div(
                dcc.Graph(id='FS_graph_fire', config={'displayModeBar': False})
            ),
            html.Div(
                dcc.Graph(id='FWS_graph_fire', config={'displayModeBar': False})
            ),
            html.Div(
                dcc.Graph(id='NPS_graph_fire', config={'displayModeBar': False})
            ),
            html.Div(
                dcc.Graph(id='BLM_graph_fire', config={'displayModeBar': False})
            )
        ],
        #width=2
        xs=4, sm=4, md=4, lg=2, xl=2
        )


    ],no_gutters=True),

    dbc.Row([
        dbc.Col([


            html.Div(html.P(children='Number of fires according size & land owner'),className='text-center font-weight-bolder'),
            html.Div(
                dcc.Graph(id='2d_fires_owner')
                    )


        ],
        #width=6
        xs=12, sm=12, md=12, lg=6, xl=6
        ),

        dbc.Col([


            html.Div(html.P(children='Analysis according to the days of year'),className='text-center font-weight-bolder'),
            html.Div(
                dcc.RadioItems(id='displot_option', value='burned_owner', labelClassName='mr-3 text-dark',
                                #labelClassName='mr-3 text-dark',
                                className='text-center',
                                options=[
                                    {'label':'Burned area/owner', 'value':'burned_owner'},
                                    {'label':'Burned area/cause', 'value':'burned_cause'}

                                    ])),
            html.Div(
                dcc.Graph(id='displot')
                    )



        ],
        #width=6
        xs=12, sm=12, md=12, lg=6, xl=6
        )
    ]),

    dbc.Row([
        dbc.Col([
            html.Div(html.P(children='Multiple dynamic distributions'),className='text-center font-weight-bolder'),
            html.Div(dcc.Graph(id='paral'))
        ],
        xs=12, sm=12, md=12, lg=12, xl=12
        )
    ]),

    dbc.Row([
        dbc.Col([
            html.Div(html.P(children='States proportions'),className='text-center font-weight-bolder'),
            html.Div(
                dcc.RadioItems(id='squares_option', value='area_states', labelClassName='mr-3 text-dark',
                                #labelClassName='mr-3 text-dark',
                                className='text-center',
                                options=[
                                    {'label':'Burned area by states', 'value':'area_states'},
                                    {'label':'Number of fires by states', 'value':'fires_states'}

                                    ])),
            html.Div(dcc.Graph(id='squares'))
        ],
        #width=8
        xs=12, sm=12, md=12, lg=8, xl=8
        ),

        dbc.Col([
            html.Div(html.P(children='Analysis of burned area by region & cause of fire'),className='text-center font-weight-bolder'),
            html.Div(dcc.Graph(id='donut'))

        ],
        #width=4
        xs=12, sm=12, md=12, lg=4, xl=4
        ),

    ])


], fluid=True)




if __name__ == '__main__':
    app.run_server(debug=True)
