import dash
import dash_cytoscape as cyto
cyto.load_extra_layouts()

from dash import html, dcc, Output, Input

from worlds.factorio_bobs import modpacks, FactorioModpack
from worlds.factorio_bobs.RecipeEngine.Graph import Graph


app = dash.Dash(__name__)
stylesheet = [
    {
        'selector': 'node',
        'style': {
            'shape': 'round-rectangle',
            'label': 'data(label)',
            'width': 'data(width)',
            'height': 'data(height)',

            'text-wrap': 'wrap',
            'text-max-width': 120,

            'text-valign': 'center',
            'text-halign': 'center',

            'font-size': 10,

            'padding': '10px',

            'background-color': '#2b2b2b',
            'color': 'white'
        }
    },

    {
        'selector': '[type = "AndNode"]',
        'style': {
            'background-color': 'black'
        }
    },
    {
        'selector': '[type = "OrNode"]',
        'style': {
            'background-color': 'red'
        }
    },
    {
        'selector': '[type = "ItemNode"]',
        'style': {
            'background-color': 'blue'
        }
    },
    {
        'selector': '[type = "RecipeNode"]',
        'style': {
            'background-color': 'green'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'width': 2,
            'line-color': '#888',
            'target-arrow-color': '#888',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',

            'label': 'data(weight)',
            'font-size': 8,
        }
    },
    {
        'selector': 'node:selected',
        'style': {
            'border-width': 4,
            'border-color': '#ffcc00',
            'opacity': 1,
            'z-index': 9999
        }
    },
    {
        'selector': 'edge:connected',
        'style': {
            'line-color': '#ffcc00',
            'target-arrow-color': '#ffcc00',
            'opacity': 1,
            'width': 3
        }
    },
    {
    'selector': 'node:neighbor',
    'style': {
        'border-width': 3,
        'border-color': 'orange'
        }
    }
]
loaded_graph: None | Graph = None

def main():
    app.layout = html.Div([
        cyto.Cytoscape(
            id='graph',
            layout={
                'name': 'dagre',
                'rankDir': 'TB',  # top → bottom
                'nodeSep': 50,
                'rankSep': 100
            },
            autoungrabify=False,
            autounselectify=False,
            boxSelectionEnabled=True,
            stylesheet=stylesheet,
            style={'width': '70%', 'height': '500px'}
        ),

        html.Div([
            html.Div(
                dcc.Dropdown(
                    id='graph-selector',
                    options=[
                        {'label': name, 'value': name} for name in modpacks
                    ],
                    value='graph1'
                )
            ),
            html.Div(
            id='node-details',
            style={
                'width': '30%',
                'padding': '12px',
                'border': '1px solid #ccc',
                'overflowY': 'auto'
            }),
        ])
    ])
    app.run(debug=True)

@app.callback(
    Output('graph', 'elements'),
    Input('graph-selector', 'value')
)
def update_graph(modpack_name):
    if modpack_name is None:
        return []

    modpack: FactorioModpack = modpacks[modpack_name]
    modpack.init_items()
    modpack.init_locations()
    modpack.init_pack_check()
    global loaded_graph
    loaded_graph: Graph = modpack.game_item_manager.recipe_engine

    elements = []
    for node in loaded_graph.nodes.values():
        elements.append({'data': {'id': node.name,
                                  'label': node.name,
                                  'type': type(node).__name__,
                                  'width': 150,
                                  'height': 100,
                                  }})
        for edge, weight in node.used_by.items():
            elements.append({'data': {'source': node.name, 'target': edge.name, 'weight': weight}})

    return elements

@app.callback(
    Output('node-details', 'children'),
    Input('graph', 'tapNodeData')
)
def show_node_details(data):
    if not data:
        return "Select a node"


    return html.Div([
        html.H3(data.get('label', 'Unnamed')),
        html.P(f"Type: {data.get('type', 'N/A')}"),
        html.Hr(),
        html.P(data.get('info', 'No details available'))
    ])

if __name__ == '__main__':
    main()
