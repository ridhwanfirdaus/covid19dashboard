import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import pyrebase
import plotly
import dash_table

# GitHub repos URLs
url_confirmed = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"

url_deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"

url_recovered = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"

# Firebase Database config for number of violations occuring and temperature recorded by visitors
firebaseConfig ={
	#insert number of violation database here 
}
firebaseConfig1 = {
    #insert temperature database credentials here
  };

firebaseviolations = pyrebase.initialize_app(firebaseConfig)
firebasetemperature = pyrebase.initialize_app(firebaseConfig1)
dbtemperature = firebasetemperature.database()
dbviolations = firebaseviolations.database()

def getData():
	Ambient = list()
	Object = list()
	ambientdict = dbtemperature.child('Ambient').get().each()
	objectdict=dbtemperature.child('Object').get().each()
	for i, data in enumerate(ambientdict):
		Ambient.append(ambientdict[i].val())        
    	
	for i, data in enumerate(objectdict):
		Object.append(objectdict[i].val())    	
    
	newdf = pd.DataFrame({'Ambient Temperature':	Ambient,'Object Temperature' : Object})
	newdf['index'] = range(1, len(newdf) + 1)
	return newdf


df = getData()
size = 0
X=list()
X.append(1)
Y=list()
Y.append(1)

# Get the data into the app
confirmed = pd.read_csv(url_confirmed)
deaths = pd.read_csv(url_deaths)
recovered = pd.read_csv(url_recovered)

# Unpivot the data frames
total_confirmed = confirmed.melt(
  id_vars = ["Province/State", "Country/Region", "Lat", "Long"],
  value_vars = confirmed.columns[4:],
  var_name = "date",
  value_name = "confirmed"
)

total_deaths = deaths.melt(
  id_vars = ["Province/State", "Country/Region", "Lat", "Long"],
  value_vars = deaths.columns[4:],
  var_name = "date",
  value_name = "deaths"
)

total_recovered = recovered.melt(
  id_vars = ["Province/State", "Country/Region", "Lat", "Long"],
  value_vars = recovered.columns[4:],
  var_name = "date",
  value_name = "recovered"
)

# Merge data frames
covid_data = total_confirmed.merge(
  right = total_deaths,
  how = "left",
  on = ["Province/State", "Country/Region", "date", "Lat", "Long"]
).merge(
  right = total_recovered,
  how = "left",
  on = ["Province/State", "Country/Region", "date", "Lat", "Long"]
)

# Wrangle data
covid_data["recovered"] = covid_data["recovered"].fillna(0)
covid_data["active"] = covid_data["confirmed"] - covid_data["deaths"] - covid_data["recovered"]
covid_data["date"] = pd.to_datetime(covid_data["date"])

# Daily totals
covid_data_1 = covid_data.groupby(["date"])[["confirmed", "deaths", "recovered", "active"]].sum().reset_index()

# Create dict of list
covid_data_list = covid_data[["Country/Region", "Lat", "Long"]]
dict_of_locations = covid_data_list.set_index("Country/Region")[["Lat", "Long"]].T.to_dict("dict")

# Instanciate the app
app = dash.Dash(__name__, meta_tags = [{"name": "viewport", "content": "width=device-width"}])

