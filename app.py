import dash
from dash import dcc
from dash import html
import dash_daq as daq

import plotly.express as px
import pandas as pd
import numpy as np
import re, collections

from dash.dependencies import Input, Output
from plotly import graph_objs as go
from plotly.graph_objs import *
import pytz
import json
import time
import os, sys
from backend import backend

external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    {
        'href': 'http://fonts.googleapis.com/css?family=Titillium+Web',
        'rel': 'stylesheet',
        'type': 'text/css',
    }
]
bk = None

app = dash.Dash(__name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=external_stylesheets)
mapbox_access_token = "pk.eyJ1IjoibW9ycGhldXMyNyIsImEiOiJja2Zrd3J0dWMwb2pxMnlwY3g0Zmtza3ZuIn0.obFXuRnZeFgcHdzxq-Co4g"

bk = backend()
all_station_list = bk.get_all_station_list()
server = app.server

def getStationHoverInfo(stationlist):
    station_hover_info = []
    for info in stationlist:
        sno = info['sno']
        sna = info['sna']
        tot = info['tot']
        sbi = info['sbi']
        bemp = info['bemp']
        str_station = '[{sno}] {sna}<br> bike:{sbi}<br> empty:{bemp}<br> total:{tot}'.format(sno=sno,sna=sna,sbi=sbi,bemp=bemp,tot=tot)
        station_hover_info = station_hover_info + [str_station]
    return station_hover_info

# ------------------ layout ------------------
def value_block(title, value, blk_id, wper):
    block_obj = html.Div(
        className = 'div-value-block',
        style={'float':'left', 'width': wper},
        children = [
            html.P(title, style={'text-align':'left','font-size':'18px','font-weight':'bold'}),
            html.P(value, style={'text-align':'center','font-size':'30px','font-weight':'bold'}, id=blk_id)
        ]
    )
    return block_obj

def weather_value_block(title, value, blk_id, wper):
    block_obj = html.Div(
        className = 'weather-div-value-block',
        style={'float':'left', 'width': wper},
        children = [
            html.P(title, style={'text-align':'center','font-size':'18px','font-weight':'bold'}),
            html.P(value, style={'text-align':'center','font-size':'20px','font-weight':'bold'}, id=blk_id)
        ]
    )
    return block_obj

font_link = html.Link(
    href = 'http://fonts.googleapis.com/css?family=Yanone+Kaffeesatz'
)

hist_div = html.Div(
    className = "hist-div",
    children=[
        dcc.Slider(
            id='hour-slider',
            min=-24,
            max=1,
            step=1,
            value=1,
            updatemode='drag',
            tooltip={"placement": "bottom", "always_visible": False},
        ),
        dcc.Graph(
            id='histogram',
        ),
    ]
)

graph_div = html.Div(
    className = "graph-div",
    children=[
        dcc.Graph(
            id='map-graph',
        ),
        hist_div
    ]
)

user_control_div = html.Div (
        className = "div-user-control",
        children=[
            html.Img(src=app.get_asset_url('search.png'),width="30", height="30"),
            dcc.Dropdown(
                id="location-dropdown",
                options=[ {"value": s['sno'] , "label": "[{sno}] {name}".format(sno=s['sno'] ,name = s['sna'])} for s in all_station_list],
                placeholder="Select a location",
                style={'min-width':'250px','font-size':'15px','border-radius':'15px','board-width':'0px','margin-left':'2%'},
            ),
        ],
)

search_result = html.Div(
    className = 'search-result-div',
    children=[
        value_block('Bike','--','pred_bike_value',"40%"),
        value_block('Empty ','--', 'pred_empty_value',"40%"),
        dcc.Store(id='intermediate-value'),
        dcc.Store(id='intermediate-value_hr'),
        dcc.ConfirmDialog(
        id='confirm-danger',
        message='prediction for this station is not support now!',
    ),
    ]
)

current_status_div = html.Div(
    className = 'current-station-div',
    children = [
        html.P("No.",id='station-no'),
        html.H2("Station Name",id='station-name'),
        html.P("Station Address",id='station-addr'),
        html.P("Status",id='station-status'),
        html.Div(
            style={'margin-top':'10%'},
            children = [
                value_block("Bike",'--',"station-bike-value",'80px'),
                value_block("Empty",'--',"station-empty-value",'80px') ,
                value_block("Total",'--',"station-total-value","80px")
            ]
        ),
        dcc.Store(id='intermediate_value_station_info'),
        ]
)
from datetime import datetime

