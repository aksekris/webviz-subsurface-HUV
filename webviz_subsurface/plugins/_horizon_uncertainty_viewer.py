from uuid import uuid4
from pathlib import Path
from typing import List
import dash
import pandas as pd
import numpy as np
from operator import add
from operator import sub
import plotly.graph_objects as go
from matplotlib.colors import ListedColormap
import xtgeo
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import webviz_core_components as wcc
from webviz_subsurface_components import LayeredMap
from webviz_config import WebvizPluginABC
from webviz_config.webviz_store import webvizstore
from webviz_config.utils import calculate_slider_step

from .._datainput.well import load_well
from .._datainput.surface import make_surface_layer, get_surface_fence


class HorizonUncertaintyViewer(WebvizPluginABC):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    """

This plugin visualizes surfaces in a map view and seismic in a cross section view.
The cross section is defined by a polyline interactively edited in the map view.

* `surfacefiles`: List of file paths to Irap Binary surfaces
* `surfacenames`: Corresponding list of displayed surface names
* `zunit`: z-unit for display
* `colors`: List of colors to use
"""

    ### Initialize ###
    def __init__(
        self,
        app,
        surfacefiles: List[Path],
        surfacefiles_de: List[Path],
        wellfiles: List[Path],
        surfacenames: list = None,
        wellnames: list = None,
        zunit="depth (m)",
    ):

        super().__init__()
        self.zunit = zunit
        self.surfacefiles = [str(surffile) for surffile in surfacefiles]
        self.surfacefiles_de = [str(surfacefile_de) for surfacefile_de in surfacefiles_de]
        if surfacenames is not None:
            if len(surfacenames) != len(surfacefiles):
                raise ValueError(
                    "List of surface names specified should be same length as list of surfacefiles"
                )
            self.surfacenames = surfacenames
        else:
            self.surfacenames = [Path(surfacefile).stem for surfacefile in surfacefiles]
        
        self.wellfiles = [str(wellfile) for wellfile in wellfiles]
        if wellnames is not None:
            if len(wellnames) != len(wellfiles):
                raise ValueError(
                    "List of surface names specified should be same length as list of surfacefiles"
                )
            self.wellnames = wellnames
        else:
            self.wellnames = [Path(wellfile).stem for wellfile in wellfiles]
        self.plotly_theme = app.webviz_settings["theme"].plotly_theme
        self.uid = uuid4()
        self.set_callbacks(app)

    ### Generate unique ID's ###
    def ids(self, element):
        return f"{element}-id-{self.uid}"

    ### Layout map section ###
    @property
    def map_layout(self):
        return None

    ### Layout cross section ###
    @property
    def cross_section_layout(self):
        return html.Div(
            children=[
                wcc.FlexBox(
                    children=[
                        html.Div(
                            children=[
                                html.Label(
                                    style={
                                        "font-weight": "bold",
                                        "textAlign": "center",
                                    },
                                    children="Select well",
                                ),
                                dcc.Dropdown(
                                    id=self.ids("well-dropdown"),
                                    options=[
                                        {"label": name, "value": path}
                                        for name, path in zip(
                                            self.wellnames, self.wellfiles
                                        )
                                    ],
                                    value=self.wellfiles[0],
                                    clearable=False,
                                ),
                            ]
                        ),
                    ],
                ),
                wcc.FlexBox(
                    children=[
                        html.Div(
                            children=[
                                html.Label(
                                    style={
                                        "font-weight": "bold",
                                        "textAlign": "Left",
                                    },
                                    children="Select Surfaces",
                                ),
                                dcc.Checklist(
                                    id=self.ids('all-surfaces-checkbox'),
                                    options=[{'label': 'all', 'value': 'True'}],
                                    value=['True'],
                                ),
                                dcc.Checklist(
                                    id=self.ids('surfaces-checklist'),
                                    options=[
                                        {"label": name, "value": path}
                                        for name, path in zip(
                                            self.surfacenames, self.surfacefiles
                                        )
                                    ],
                                    value=self.surfacefiles,
                                ),
                                dcc.Checklist(
                                    id=self.ids('surfaces_de_checklist'),
                                    options=[
                                        {"label": name+'_error', "value": path}
                                        for name, path in zip(
                                            self.surfacenames, self.surfacefiles_de
                                        )
                                    ],
                                    value=self.surfacefiles_de,
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(
                            style={
                                "marginTop": "20px",
                                "height": "800px",
                                "zIndex": -9999,
                            },
                            children=wcc.Graph(
                                figure={"displayModeBar": True}, id=self.ids("cross-section-view")
                            ),
                        )
                    ]
                ),
            ]
        )

    ### Flexbox ###
    @property
    def layout(self):
        return wcc.FlexBox(
            id=self.ids("layout"),
            children=[
                html.Div(style={"flex": 1}, children=self.map_layout),
                html.Div(style={"flex": 1}, children=self.cross_section_layout),
            ],
        )

    ### Callbacks cross-section-view ###
    def set_callbacks(self, app):
        @app.callback(
            Output(self.ids("cross-section-view"), "figure"),
            [
                Input(self.ids("well-dropdown"), "value"), #wellpath
                Input(self.ids("surfaces-checklist"), "value"), #surfacepaths list
                Input(self.ids("surfaces_de_checklist"), "value"), #surfacepaths_de list
            ],
        )
        def _render_surface(wellpath, surfacepaths, surfacepaths_de):
            list_length = len(surfacepaths)
            well = xtgeo.Well(get_path(wellpath))
            well_df = well.dataframe
            well_fence = well.get_fence_polyline(nextend=100, sampling=5) # Generate a polyline along a well path
            well.create_relative_hlen() # Get surface values along the polyline
            
            surfaces = []
            surfaces_lines = []
            surfaces_lines_xdata = []
            surfaces_lines_ydata = []

            for idx, path in enumerate(surfacepaths): # surface
                surfaces.append(xtgeo.surface_from_file(path, fformat="irap_binary")) #list of surfaces
                surfaces_lines.append(surfaces[idx].get_randomline(well_fence)) # cross section x and y coordinates
                surfaces_lines_xdata.append(surfaces_lines[idx][:,0]) # x coordinates lines from surface
                surfaces_lines_ydata.append(surfaces_lines[idx][:,1]) # y coordinates lines from surface

            surfaces_de = []
            surfaces_lines_de = []
            surfaces_lines_de_xdata = []
            surfaces_lines_de_ydata = []
            surfaces_lines_de_add_ydata = []
            surfaces_lines_de_sub_ydata = []

            for idx, path in enumerate(surfacepaths_de): # surface with depth error
                surfaces_de.append(xtgeo.surface_from_file(path, fformat="irap_binary")) #list of surfaces
                surfaces_lines_de.append(surfaces_de[idx].get_randomline(well_fence)) # cross section x and y coordinates
                surfaces_lines_de_xdata.append(surfaces_lines_de[idx][:,0]) # x coordinates lines from surface
                surfaces_lines_de_ydata.append(surfaces_lines_de[idx][:,1]) # y coordinates lines from surface
                surfaces_lines_de_add_ydata.append(list(map(add, surfaces_lines_ydata[idx], surfaces_lines_de_ydata[idx]))) #add error y data
                surfaces_lines_de_sub_ydata.append(list(map(sub, surfaces_lines_ydata[idx], surfaces_lines_de_ydata[idx]))) #sub error y data

            return make_gofig(well_df, surfaces_lines, surfaces_lines_de_add_ydata, surfaces_lines_de_sub_ydata, surfaces_lines_xdata, surfaces_lines_de_xdata)

        ### Update of tickboxes when selectin "all" surfaces in cross-section-view
        @app.callback(
            Output(self.ids("surfaces-checklist"), "value"),
            [Input(self.ids("all-surfaces-checkbox"), "value")],
        )
        def update_surface_tickboxes(all_surfaces_checkbox):
            return self.surfacefiles if all_surfaces_checkbox == ['True'] else []

    def add_webvizstore(self):
        return [(get_path, [{"path": fn}]) for fn in self.surfacefiles]

@webvizstore
def get_path(path) -> Path:
    return Path(path)

def make_gofig(well_df, surfaces_lines, surfaces_lines_de_add_ydata, surfaces_lines_de_sub_ydata, surfaces_lines_xdata, surfaces_lines_de_xdata):
    max_depth = max_depth_of_surflines(surfaces_lines)
    min_depth = min_depth_of_surflines(surfaces_lines)
    x_well,y_well,xmax = find_where_it_crosses_well(min_depth,max_depth,well_df)
    y_width = np.abs(max_depth-y_well)
    x_width = np.abs(xmax-x_well)
    layout = {}
    layout.update(
        {          
            "yaxis": {
                "title": "Depth (m)",
                "autorange": "off",
                "range" : [max_depth,y_well-0.15*y_width]
            },
            "xaxis": {
                "title": "Distance from polyline",
                "range": [x_well-x_width,xmax+x_width],
            },
            "plot_bgcolor":'rgb(233,233,233)'
        }
    )
    data_surfaces = [{
                "type": "line",
                "y": surface_line[:,1],
                "x": surface_line[:,0],
                "name": "surface",
                "fill":"tonexty"} 
            for surface_line in surfaces_lines]
    
    data_surfaces_de_add = [{
                "type": "line",
                "y": ydata,
                "x": surfaces_lines_de_xdata[idx],
                "name": "error_add",
                "line":{"color":"black"},
            } for idx, ydata in enumerate(surfaces_lines_de_add_ydata)
            ]
    data_surfaces_de_sub = [{
                "type": "line",
                "y": ydata,
                "x": surfaces_lines_de_xdata[idx],
                "name": "error_sub",
                "line":{"color":"gray"},
            } for idx, ydata in enumerate(surfaces_lines_de_sub_ydata)
            ]
    data_surfaces.append({
                "type": "line",
                "x": [surfaces_lines[0][0, 0], surfaces_lines[0][np.shape(surfaces_lines[0])[0] - 1, 0]],
                "y": [max_depth+50, max_depth+50],
                "fill": "tonexty",
                "line":{"color":"black"}
                })     
    data_surfaces.append({
                "type": "line",
                "y": well_df["Z_TVDSS"],
                "x": well_df["R_HLEN"],
                "name": "well"
                })
    
    return {'data':data_surfaces + data_surfaces_de_add + data_surfaces_de_sub,
            'layout':layout}

def max_depth_of_surflines(surfaces_lines):
    """
    Find the maximum depth of layers along a cross section
    :param surfaces_lines: surface cross section lines
    :return: max depth
    """
    maxvalues = np.array([
        np.max(sl[:,1]) for sl in surfaces_lines
    ])
    return np.max(maxvalues)

def min_depth_of_surflines(surfaces_lines):
    """
    Find the miniimum depth of layers along a cross section
    :param surfaces_lines: surface cross section lines
    :return: min depth
    """
    minvalues = np.array([
        np.min(sl[:,1]) for sl in surfaces_lines
    ])
    return np.min(minvalues)

def find_where_it_crosses_well(ymin,ymax,df):
    y_well = df["Z_TVDSS"]
    x_well = df["R_HLEN"]
    x_well_max = np.max(x_well)
    X_point_y = 0
    X_point_x = 0
    for i in range(len(y_well)):
        if y_well[i] >= ymin:
            X_point_y = y_well[i]
            X_point_x = x_well[i]
            break
    return X_point_x, X_point_y, x_well_max