# Build the layout
app.layout = html.Div(
	children = [
		# (First row) Header: Logo - Title - Last updated
		html.Div(
			children = [
				# Logo
				html.Div(
					children = [
						html.Img(
							src = app.get_asset_url("utp-logo-1.jpg"),
							id = "corona-image",
							style = {
								"height": "100px",
								"width": "auto",
								"margin-bottom": "25px"
							}
						)
					],
					className = "one-third column"
				),
				html.Div(
					children = [
						# Title and subtitle
						html.Div(
							children = [
								html.H3(
									children = "Covid-19",
									style = {
										"margin-bottom": "0",
										"color": "white"
									}
								),
								html.H5(
									children = "Track Covid-19 cases",
									style = {
										"margin-bottom": "0",
										"color": "white"
									}
								)
							]
						)
					],
					className = "one-half column",
					id = 'title'
				),
				# Last updated
				html.Div(
					children = [
						html.H6(
							children = "Last Updated " + str(covid_data["date"].iloc[-1].strftime("%B %d, %Y")),
							style = {
								"color": "orange"
							}
						)
					],
					className = "one-thid column",
					id = "title1"
				)
			],
			id = "header",
			className = "row flex-display",
			style = {
				"margin-bottom": "25px"
			}
		),
		# (Second row) Cards: Global cases - Global deaths - Global recovered - Global active
		html.Div(
			children = [
				# (Column 1): Global cases
				html.Div(
					children = [
						# Title
						html.H6(
							children = "Global cases",
							style = {
								"textAlign": "center",
								"color": "white"
							}
						),
						# Total value
						html.P(
							children = f"{covid_data_1['confirmed'].iloc[-1]:,.0f}",
							style = {
								"textAlign": "center",
								"color": "orange",
								"fontSize": 40
							}
						),
						# New cases
						html.P(
							children = "new: " +
								f"{covid_data_1['confirmed'].iloc[-1] - covid_data_1['confirmed'].iloc[-2]:,.0f}" +
								" (" +
								f"{round(((covid_data_1['confirmed'].iloc[-1] - covid_data_1['confirmed'].iloc[-2]) / covid_data_1['confirmed'].iloc[-1]) * 100, 2)}" +
								"%)",
							style = {
								"textAlign": "center",
								"color": "orange",
								"fontSize": 15,
								"margin-top": "-18px"
							}
						)
					],
					className = "card_container three columns"
				),
				# (Column 2): Global deaths
				html.Div(
					children = [
						# Title
						html.H6(
							children = "Global deaths",
							style = {
								"textAlign": "center",
								"color": "white"
							}
						),
						# Total value
						html.P(
							children = f"{covid_data_1['deaths'].iloc[-1]:,.0f}",
							style = {
								"textAlign": "center",
								"color": "#dd1e35",
								"fontSize": 40
							}
						),
						# New deaths
						html.P(
							children = "new: " +
								f"{covid_data_1['deaths'].iloc[-1] - covid_data_1['deaths'].iloc[-2]:,.0f}" +
								" (" +
								f"{round(((covid_data_1['deaths'].iloc[-1] - covid_data_1['deaths'].iloc[-2]) / covid_data_1['deaths'].iloc[-1]) * 100, 2)}" +
								"%)",
							style = {
								"textAlign": "center",
								"color": "#dd1e35",
								"fontSize": 15,
								"margin-top": "-18px"
							}
						)
					],
					className = "card_container three columns"
				),
				# (Column 3): Global recovered
				html.Div(
					children = [
						# Title
						html.H6(
							children = "Global recovered",
							style = {
								"textAlign": "center",
								"color": "white"
							}
						),
						# Total recovered
						html.P(
							children = f"{covid_data_1['recovered'].iloc[-1]:,.0f}",
							style = {
								"textAlign": "center",
								"color": "green",
								"fontSize": 40
							}
						),
						# New recovered
						html.P(
							children = "new: " +
								f"{covid_data_1['recovered'].iloc[-1] - covid_data_1['recovered'].iloc[-2]:,.0f}" +
								" (" +
								f"{round(((covid_data_1['recovered'].iloc[-1] - covid_data_1['recovered'].iloc[-2]) / covid_data_1['recovered'].iloc[-1]) * 100, 2)}" +
								"%)",
							style = {
								"textAlign": "center",
								"color": "green",
								"fontSize": 15,
								"margin-top": "-18px"
							}
						)
					],
					className = "card_container three columns"
				),
				# (Column 4): Global active
				html.Div(
					children = [
						# Title
						html.H6(
							children = "Global active",
							style = {
								"textAlign": "center",
								"color": "white"
							}
						),
						# Total v
						html.P(
							children = f"{covid_data_1['active'].iloc[-1]:,.0f}",
							style = {
								"textAlign": "center",
								"color": "#e55467",
								"fontSize": 40
							}
						),
						# New active
						html.P(
							children = "new: " +
								f"{covid_data_1['active'].iloc[-1] - covid_data_1['active'].iloc[-2]:,.0f}" +
								" (" +
								f"{round(((covid_data_1['active'].iloc[-1] - covid_data_1['active'].iloc[-2]) / covid_data_1['active'].iloc[-1]) * 100, 2)}" +
								"%)",
							style = {
								"textAlign": "center",
								"color": "#e55467",
								"fontSize": 15,
								"margin-top": "-18px"
							}
						)
					],
					className = "card_container three columns"
				)
			],
			className = "row flex-display"
		),
		# (Third row): Value boxes - Donut chart - Line & Bars
		html.Div(
			children = [
				# (Column 1) Value boxes
				html.Div(
					children = [
						# (Row 1) Country selector
						html.P(
							children = "Select Country: ",
							className = "fix_label",
							style = {
								"color": "white"
							}
						),
						dcc.Dropdown(
							id = "w_countries",
							multi = False,
							searchable = True,
							value = "Malaysia",
							placeholder = "Select Country",
							options = [{"label": c, "value": c} for c in (covid_data["Country/Region"].unique())],
							className = "dcc_compon"
						),
						# (Row 2) New cases title
						html.P(
							children = "New cases: " + " " + str(covid_data["date"].iloc[-1].strftime("%B %d, %Y")),
							className = "fix_label",
							style = {
								"textAlign": "center",
								"color": "white"
							}
						),
						# (Row 3) New confirmed
						dcc.Graph(
							id = "confirmed",
							config = {
								"displayModeBar": False
							},
							className = "dcc_compo",
							style = {
								"margin-top": "20px"
							}
						),
						# (Row 4) New deaths
						dcc.Graph(
							id = "deaths",
							config = {
								"displayModeBar": False
							},
							className = "dcc_compo",
							style = {
								"margin-top": "20px"
							}
						),
						# (Row 5) New recovered
						dcc.Graph(
							id = "recovered",
							config = {
								"displayModeBar": False
							},
							className = "dcc_compo",
							style = {
								"margin-top": "20px"
							}
						),
						# (Row 6) New active
						dcc.Graph(
							id = "active",
							config = {
								"displayModeBar": False
							},
							className = "dcc_compo",
							style = {
								"margin-top": "20px"
							}
						)
					],
					className = "create_container three columns"
				),
				# (Column 2) Donut chart
				html.Div(
					children = [
						# Donut chart
						dcc.Graph(
							id = "pie_chart",
							config = {
								"displayModeBar": "hover"
							}
						)
					],
					className = "create_container four columns",
					style = {
						"maxWidth": "400px"
					}
				),
				# (Columns 3 & 4) Line and bars plot
				html.Div(
					children = [
						dcc.Graph(
							id = "line_chart",
							config = {
								"displayModeBar": "hover"
							}
						)
					],
					className = "create_container five columns"
				)
			],
			className = "row flex-display"
		),		
		#Fourth Row  Live data 
		html.Div(
			children =[
				html.Div( 
					
					children = [
						
						dcc.Graph(
							id='live-graph',
							animate=True,
							
							
						),
						dcc.Interval(
            				id='graph-update',
            				interval=1*1000
        				),						
					],
					className = "create_container2 twelve columns",
					
				)				
			],
			className = "row flex-display"
		),
		html.Div(
			children =[
				html.Div(
					children = [
						dash_table.DataTable(          
          					id = 'table',  
          					#data = df.to_dict('records'),
          					columns=[{"name": i, "id": i} for i in df.columns],
          					fixed_rows={'headers': True},
         					style_table={'height': '300px', 'overflowY': 'auto'},
							style_cell=dict(textAlign='left'),
							style_header=dict(backgroundColor="paleturquoise"),
							style_data=dict(backgroundColor="lavender")
        				),
						dcc.Interval(id = 'table-update', interval = 1000, ),		
					],
					className='create_container2 twelve columns'
				)				
			],
			className = "row flex-display"	
		),
		# (Fifth-row) Map
		html.Div(
			children = [
				html.Div(
					children = [
						dcc.Graph(
							id = "map_chart",
							config = {
								"displayModeBar": "hover"
							}
						)
					],
					className = "create_container1 twelve columns"
				)
			],
			className = "row flex-display"
		),
	],
	id = "mainContainer",
	style = {
		"display": "flex",
		"flex-direction": "column"
	}
)