date_time_div = html.Div(
    className='date-time-div',
    children = [
        html.Div(id='date-today'),
        html.Div(id='time-today'),
        dcc.Interval(
            id='interval-component-60s',
            interval=60*1000, # in milliseconds
            n_intervals=0
        ),
    ]
)
weather_info_div = html.Div(
    className = 'weather-info-div',
    children=[
        weather_value_block("UVI",'--','uvi_value',"40%"),
        weather_value_block("Rainfall",'--','rain_value',"40%"),
        weather_value_block("Humidity",'--','humidity_value',"40%"),
        weather_value_block("Pressure",'--','pressure_value',"40%"),
        weather_value_block("Wind Dir",'--','wind_dir_value',"40%"),
        weather_value_block("Wind Speed",'--','wind_speed_value',"40%"),
        dcc.Store(id='intermediate_value_weather'),
    ]
)
weather_img_div = html.Div(
    id = 'weather-img-div',
    children=[
        html.Img(src=app.get_asset_url('weather_icon/sun.jpg'),width="100", height="100",style={"margin":"5%", "border-radius": "50%"}),
    ]
)

weather_div = html.Div(
    className='weather-div',
    children = [
        html.P("local weather",id='weather-title',style={'text-align':'left', "margin-top":"5%"}),
        weather_img_div,
        html.Div(id='temp-value',style = {'color': 'white', 'font-size': '35px'}),
        weather_info_div
    ]
)
side_info_div = html.Div(
    className='side-info-div',
    children = [
        date_time_div,
        weather_div
    ]
)

station_info_div = html.Div(
    className = "station-info-div",
    children=[
        current_status_div,
        html.H3("Prediction for Next Hour",id='next-hour'),
        search_result
    ]
)

header_div = html.Div(
    className = "header-div",
    children=[
        html.H1("Forecasting System for Taipei Youbike",style={'text-align':'center'}),
        user_control_div,
    ]
)

info_div = html.Div(
    className = "info-div",
    children=[
        station_info_div,
        graph_div,
        side_info_div
    ]
)

body_div = html.Div(
    className = "body-div",
    children=[
        header_div,
        info_div,
    ]
)

app.layout = html.Div(
    className = "main-div",
    children=[
        header_div,
        info_div,
    ]
)


@app.callback(
    Output("time-today", "children"),
    Output("date-today", "children"),
    [
        Input("interval-component-60s", 'n_intervals'),
    ],
)
def update_clock(intervals):
    dt_style = {'color':'white', 'size':'30px'}
    dt = datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
    return html.Span(dt.strftime("%H:%M %A"),style=dt_style), html.Span(datetime.today().strftime('%B-%d-%Y'),style=dt_style)



# ------------------ Figure ------------------
totalList = []
def get_selection(month, day, selection):
    xVal = []
    yVal = []
    xSelected = []
    colorVal = [
        "#F4EC15",
        "#DAF017",
        "#BBEC19",
        "#9DE81B",
        "#80E41D",
        "#66E01F",
        "#4CDC20",
        "#34D822",
        "#24D249",
        "#25D042",
        "#26CC58",
        "#28C86D",
        "#29C481",
        "#2AC093",
        "#2BBCA4",
        "#2BB5B8",
        "#2C99B4",
        "#2D7EB0",
        "#2D65AC",
        "#2E4EA4",
        "#2E38A4",
        "#3B2FA0",
        "#4E2F9C",
        "#603099",
    ]

    # Put selected times into a list of numbers xSelected
    xSelected.extend([int(x) for x in selection])

    for i in range(24):
        # If bar is selected then color it white
        if i in xSelected and len(xSelected) < 24:
            colorVal[i] = "#FFFFFF"
        xVal.append(i)
        # Get the number of rides at a particular time
        yVal.append(len(totalList[month][day][totalList[month][day].index.hour == i]))

    return [np.array(xVal), np.array(yVal), np.array(colorVal)]


