import os
import dash
from dash import dcc, html
import dash_leaflet as dl
from dash.dependencies import Output, Input
from flask import Flask, send_from_directory
import pandas as pd
import plotly.graph_objects as go
from data import collect_all_ndvi_values, calculate_ndvi_intervals

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TILES_DIR = os.path.join(BASE_DIR, 'tiles/rgb')
CIR_TILES_DIR = os.path.join(BASE_DIR, 'tiles/cir')
TREE_DETECT_DIR = os.path.join(BASE_DIR, 'tiles/Processed_Tiles')
COLLOR_TILES_DIR = os.path.join(BASE_DIR, 'tiles/Collor_Tiles')
DEFAULT_TILE = os.path.join(BASE_DIR, 'tree_pattern.avif')
TC_PORT = 8050
TC_HOST = '0.0.0.0'
colorscale = ['red', 'orange', 'green']

gemeenteCoordinates = pd.DataFrame(pd.read_json(os.path.join(BASE_DIR, 'assets/zipcode-belgium.json')))

server = Flask(__name__)
app = dash.Dash(__name__, server=server)

@server.route('/tiles/rgb/<int:z>/<int:x>/<int:y>.png')
def serve_rgb_tile(z, x, y):
    return serve_tile(z, x, y, TILES_DIR, CIR_TILES_DIR)

@server.route('/tiles/cir/<int:z>/<int:x>/<int:y>.png')
def serve_cir_tile(z, x, y):
    return serve_tile(z, x, y, CIR_TILES_DIR, TILES_DIR)

@server.route('/tiles/Processed_Tiles/<int:z>/<int:x>/<int:y>.png')
def serve_detected_tile(z, x, y):
    return serve_tile(z, x, y, TREE_DETECT_DIR, TILES_DIR)

@server.route('/tiles/Collor_Tiles/<int:z>/<int:x>/<int:y>.png')
def serve_collor_tile(z, x, y):
    return serve_tile(z, x, y, COLLOR_TILES_DIR, CIR_TILES_DIR)

def serve_tile(z, x, y, primary_dir, alternative_dir=None):
    inverted_y = y
    max_y_values = {
        9: 341, 10: 682, 11: 1364, 12: 2729,
        13: 5459, 14: 10918, 15: 21837,
        16: 43674, 17: 87348
    }
    min_y_values = {
        9: 340, 10: 681, 11: 1363, 12: 2726,
        13: 5452, 14: 10905, 15: 21810,
        16: 43620, 17: 87241
    }

    if z in max_y_values:
        max_y = max_y_values[z]
        min_y = min_y_values[z]
        inverted_y = max_y - (y - min_y)

    tile_path = os.path.join(primary_dir, f"{z}/{x}/{inverted_y}.png")
    if os.path.exists(tile_path):
        return send_from_directory(primary_dir, f"{z}/{x}/{inverted_y}.png")

    if alternative_dir:
        tile_path = os.path.join(alternative_dir, f"{z}/{x}/{inverted_y}.png")
        if os.path.exists(tile_path):
            return send_from_directory(alternative_dir, f"{z}/{x}/{inverted_y}.png")

    return send_from_directory(os.path.dirname(DEFAULT_TILE), os.path.basename(DEFAULT_TILE))