# Build the callbacks

# New confirmed cases value box
@app.callback(
	Output(
		component_id = "confirmed",
		component_property = "figure"
	),
	Input(
		component_id = "w_countries",
		component_property = "value"
	)
)
def update_confirmed(w_countries):
	# Filter the data
	covid_data_2 = covid_data.groupby(["date", "Country/Region"])[["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
	# Calculate values
	value_confirmed = covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-1] - \
										covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-2]
	delta_confirmed = covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-1] - \
									  covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-3]
	# Build the figure
	fig = {
		"data": [
			go.Indicator(
				mode = "number+delta",
				value = value_confirmed,
				delta = {
					"reference": delta_confirmed,
					"position": "right",
					"valueformat": ",g",
					"relative": False,
					"font": {
						"size": 15
					}
				},
				number = {
					"valueformat": ",",
					"font": {
						"size": 20
					}
				},
				domain = {
					"y": [0, 1],
					"x": [0, 1]
				}
			)
		],
		"layout": go.Layout(
			title = {
				"text": "New confirmed",
				"y": 1,
				"x": 0.5,
				"xanchor": "center",
				"yanchor": "top"
			},
			font = {
				"color": "orange"
			},
			paper_bgcolor = "#1f2c56",
			plot_bgcolor = "#1f2c56",
			height = 50
		)
	}
	# Return the figure
	return fig