@app.callback(
    Output("histogram", "figure"),
    [
        Input("location-dropdown", "value"),
        Input('hour-slider', 'value'),
        Input('intermediate-value', 'data'),
        Input('intermediate-value_hr', 'data')
    ],
)
def update_histogram(selectedLocation, hr_slider, sbi_series, cur_hr):

    idx = np.array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])
    if selectedLocation != None and sbi_series:
        dt = datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
        a_list = collections.deque(idx)
        a_list.rotate(22)
        h_df = sbi_series[(24+hr_slider) : (48+hr_slider)]
        xVal = np.array(list(a_list))
        yVal = np.array(list(h_df))

    else:
        xVal = np.array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])
        yVal = np.zeros(24)

    if len(yVal) == 0:
        yVal = np.zeros(24)

    colorVal = [
        "#F4EC15",
        "#DAF017",
        "#BBEC19",
        "#9DE81B",
        "#80E41D",
        "#66E01F",
        "#4CDC20",
        "#34D822",
        "#24D249",
        "#25D042",
        "#26CC58",
        "#28C86D",
        "#29C481",
        "#2AC093",
        "#2BBCA4",
        "#2BB5B8",
        "#2C99B4",
        "#2D7EB0",
        "#2D65AC",
        "#2E4EA4",
        "#2E38A4",
        "#3B2FA0",
        "#4E2F9C",
        "#603099",
    ]
    #print("->>>>>>",hr_slider, isinstance(pred_sbi, int))
    if hr_slider == 1:
        colorVal[23] = '#E06CC1'


    layout = go.Layout(
        bargap=0.01,
        bargroupgap=0,
        barmode="group",
        height=250,
        margin=go.layout.Margin(l=10, r=0, t=0, b=50),
        showlegend=False,
        plot_bgcolor="#0A1612",
        paper_bgcolor="#0A1612",
        dragmode="select",
        font=dict(color="white"),

        xaxis=dict(
            range=[-0.5, 23.5],
            showgrid=False,
            nticks=25,
            fixedrange=True,
            ticksuffix=":00",
            type='category'
        ),

        yaxis=dict(
            range=[0, max(yVal) + max(yVal) / 4],
            showticklabels=False,
            showgrid=False,
            fixedrange=True,
            rangemode="nonnegative",
            zeroline=False,
        ),

        annotations=[
            dict(
                x=xi,
                y=yi,
                text=str(yi),
                xanchor="center",
                yanchor="bottom",
                showarrow=False,
                font=dict(color="white"),
            )
            for xi, yi in zip(idx, yVal)
        ],
    )

    fig = go.Figure(
        data=[
            go.Bar(x=xVal, y=yVal, marker=dict(color=colorVal), hoverinfo="x"),
            go.Scatter(
                opacity=0,
                x=xVal,
                y=yVal / 2,
                hoverinfo="none",
                mode="markers",
                marker=dict(color="rgb(66, 134, 244, 0)", symbol="square", size=40),
                visible=True,
            ),
        ],
        layout=layout,
    )
    return fig


# parameters for Figure 2
title = 'Select behavior'
labels = ['Empty Truth', 'Bike Truth', 'Empty Prediction', 'Bike Prediction']
colors = ['rgb(67,67,67)', 'rgb(115,115,115)', 'rgb(49,130,189)', 'rgb(189,189,189)']
mode_size = [8, 8, 8, 8]
line_size = [2, 2, 2, 2]
x_data = np.vstack((np.arange(0, 24),)*4)

@app.callback(
    Output("location-dropdown", "value"),
    [
        Input('map-graph', 'clickData'),
    ],
)
def update_current_station(click_data):
    sno = None
    if click_data != None:
        sno = re.findall('\d+', click_data['points'][0]['text'])
        sno = str(sno[0]).zfill(4)
    return sno


