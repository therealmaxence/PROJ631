from Bus_stop import get_next_stop

class Edge:
    def __init__(self, start, end, line, duration=None, color=None):
        self.start = start
        self.end = end
        self.line = line
        self.duration = duration
        self.color = color

    def get_duration(self):
        return self.duration
    
    def get_color(self):
        return self.color

def create_edges(bus_stops, datetime):
    edges = []

    schedules = [
        ("regular_date_go", "go"),
        ("regular_date_back", "back"),
        ("we_holidays_date_go", "go"),
        ("we_holidays_date_back", "back"),
    ]

    colors = ["green", "blue", "yellow"]

    for stop in bus_stops:
        for line in stop.lines:
            color = colors[stop.lines.index(line)]
            for schedule, direction in schedules:
                stops_schedule = getattr(line, schedule, {})
                for stop_name, times in stops_schedule.items():
                    next_stop = get_next_stop(stop_name, datetime, line, direction=direction)
                    duration = None
                    edge = Edge(start=stop_name, end=next_stop, line=line, duration=duration, color=color)
                    edges.append(edge)
    return edges