# Deaths value box
@app.callback(
	Output(
		component_id = "deaths",
		component_property = "figure"
	),
	Input(
		component_id = "w_countries",
		component_property = "value"
	)
)
def update_deaths(w_countries):
	# Filter the data
	covid_data_2 = covid_data.groupby(["date", "Country/Region"])[["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
	# Calculate values
	value_deaths = covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-1] - \
										covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-2]
	delta_deaths = covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-1] - \
									  covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-3]
	# Build the figure
	fig = {
		"data": [
			go.Indicator(
				mode = "number+delta",
				value = value_deaths,
				delta = {
					"reference": delta_deaths,
					"position": "right",
					"valueformat": ",g",
					"relative": False,
					"font": {
						"size": 15
					}
				},
				number = {
					"valueformat": ",",
					"font": {
						"size": 20
					}
				},
				domain = {
					"y": [0, 1],
					"x": [0, 1]
				}
			)
		],
		"layout": go.Layout(
			title = {
				"text": "New deaths",
				"y": 1,
				"x": 0.5,
				"xanchor": "center",
				"yanchor": "top"
			},
			font = {
				"color": "#dd1e35"
			},
			paper_bgcolor = "#1f2c56",
			plot_bgcolor = "#1f2c56",
			height = 50
		)
	}
	# Return the figure
	return fig