app.layout = html.Div(children=[
    dcc.Tabs([
        dcc.Tab(
            label="Map",
            children=[
                dcc.Dropdown(
                    [
                        {'label': f"{row['city']} - {row['zip']}", 'value': row['city']}
                        for _, row in gemeenteCoordinates.iterrows()
                    ],
                    placeholder="Selecteer een gemeente",
                    id="dropdown",
                    style={"margin": "20px 0"},
                ),
                html.Div(
                    children=[
                        dl.Map(
                            [
                                dl.LayersControl(
                                    [
                                        dl.BaseLayer(
                                            dl.TileLayer(
                                                url='http://localhost:8050/tiles/rgb/{z}/{x}/{y}.png',
                                                attribution='RGB Layer'
                                            ),
                                            name='RGB',
                                            checked=True
                                        ),
                                        dl.BaseLayer(
                                            dl.TileLayer(
                                                url='http://localhost:8050/tiles/cir/{z}/{x}/{y}.png',
                                                attribution='CIR Layer'
                                            ),
                                            name='CIR'
                                        ),
                                        dl.BaseLayer(
                                            dl.TileLayer(
                                                url='http://localhost:8050/tiles/Processed_Tiles/{z}/{x}/{y}.png',
                                                attribution='Tree Detection Layer'
                                            ),
                                            name='Tree Detection'
                                        ),
                                        dl.BaseLayer(
                                            dl.TileLayer(
                                                url='http://localhost:8050/tiles/Collor_Tiles/{z}/{x}/{y}.png',
                                                attribution='Collor Tiles Layer'
                                            ),
                                            name='Ongezonde bomen'
                                        ),
                                        dl.Colorbar(
                                            colorscale=colorscale,
                                            width=20,
                                            height=200,
                                            min=0,
                                            max=1,
                                            position="bottomright"
                                        )
                                    ],
                                    id='lc'
                                )
                            ],
                            center=[-51.15, 3.21],
                            zoom=17,
                            style={"width": "100%", "height": "800px"},
                            id="map",
                            bounceAtZoomLimits=True,
                            maxZoom=17,
                            minZoom=9,
                        ),
                        dcc.Graph(
                            id="ndvi-bar-chart",
                            style={"marginTop": "20px", "height": "400px", "display": "none"}
                        ),
                    ]
                )
            ]
        ),

        dcc.Tab(label="Data", children=[
            html.Div(children=[
                dcc.Loading(
                    id="loading-indicator",
                    type="circle",
                    children=[dcc.Graph(id='random-bar-chart')]
                )
            ], style={"height": "300px", "width": "100%"})
        ])
    ]), 

        html.Div(children=[
        html.Img(
            src='/assets/ndvi.webp',
            style={
                "width": "800px",
                "height": "auto",
                "marginTop": "180px",
                "display": "block",
                "marginLeft": "auto",
                "marginRight": "auto",
            }
        ),
        html.P(
            children=[
                "More information about ",
                html.A("NDVI", href="https://www.cropin.com/blogs/ndvi-normalized-difference-vegetation-index", target="_blank")
            ],
            style={
                "textAlign": "center",
                "marginTop": "10px",
                "fontSize": "16px",
            }
        )
    ]),
    
    html.Div(children=[
        html.Div(id="label")
    ], className="info")
], style={"display": "grid", "width": "100%", "height": "100vh"})


@app.callback(Output("label", "children"), [Input("map", 'click_lat_lng')])
def update_label(click_lat_lng):
    if not click_lat_lng:
        return "-"
    return "{:.3f} {}".format(0.0, "units")

@app.callback(
    Output("map", "viewport"),
    Input("dropdown", "value"),
    prevent_initial_call=True
)
def update_map(selected_city):
    city_row = gemeenteCoordinates[gemeenteCoordinates['city'] == selected_city]
    lat, lng = city_row['lat'].values[0], city_row['lng'].values[0]

    return dict(center=(lat-102.351,lng), zoom=15, transition="flyTo")

@app.callback(
    Output("map", "zoom"),
    Input("lc", "activeBaseLayer"),
    prevent_initial_call=True
)
def update_zoom_level(active_layer):
    if active_layer == 'Tree Detection':    
        return 17
    else:
        return 15

@app.callback(
    Output('random-bar-chart', 'figure'),
    Input('dropdown', 'value')
)

def update_random_bar_chart(selected_city):
    geojson_base_folder = './Own_Tiles/'
    all_ndvi_values = collect_all_ndvi_values(geojson_base_folder)

    ndvi_percentages = calculate_ndvi_intervals(all_ndvi_values)

    ndvi_intervals = list(ndvi_percentages.keys())
    ndvi_values = list(ndvi_percentages.values())

    interval_values = [(i/10, (i+1)/10) for i in range(10)]

    mean_ndvi_per_interval = []
    for i in range(10):
        interval_start, interval_end = interval_values[i]
        interval_ndvi_values = [ndvi for ndvi in all_ndvi_values if interval_start <= ndvi < interval_end]
        if interval_ndvi_values:
            mean_ndvi_per_interval.append(sum(interval_ndvi_values) / len(interval_ndvi_values))
        else:
            mean_ndvi_per_interval.append(0)

    colorscale = 'RdYlGn'

    min_value = min(mean_ndvi_per_interval)
    max_value = max(mean_ndvi_per_interval)

    normalized_values = [(value - min_value) / (max_value - min_value) for value in mean_ndvi_per_interval]

    fig = go.Figure(
        data=[go.Bar(
            x=ndvi_intervals,
            y=ndvi_values,
            name='NDVI Percentages',
            marker=dict(
                color=normalized_values,
                colorscale=colorscale,
                cmin=0,
                cmax=1,
                colorbar=dict(
                    title="NDVI Value",
                    tickvals=[0, 0.5, 1],
                    ticktext=["0 (Rood)", "0.5 (Geel)", "1 (Groen)"],
                ),
                showscale=True
            )
        )],
        layout = go.Layout(
            title={
                "text": "Normalized Difference Vegetation Index Percentage per Interval",
                "x": 0.5,
                "font": {
                    "size": 24, 
                },
            },
            xaxis=dict(title="NDVI Interval"),
            yaxis=dict(title="Percentage (%)"),
        )
    )

    return fig

if __name__ == '__main__':
    app.run_server(port=TC_PORT, host=TC_HOST)