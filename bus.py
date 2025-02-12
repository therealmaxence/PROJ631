from datetime import datetime, timedelta
import holidays
import networkx as nx
import matplotlib.pyplot as plt
import heapq
from collections import deque, defaultdict
import plotly.graph_objects as go


def dates2dic(dates):
    dic = {}
    splitted_dates = dates.split("\n")
    for stop_dates in splitted_dates:
        tmp = stop_dates.split(" ")
        dic[tmp[0]] = tmp[1:]
    return dic

def is_holiday(date):
    """
    Détermine si une date est un week-end ou un jour férié en France.
    
    :param: date_entree: Date au format datetime.date
    :return: Un integer, 1 si la date est un week-end ou un jour férié, 0 sinon
    """
    # Vérification si la date est un week-end
    if date.weekday() in [5, 6]:  # 5 = Samedi, 6 = Dimanche
        return 1
    
    # Vérification si la date est un jour férié en France
    jours_feries = holidays.France()
    if date in jours_feries:
        return 1
    
    # Sinon, c'est un jour ouvré
    return 0

def create_lines():
    files = [
        './data/1_Poisy-ParcDesGlaisins.txt',
        './data/2_Piscine-Patinoire_Campus.txt',
        './data/4_Seynod_Neigeos-Campus.txt'
    ]

    lines = []
    for file in files:
        try:
            with open(file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"File {file} not found. Skipping.")
            continue

        slited_content = content.split("\n\n")
        try:
            line = Line(
                regular_date_go=dates2dic(slited_content[1]),
                regular_date_back=dates2dic(slited_content[2]),
                we_holidays_date_go=dates2dic(slited_content[4]),
                we_holidays_date_back=dates2dic(slited_content[5])
            )
            lines.append(line)
        except IndexError:
            print(f"Error processing file {file}. Content format may be invalid.")
            continue
    return lines

class Bus_stop:
    def __init__(self, name, lines=None):
        self.name = name
        self.lines = [] if lines is None else lines

    def __eq__(self, other):
        return isinstance(other, Bus_stop) and self.name == other.name

class Edge:
    def __init__(self, start, end, line, duration = 1000):
        self.start = start
        self.end = end
        self.line = line
        self.duration = duration # Duration in minutes

    def get_duration(self):
        return self.duration


class Line:
    def __init__(self, regular_date_go, regular_date_back, we_holidays_date_go, we_holidays_date_back):
        self.regular_date_go = regular_date_go
        self.regular_date_back = regular_date_back
        self.we_holidays_date_go = we_holidays_date_go
        self.we_holidays_date_back = we_holidays_date_back



def create_bus_stops(lines):
    bus_stops = {}

    for line in lines:
        # Loop over each dictionary in the line
        for stop_category in ['regular_date_go', 'regular_date_back', 'we_holidays_date_go', 'we_holidays_date_back']:
            stops = getattr(line, stop_category)  # Get the dictionary by category
            for stop, times in stops.items():
                if stop not in bus_stops:
                    bus_stops[stop] = Bus_stop(stop, [line])  # Create a new bus stop if it doesn't exist
                elif line not in bus_stops[stop].lines:
                    bus_stops[stop].lines.append(line)  # Append line to the stop if it's not already present

    return list(bus_stops.values())



def get_next_stop(stop_name, datetime, line, direction):
    if is_holiday(datetime):
        stops = line.we_holidays_date_go if direction == "go" else line.we_holidays_date_back
    else:
        stops = line.regular_date_go if direction == "go" else line.regular_date_back
    stop_keys = list(stops.keys())
    for i, stop in enumerate(stop_keys):
        if stop_name == stop:
            if i == len(stop_keys) - 1:
                return None
            next_stop = stop_keys[i + 1]
            return next_stop
    return None