# Recovered value box
@app.callback(
	Output(
		component_id = "recovered",
		component_property = "figure"
	),
	Input(
		component_id = "w_countries",
		component_property = "value"
	)
)
def update_recovered(w_countries):
	# Filter the data
	covid_data_2 = covid_data.groupby(["date", "Country/Region"])[["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
	# Calculate values
	value_recovered = covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-1] - \
										covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-2]
	delta_recovered = covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-1] - \
									  covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-3]
	# Build the figure
	fig = {
		"data": [
			go.Indicator(
				mode = "number+delta",
				value = value_recovered,
				delta = {
					"reference": delta_recovered,
					"position": "right",
					"valueformat": ",g",
					"relative": False,
					"font": {
						"size": 15
					}
				},
				number = {
					"valueformat": ",",
					"font": {
						"size": 20
					}
				},
				domain = {
					"y": [0, 1],
					"x": [0, 1]
				}
			)
		],
		"layout": go.Layout(
			title = {
				"text": "New recovered",
				"y": 1,
				"x": 0.5,
				"xanchor": "center",
				"yanchor": "top"
			},
			font = {
				"color": "green"
			},
			paper_bgcolor = "#1f2c56",
			plot_bgcolor = "#1f2c56",
			height = 50
		)
	}
	# Return the figure
	return fig


# Recovered value box
@app.callback(
	Output(
		component_id = "active",
		component_property = "figure"
	),
	Input(
		component_id = "w_countries",
		component_property = "value"
	)
)
def update_active(w_countries):
	# Filter the data
	covid_data_2 = covid_data.groupby(["date", "Country/Region"])[["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
	# Calculate values
	value_active = covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-1] - \
								 covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-2]
	delta_active = covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-1] - \
								 covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-3]
	# Build the figure
	fig = {
		"data": [
			go.Indicator(
				mode = "number+delta",
				value = value_active,
				delta = {
					"reference": delta_active,
					"position": "right",
					"valueformat": ",g",
					"relative": False,
					"font": {
						"size": 15
					}
				},
				number = {
					"valueformat": ",",
					"font": {
						"size": 20
					}
				},
				domain = {
					"y": [0, 1],
					"x": [0, 1]
				}
			)
		],
		"layout": go.Layout(
			title = {
				"text": "New active",
				"y": 1,
				"x": 0.5,
				"xanchor": "center",
				"yanchor": "top"
			},
			font = {
				"color": "#e55467"
			},
			paper_bgcolor = "#1f2c56",
			plot_bgcolor = "#1f2c56",
			height = 50
		)
	}
	# Return the figure
	return fig