@app.callback(
    Output("station-empty-value", "children"),
    Output("station-bike-value", "children"),
    Output("station-total-value", "children"),
    Output("station-no", "children"),
    Output("station-name", "children"),
    Output("station-addr", "children"),
    Output("station-status", "children"),
    Output("intermediate_value_station_info", "data"),
    Output("map-graph", "figure"),
    [
        Input("location-dropdown", "value"),
        Input("map-graph", "figure"),
    ],
)
def update_station_status(selectedLocation, map_graph):
    zoom = 12.0
    latInitial = 25.0408578889
    lonInitial = 121.567904444
    bearing = 0

    #reset all variables
    total_num = '--'
    bike_num = '--'
    empty_num = '--'
    pred_sbi = '--'
    pred_bemp = '--'

    station_no = "No. "
    station_name = "Station Name"
    station_addr = "Address"
    station_status = "Status: Unknown"
    station_info = None

    #fig 2
    graph_data = pd.DataFrame(range(0,24),index=pd.date_range("2018-03-01", periods=24, freq="H"))
    y_data = []

    for i in range(0,4):
        y_data = y_data + [graph_data]
    start_time = time.time()
    station_list = bk.get_all_station_list()
    all_station_list = station_list
    hover_info_txt = getStationHoverInfo(station_list)
    print('get all station time:',time.time() - start_time)
    start_time = time.time()
    if selectedLocation and station_list:
        zoom = 15.0
        station_info = bk.get_station_info(selectedLocation)
        latInitial = station_info['lat']
        lonInitial = station_info['lng']
        total_num = station_info['tot']
        bike_num = station_info['sbi']
        empty_num = station_info['bemp']
        station_no = station_no + str(station_info['sno'])
        station_name = station_info['sna']
        station_addr =  station_info['ar']
        print('get_station_info time:',time.time() - start_time)
        start_time = time.time()

        if(int(station_info['act']) == 1):
            station_status = "Status: Active"
        else:
            station_status = "Status: Inactive"
            warning_display = True


        print('seleted time:',time.time() - start_time)
        start_time = time.time()

    if True:
        fig = go.Figure(
            data=[
                # Plot of important locations on the map
                Scattermapbox(
                    lat=[float(i['lat']) for i in station_list],
                    lon=[float(i['lng']) for i in station_list],
                    mode="markers",
                    hoverinfo="text",
                    text= hover_info_txt,
                    marker=dict(
                    size=10,
                    color=[(1 - int(i['sbi'])/int(i['tot']))*100  for i in station_list],
                    colorscale='jet',
                    showscale=True
                    ),
                ),
            ],

            layout=Layout(
                autosize=True,
                margin=go.layout.Margin(l=5, r=5, t=5, b=5),
                showlegend=False,
                paper_bgcolor="#0A1612",
                mapbox = dict(
                    accesstoken=mapbox_access_token,
                    center=dict(lat=latInitial, lon=lonInitial),
                    style='mapbox://styles/mapbox/dark-v10',
                    bearing=bearing,
                    zoom=zoom,
                ),
                updatemenus=[
                    dict(
                        buttons=(
                        [
                            dict(
                                args=[
                                    {
                                        "mapbox.zoom": 12,
                                        "mapbox.center.lon": "121.567904444",
                                        "mapbox.center.lat": "25.0408578889",
                                        "mapbox.bearing": 0,
                                        "mapbox.style": "dark",
                                    }
                                ],
                            label="Reset Zoom",
                            method="relayout",
                        )
                        ]
                        ),
                        direction="left",
                        pad={"r": 0, "t": 0, "b": 0, "l": 0},
                        showactive=False,
                        type="buttons",
                        x=0.45,
                        y=0.02,
                        xanchor="left",
                        yanchor="bottom",
                        bgcolor="#0A1612",
                        borderwidth=1,
                        bordercolor="#6d6d6d",
                        font=dict(color="#FFFFFF"),
                    )
                ],
            ),
        )
    print('plot graph time:',time.time() - start_time)
    start_time = time.time()

    return empty_num, bike_num, total_num, station_no, station_name, station_addr, station_status, station_info, fig


@app.callback(
    Output("uvi_value", "children"),
    Output("rain_value", "children"),
    Output("humidity_value", "children"),
    Output("pressure_value", "children"),
    Output("wind_dir_value", "children"),
    Output("wind_speed_value", "children"),
    Output("temp-value", "children"),
    Output("weather-img-div", "children"),
    Output("intermediate_value_weather", "data"),#intermediate_value_weather
    [
        Input("location-dropdown", "value"),
    ],
)
def update_weather(selectedLocation):
    w_uvi = '--'
    w_humd = '--'
    w_pres = '--'
    w_rain = '--'
    w_wdir = '--'
    w_wdse = '--'
    w_temp = '-- °C'
    img_div = html.Img(src=app.get_asset_url('weather_icon/sun.jpg'),width="100", height="100",style={"margin":"5%", "border-radius": "50%"}),
    wdata = None
    if selectedLocation:
        wdata = bk.get_current_weather_from_file(int(selectedLocation))
        if wdata != None:
            w_pres = wdata['PRES']
            w_uvi = wdata['UVI']
            w_humd = wdata['HUMD']
            w_rain = wdata['H_24R']
            w_wdir = wdata['WDIR']
            w_wdse = wdata['WDSE']
            w_temp = html.Span(str(wdata['TEMP'])+ '°C')
            new_path = bk.get_weather_icon_path(wdata['Describe'])
            img_div = html.Img(src=app.get_asset_url(new_path),width="100", height="100",style={"margin":"5%", "border-radius": "50%"}),

    return w_uvi,w_rain,w_humd,w_pres,w_wdir,w_wdse,w_temp,img_div, wdata