def get_duration(stop_name, next_stop, datetime, line, direction):
    
    if is_holiday(datetime):
        stops = line.we_holidays_date_go if direction == "go" else line.we_holidays_date_back
    else:
        stops = line.regular_date_go if direction == "go" else line.regular_date_back

    if stop_name not in list(stops.keys()) or next_stop not in list(stops.keys()):
        return 0.0

    current_times = stops[stop_name]
    next_times = stops[next_stop]

    current_time = [datetime.strptime(t, "%H:%M").time() for t in current_times if t != "-"]
    next_time = [datetime.strptime(t, "%H:%M").time() for t in next_times if t != "-"]

    for current_t in current_time:
        if current_t > datetime.time():
            for next_t in next_time:
                if next_t > current_t:
                    duration = (
                        datetime.combine(datetime.date(), next_t) 
                      - datetime.combine(datetime.date(), current_t))
                    return duration.total_seconds() / 60
    
    return 0.0



def create_edges(bus_stops, datetime):
    edges = []

    schedules = [
        ("regular_date_go", "go"),
        ("regular_date_back", "back"),
        ("we_holidays_date_go", "go"),
        ("we_holidays_date_back", "back"),
    ]

    for stop in bus_stops:
        for line in stop.lines:
            for schedule, direction in schedules:
                stops_schedule = getattr(line, schedule, {})
                for stop_name, times in stops_schedule.items():
                    next_stop = get_next_stop(stop_name, datetime, line, direction=direction)
                    duration = None
                    edge = Edge(start=stop_name, end=next_stop, line=line, duration=duration)
                    edges.append(edge)
    return edges

class Network:
    def __init__(self, bus_stops=None, edges=None, lines=None, datetime=datetime.now()):
        self.bus_stops = [] if bus_stops is None else bus_stops
        self.edges = [] if edges is None else edges
        self.lines = lines
        self.datetime = datetime
        self.graph = nx.DiGraph()  
        self.create_network()


    def create_network(self):
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
                    print(f"New duration from {current_stop} to {neighbor} on line {line}: {new_duration}") 
                    if new_duration < durations[neighbor]:
                        durations[neighbor] = new_duration
                        heapq.heappush(priority_queue, (new_duration, neighbor, line))
                        self.graph[current_stop][neighbor]["duration"] = new_duration


        


    def fastest(self, start, end):
        self.set_durations(start, self.datetime)
        durations = {stop.name: float('inf') for stop in self.bus_stops}
        durations[start] = 0  
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
                duration = self.graph[current_node][neighbor]["duration"]
                print(f"Current distance: {current_distance}, duration: {duration}")
                new_duration = current_distance + (duration if duration else 0)    
                if new_duration < durations[neighbor]:
                    durations[neighbor] = new_duration
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_duration, neighbor))
        return None, None 
    

    def shortest(self, start, end):
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

            


    def visualize_network_interactive(self, path=[]):
        pos = nx.spring_layout(self.graph, seed=42) 
        x_nodes = [pos[node][0] for node in self.graph.nodes()]
        y_nodes = [pos[node][1] for node in self.graph.nodes()]
        edge_x = []
        edge_y = []
        edge_trace = []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None]) 
            edge_y.extend([y0, y1, None])
            if edge[0] in path and edge[1] in path:
                edge_trace.append(go.Scatter(
                    x=[x0, x1], y=[y0, y1],
                    line=dict(width=2, color='red'), 
                    hoverinfo='none',
                    mode='lines'
                ))
            else:
                edge_trace.append(go.Scatter(
                    x=[x0, x1], y=[y0, y1],
                    line=dict(width=0.5, color='#888'),
                    hoverinfo='none',
                    mode='lines'
                ))
        node_trace = go.Scatter(
            x=x_nodes, y=y_nodes,
            mode='markers+text',
            text=list(self.graph.nodes),
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                size=10,
                color='skyblue',
                line=dict(width=2, color='black')
            )
        )
        fig = go.Figure(data=[*edge_trace, node_trace],
                        layout=go.Layout(
                            title='<b>Interactive Bus Network Graph</b>',
                            titlefont_size=16,
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=40),
                            xaxis=dict(showgrid=False, zeroline=False),
                            yaxis=dict(showgrid=False, zeroline=False)
                        ))
        fig.show()
