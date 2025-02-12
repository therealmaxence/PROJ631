from Bus_stop import create_bus_stops
from Edge import create_edges
from Line import create_lines
from datetime import datetime, timedelta
import heapq
import networkx as nx
from algorithms import get_duration
import plotly.graph_objects as go
from collections import deque, defaultdict


class Network:
    def __init__(self, bus_stops=None, edges=None, lines=None, datetime=datetime.now()):
        """
        Initializes a Network instance.

        Args:
            bus_stops (list, optional): A list of Bus_stop instances. Defaults to an empty list.
            edges (list, optional): A list of Edge instances. Defaults to an empty list.
            lines (list, optional): A list of Line instances. Defaults to None.
            datetime (datetime, optional): The current date and time. Defaults to the current datetime.
        """
        self.bus_stops = [] if bus_stops is None else bus_stops
        self.edges = [] if edges is None else edges
        self.lines = lines
        self.datetime = datetime
        self.graph = nx.DiGraph()  
        self.create_network()

    def create_network(self):
        """
        Creates the bus network by initializing bus stops, edges, and lines, and adding them to the graph.
        """
        self.bus_stops = create_bus_stops(create_lines())
        self.edges = create_edges(self.bus_stops, self.datetime)
        self.lines = create_lines()

        for edge in self.edges:
            if edge.start and edge.end: 
                self.graph.add_edge(edge.start, edge.end, duration=edge.duration, line=edge.line)

    def set_durations(self, start_stop_name, current_datetime):
        """
        Updates the duration of edges in the network graph, considering the possibility of changing lines.
        
        :param start_stop_name: The starting bus stop name to initialize the duration update.
        :param current_datetime: The datetime object used to determine durations.
        """
        if not self.graph:
            print("Graph is empty. Please initialize the network first.")
            return
        durations = {stop: float('inf') for stop in self.graph.nodes}
        durations[start_stop_name] = 0  
        priority_queue = [(0, start_stop_name, None)]  
        while priority_queue:
            current_time, current_stop, current_line = heapq.heappop(priority_queue)
            for neighbor in self.graph.neighbors(current_stop):
                edge_data = self.graph[current_stop][neighbor]
                lines = edge_data["line"] if isinstance(edge_data["line"], list) else [edge_data["line"]]
                for line in lines:  
                    line_duration = get_duration(current_stop, neighbor, current_datetime, line, direction="go")
                    if current_line and current_line != line:
                        switch_penalty = 2 
                    else:
                        switch_penalty = 0
                    new_duration = line_duration + switch_penalty
                    #print(f"New duration from {current_stop} to {neighbor} on line {line}: {new_duration}") 
                    if new_duration < durations[neighbor]:
                        durations[neighbor] = new_duration
                        heapq.heappush(priority_queue, (new_duration, neighbor, line))
                        self.graph[current_stop][neighbor]["duration"] = new_duration


                            
    def visualize_network_interactive(self, path=[]):
        """
        Visualizes the network graph interactively using Plotly.

        This method generates an interactive visualization of the network graph
        stored in `self.graph`. Nodes are displayed as markers, and edges are
        displayed as lines. If a path is provided, the edges in the path are
        highlighted in red.

        Parameters:
        -----------
        path : list of Bus_stop objects, optional
            Default is an empty list.

        Returns:
        --------
        None
            Displays the interactive graph visualization using Plotly.
        """
        pos = nx.spring_layout(self.graph, seed=42)
        x_nodes = [pos[node][0] for node in self.graph.nodes()]
        y_nodes = [pos[node][1] for node in self.graph.nodes()]
        edge_trace = []

        for edge in self.graph.edges():
            #print(edge)
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_color = list(filter(lambda x: x.start == edge[0] and x.end == edge[1], self.edges))[0].get_color()

            color = edge_color
            width = 6 if edge[0] in path and edge[1] in path else 2

            edge_trace.append(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                line=dict(width=width, color=color),
                hoverinfo='text',
                mode='lines',
            ))

        node_trace = go.Scatter(
            x=x_nodes, y=y_nodes,
            mode='markers+text',
            text=list(self.graph.nodes),
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                size=10,
                color='#EDEDE9',
                line=dict(width=2, color='black')
            )
        )
        fig = go.Figure(data=[*edge_trace, node_trace],
                        layout=go.Layout(
                            title='<b>Sibra Network</b>',
                            titlefont_size=18,
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=40),
                            xaxis=dict(showgrid=False, zeroline=False),
                            yaxis=dict(showgrid=False, zeroline=False)
                        ))
        fig.show()

    def get_next_departure(self, stop_name):
        """
        Get the next departure time for a given bus stop.

        Args:
            stop_name (str): The name of the bus stop.

        Returns:
            float: The time between datetime and next departure time from the bus stop in minutes.
        """
        for line in self.lines:
            for stop_category in ['regular_date_go', 'regular_date_back', 'we_holidays_date_go', 'we_holidays_date_back']:
                stops = getattr(line, stop_category)
                if stop_name in stops:
                    times = stops[stop_name]
                    for time in times:
                        if time != "-" and self.datetime.time() < datetime.strptime(time, "%H:%M").time():
                            time_diff = datetime.strptime(time, "%H:%M") - self.datetime
                            print(time_diff.total_seconds() / 60.0) 
                            return time_diff.total_seconds() / 60.0
        return None

    def fastest(self, start, end):
        """
        Finds the fastest path between two bus stops using Dijkstra's algorithm.

        Args:
            start (str): The starting node (departure).
            end (str): The ending node (arrival).

        Returns:
            tuple: A tuple containing:
                - list: The list of bus stops representing the fastest path from start to end.
                - float: The total duration of the fastest path.

            If no path is found, returns (None, None).
        """
        self.set_durations(start, self.datetime)

        durations = {stop.name: float('inf') for stop in self.bus_stops}
        durations[start] = self.get_next_departure(start)
        priority_queue = [(0, start)]
        previous_nodes = {start: None}
        visited = set()

        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)

            if current_node in visited:
                continue
            visited.add(current_node)

            if current_node == end:
                path = []
                while current_node is not None:
                    path.append(current_node)
                    current_node = previous_nodes.get(current_node)
                path.reverse()
                return path, durations[end]

            for edge in self.graph.edges(current_node):
                neighbor = edge[1]
                duration = self.graph[current_node][neighbor].get("duration")
                if duration is None:
                    duration = 0.0
                new_duration = current_distance + duration
                if new_duration < durations[neighbor]:
                    durations[neighbor] = new_duration
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_duration, neighbor))

        return None, None 


    def shortest(self, start, end):
        """
        Finds the shortest path between two nodes in a graph using Breadth-First Search (BFS).

        Args:
            start (str): The starting node (departure).
            end (str): The ending node (arrival).

        Returns:
            list: A list of nodes representing the shortest path from start to end.
                If no path is found, returns None.
        """
        adjacency_list = defaultdict(list)
        for edge in self.edges:
            if edge.start and edge.end: 
                adjacency_list[edge.start].append(edge.end)
        queue = deque([(start, [start])])
        visited = set()

        while queue:
            current_stop, path = queue.popleft()
            if current_stop == end:
                return path
            visited.add(current_stop)
            for neighbor in adjacency_list[current_stop]:
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
        return None