@app.callback(
    Output("pred_empty_value", "children"),
    Output("pred_bike_value", "children"),
    Output('intermediate-value', 'data'),
    Output('intermediate-value_hr', 'data'),
    Output('confirm-danger', 'displayed'),
    [
        Input("intermediate_value_station_info", "data"),
        Input("intermediate_value_weather", "data")
    ],
)
def update_prediction(station_info, wdata):

    warning_display = False
    pred_bemp = '--'
    pred_sbi = '--'
    cur_hr = '--'
    sbi_series = None
    sbi_dict = None

    if station_info and wdata:
        try:
            cur_time = datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
            cur_hr = cur_time.hour
            sbi_series = bk.predict_sbi_data(station_info,cur_time, wdata)
            pred_sbi = sbi_series[-1:].values[0]

        except Exception as e:
            print(e)
            pred_sbi = None
            warning_display = True
            cur_hr = None

        if pred_sbi == None:
            print('pred_sbi == None')
            pred_sbi = '--'
            pred_bemp = '--'
            warning_display = True
            cur_hr = None
        else:
            pred_bemp = station_info['tot'] - pred_sbi

    return str(pred_bemp), str(pred_sbi), sbi_series , cur_hr, warning_display


if False:
    #template
    # Update Map Graph based on date-picker, selected data on histogram and location dropdown
    @app.callback(
        Output("station-empty-value", "children"),
        Output("station-bike-value", "children"),
        Output("station-total-value", "children"),
        Output("station-no", "children"),
        Output("station-name", "children"),
        Output("station-addr", "children"),
        Output("station-status", "children"),
        Output("pred_empty_value", "children"),
        Output("pred_bike_value", "children"),
        Output("uvi_value", "children"),
        Output("rain_value", "children"),
        Output("humidity_value", "children"),
        Output("pressure_value", "children"),
        Output("wind_dir_value", "children"),
        Output("wind_speed_value", "children"),
        Output("weather-img-div", "children"),
        Output("temp-value", "children"),
        Output('intermediate-value', 'data'),
        Output('intermediate-value_hr', 'data'),
        Output('confirm-danger', 'displayed'),
        Output("map-graph", "figure"),
        [
            Input("location-dropdown", "value"),
            Input("map-graph", "figure"),
        ],
    )
    def update_graph(selectedLocation, map_graph):

        zoom = 12.0
        latInitial = 25.0408578889
        lonInitial = 121.567904444
        bearing = 0
        warning_display = False

        total_num = '--'
        bike_num = '--'
        empty_num = '--'
        pred_bemp = '--'
        pred_sbi = '--'
        cur_hr = '--'

        w_uvi = '--'
        w_humd = '--'
        w_pres = '--'
        w_rain = '--'
        w_wdir = '--'
        w_wdse = '--'
        w_temp = '-- °C'

        img_div = html.Img(src=app.get_asset_url('weather_icon/sun.jpg'),width="100", height="100",style={"margin":"5%", "border-radius": "50%"}),

        station_no = "No. "
        station_name = "Station Name"
        station_addr = "Address"
        station_status = "Status: Unknown"


        #fig 2
        graph_data = pd.DataFrame(range(0,24),index=pd.date_range("2018-03-01", periods=24, freq="H"))
        y_data = []
        for i in range(0,4):
            y_data = y_data + [graph_data]
        start_time = time.time()
        station_list = bk.get_all_station_list()
        all_station_list = station_list
        hover_info_txt = getStationHoverInfo(station_list)
        print('get all station time:',time.time() - start_time)
        start_time = time.time()

        if selectedLocation:
            zoom = 15.0
            station_info= bk.get_station_info(selectedLocation)
            latInitial = float(station_info['lat'])
            lonInitial = float(station_info['lng'])
            total_num = int(station_info['tot'])
            bike_num = int(station_info['sbi'])
            empty_num = int(station_info['tot']) - int(station_info['sbi'])#int(station_info['bemp'])
            station_no = station_no + station_info['sno']
            station_name = station_info['sna']
            station_addr =  station_info['ar']
            print('get_station_info time:',time.time() - start_time)
            start_time = time.time()
            try:
                cur_time =datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
                cur_hr = cur_time.hour
                pred_sbi = bk.predict_sbi(int(selectedLocation),cur_time)
            except Exception as e:
                print(e)
                pred_sbi = None
                warning_display = True
                cur_hr = None

            if pred_sbi == None:
                pred_sbi = '--'
                pred_bemp = '--'
                warning_display = True
                cur_hr = None
            else:
                pred_bemp = total_num - pred_sbi

            if(int(station_info['act']) == 1):
                station_status = "Status: Active"
            else:
                station_status = "Status: Inactive"
                warning_display = True
                pred_sbi = '--'
                pred_bemp = '--'

            #update weather
            #wdata = bk.get_current_weather(int(selectedLocation))
            wdata = bk.get_current_weather_from_db(int(selectedLocation))

            if wdata != None:
                w_pres = wdata['PRES']
                w_uvi = wdata['UVI']
                w_humd = wdata['HUMD']
                w_rain = wdata['H_24R']
                w_wdir = wdata['WDIR']
                w_wdse = wdata['WDSE']
                w_temp = html.Span(str(wdata['TEMP'])+ '°C')
                new_path = bk.get_weather_icon_path(wdata['Describe'])
                img_div = html.Img(src=app.get_asset_url(new_path),width="100", height="100",style={"margin":"5%", "border-radius": "50%"}),

            print('seleted time:',time.time() - start_time)
            start_time = time.time()
        if True:
            fig = go.Figure(
                data=[
                    # Plot of important locations on the map
                    Scattermapbox(
                        lat=[float(i['lat']) for i in station_list],
                        lon=[float(i['lng']) for i in station_list],
                        mode="markers",
                        hoverinfo="text",
                        text= hover_info_txt,
                        marker=dict(
                        size=10,
                        color=[(1 - int(i['sbi'])/int(i['tot']))*100  for i in station_list],
                        colorscale='jet',
                        showscale=True
                        ),
                    ),
                ],

                layout=Layout(
                    autosize=True,
                    margin=go.layout.Margin(l=5, r=5, t=5, b=5),
                    showlegend=False,
                    paper_bgcolor="#0A1612",
                    mapbox = dict(
                        accesstoken=mapbox_access_token,
                        center=dict(lat=latInitial, lon=lonInitial),
                        style='mapbox://styles/mapbox/dark-v10',
                        bearing=bearing,
                        zoom=zoom,
                    ),
                    updatemenus=[
                        dict(
                            buttons=(
                            [
                                dict(
                                    args=[
                                        {
                                            "mapbox.zoom": 12,
                                            "mapbox.center.lon": "121.567904444",
                                            "mapbox.center.lat": "25.0408578889",
                                            "mapbox.bearing": 0,
                                            "mapbox.style": "dark",
                                        }
                                    ],
                                label="Reset Zoom",
                                method="relayout",
                            )
                            ]
                            ),
                            direction="left",
                            pad={"r": 0, "t": 0, "b": 0, "l": 0},
                            showactive=False,
                            type="buttons",
                            x=0.45,
                            y=0.02,
                            xanchor="left",
                            yanchor="bottom",
                            bgcolor="#0A1612",
                            borderwidth=1,
                            bordercolor="#6d6d6d",
                            font=dict(color="#FFFFFF"),
                        )
                    ],
                ),
            )
        print('plot graph time:',time.time() - start_time)
        start_time = time.time()

        return empty_num, bike_num, total_num, station_no, station_name, station_addr, station_status, pred_bemp, pred_sbi,w_uvi, w_rain, w_humd, w_pres, w_wdir, w_wdse, img_div,w_temp,pred_sbi,cur_hr,warning_display,fig


if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