# Donut chart
@app.callback(
	Output(
		component_id = "pie_chart",
		component_property = "figure"
	),
	Input(
		component_id = "w_countries",
		component_property = "value"
	)
)
def update_pie_chart(w_countries):
	# Filter the data
	covid_data_2 = covid_data.groupby(["date", "Country/Region"])[["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
	# Calculate values
	confirmed_value = covid_data_2[covid_data_2["Country/Region"] == w_countries]["confirmed"].iloc[-1]
	deaths_value = covid_data_2[covid_data_2["Country/Region"] == w_countries]["deaths"].iloc[-1]
	recovered_value = covid_data_2[covid_data_2["Country/Region"] == w_countries]["recovered"].iloc[-1]
	active_value = covid_data_2[covid_data_2["Country/Region"] == w_countries]["active"].iloc[-1]
	# List of colors
	colors = ["orange", "#dd1e35", "green", "#e55467"]
	# Build the figure
	fig = {
		"data": [
			go.Pie(
				labels = ["Confirmed", "Deaths", "Recovered", "Active"],
				values = [confirmed_value, deaths_value, recovered_value, active_value],
				marker = {
					"colors": colors
				},
				hoverinfo = "label+value+percent",
				textinfo = "label+value",
				hole = 0.7,
				rotation = 45,
				insidetextorientation = "radial"
			)
		],
		"layout": go.Layout(
			title = {
				"text": f"Total cases {w_countries}",
				"y": 0.93,
				"x": 0.5,
				"xanchor": "center",
				"yanchor": "top"
			},
			titlefont = {
				"color": "white",
				"size": 20
			},
			font = {
				"family": "sans-serif",
				"color": "white",
				"size": 12
			},
			hovermode = "closest",
			paper_bgcolor = "#1f2c56",
			plot_bgcolor = "#1f2c56",
			legend = {
				"orientation": "h",
				"bgcolor": "#1f2c56",
				"xanchor": "center",
				"x": 0.5,
				"y": -0.7
			}
		)
	}
	# Return the figure
	return fig


# Line and bars chart
@app.callback(
	Output(
		component_id = "line_chart",
		component_property = "figure"
	),
	Input(
		component_id = "w_countries",
		component_property = "value"
	)
)
def update_line_chart(w_countries):
	# Filter the data
	covid_data_2 = covid_data.groupby(["date", "Country/Region"])[["confirmed", "deaths", "recovered", "active"]].sum().reset_index()
	covid_data_3 = covid_data_2[covid_data_2["Country/Region"] == w_countries][["Country/Region", "date", "confirmed"]].reset_index()
	covid_data_3["daily_confirmed"] = covid_data_3["confirmed"] - covid_data_3["confirmed"].shift(1)
	covid_data_3["rolling_avg"] = covid_data_3["daily_confirmed"].rolling(window = 7).mean()
	# Build the figure
	fig = {
		"data": [
			go.Bar(
				x = covid_data_3["date"].tail(30),
				y = covid_data_3["daily_confirmed"].tail(30),
				name = "Daily confirmed cases",
				marker = {
					"color": "orange"
				},
				hoverinfo = "text",
				hovertemplate = "<b>Date</b>: %{x} <br><b>Daily confirmed</b>: %{y:,.0f}<extra></extra>"
			),
			go.Scatter(
				x = covid_data_3["date"].tail(30),
				y = covid_data_3["rolling_avg"].tail(30),
				name = "Rolling avg. of the last 7 days - daily confirmed cases",
				mode = "lines",
				line = {
					"width": 3,
					"color": "#ff00ff"
				},
				hoverinfo = "text",
				hovertemplate = "<b>Date</b>: %{x} <br><b>Rolling Avg.</b>: %{y:,.0f}<extra></extra>"
			)
		],
		"layout": go.Layout(
			title = {
				"text": f"Last 30 days daily confirmed cases: {w_countries}",
				"y": 0.93,
				"x": 0.5,
				"xanchor": "center",
				"yanchor": "top"
			},
			titlefont = {
				"color": "white",
				"size": 20
			},
			xaxis = {
				"title": "<b>Date</b>",
				"color": "white",
				"showline": True,
				"showgrid": True,
				"showticklabels": True,
				"linecolor": "white",
				"linewidth": 1,
				"ticks": "outside",
				"tickfont": {
					"family": "Aerial",
					"color": "white",
					"size": 12
				}
			},
			yaxis = {
				"title": "<b>Confirmed cases</b>",
				"color": "white",
				"showline": True,
				"showgrid": True,
				"showticklabels": True,
				"linecolor": "white",
				"linewidth": 1,
				"ticks": "outside",
				"tickfont": {
					"family": "Aerial",
					"color": "white",
					"size": 12
				}
			},
			font = {
				"family": "sans-serif",
				"color": "white",
				"size": 12
			},
			hovermode = "closest",
			paper_bgcolor = "#1f2c56",
			plot_bgcolor = "#1f2c56",
			legend = {
				"orientation": "h",
				"bgcolor": "#1f2c56",
				"xanchor": "center",
				"x": 0.5,
				"y": -0.7
			}
		)
	}
	# Return the figure
	return fig


# Map
@app.callback(
	Output(
		component_id = "map_chart",
		component_property = "figure"
	),
	Input(
		component_id = "w_countries",
		component_property = "value"
	)
)
def update_map(w_countries):
	# Filter the data
	covid_data_4 = covid_data.groupby(["Lat", "Long", "Country/Region"])[["confirmed", "deaths", "recovered", "active"]].max().reset_index()
	covid_data_5 = covid_data_4[covid_data_4["Country/Region"] == w_countries]
	# Get zoom
	if w_countries:
		zoom = 2
		zoom_lat = dict_of_locations[w_countries]["Lat"]
		zoom_long = dict_of_locations[w_countries]["Long"]
	# Build the figure
	fig = {
		"data": [
			go.Scattermapbox(
				lon = covid_data_5["Long"],
				lat = covid_data_5["Lat"],
				mode = "markers",
				marker = go.scattermapbox.Marker(
					size = covid_data_5["confirmed"] / 1500,
					color = covid_data_5["confirmed"],
					colorscale = "HSV",
					showscale = False,
					sizemode = "area",
					opacity = 0.3
				),
				hoverinfo = "text",
				hovertemplate = "<b>Country:</b> " + covid_data_5["Country/Region"].astype(str) + "<br>" +
												"<b>Confirmed cases:</b> " + [f'{x:,.0f}' for x in covid_data_5["confirmed"]] + "<br>" + 
												"<b>Deaths:</b> " + [f'{x:,.0f}' for x in covid_data_5["confirmed"]] + "<br>" + 
												"<b>Recovered:</b> " + [f'{x:,.0f}' for x in covid_data_5["recovered"]] + "<br>" + 
												"<b>Active:</b> " + [f'{x:,.0f}' for x in covid_data_5["active"]] + "<extra></extra>"
			)
		],
		"layout": go.Layout(
			hovermode = "x",
			paper_bgcolor = "#1f2c56",
			plot_bgcolor = "#1f2c56",
			margin = {
				"r": 0,
				"l": 0,
				"t": 0,
				"b": 0
			},
			mapbox = dict(
				accesstoken = "pk.eyJ1IjoicXM2MjcyNTI3IiwiYSI6ImNraGRuYTF1azAxZmIycWs0cDB1NmY1ZjYifQ.I1VJ3KjeM-S613FLv3mtkw",
				center = go.layout.mapbox.Center(
					lat = zoom_lat,
					lon = zoom_long
				),
				style = "dark",
				zoom = zoom
			),
			autosize = True
		)
	}
	# Return the figure
	return fig
	
#Update violations
@app.callback(Output('live-graph', 'figure'),[Input('graph-update', 'n_intervals')])
def update_graph_scatter(input_data):   
    X.append(X[-1]+1)
    datas = dbviolations.child('no of violations').get().each()
    bla = datas[len(X)].val()
    Y.append(bla['violations'])   

    data = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode= 'lines+markers',
            line = {
				"width": 3,
				"color": "#ff00ff"
			}    
            
    )

    return {'data': [data],
    'layout' : go.Layout(paper_bgcolor = "#1f2c56",plot_bgcolor ="#1f2c56",title = {"text": f"Number of violations in the current location","y": 0.93,"x": 0.5,"xanchor": "center","yanchor": "top"},
    titlefont = {
		"color": "white",
		"size": 23
	},
    xaxis=dict(range=[min(X),max(X)],title='Intervals',color = 'white',linecolor = 'white', linewidth = 1,tickfont = {"family":"Aerial","color": "white","size": 12}),
    yaxis=dict(range=[0,max(Y)],title='Number of violations',color = 'white',linecolor = 'white', linewidth = 1,tickfont = {"family":"Aerial","color": "white","size": 20}),
    )}

@app.callback(
        dash.dependencies.Output('table','data'),        
        [dash.dependencies.Input('table-update', 'n_intervals')])

def updateTable(n):
	df = pd.DataFrame()
	df = getData()
	return df.to_dict('records')
	#return {'data':[df.to_dict('records')]}
    
	


# Run the app
if __name__ == "__main__":
  app.run_server(debug = True)