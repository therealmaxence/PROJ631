import heapq
import holidays

# This method was given by the exercise
def dates2dic(dates):
    dic = {}
    splitted_dates = dates.split("\n")
    for stop_dates in splitted_dates:
        tmp = stop_dates.split(" ")
        dic[tmp[0]] = tmp[1:]
    return dic


def is_holiday(date):
    """
    Determines if a given date is a holiday.
    Args:
        date (datetime.date object): The date to check.
    Returns:
        int: Returns 1 if the date is a holiday or a weekend (Saturday or Sunday), otherwise returns 0.
    """
    if date.weekday() in [5, 6]: 
        return 1
    holidays_ = holidays.France() 
    if date in holidays_:
        return 1
    return 0


def get_duration(stop_name, next_stop, datetime, line, direction): 
    """
    Calculate the duration in minutes between two bus stops based on the given datetime, line, and direction.

    Args:
        stop_name (str): The name of the current bus stop.
        next_stop (str): The name of the next bus stop.
        datetime (datetime): The current datetime.
        line (Line object): The bus line object containing schedule information.
        direction (str): The direction of the bus ("go" or "back") for optimizing time.

    Returns:
        float: The duration in minutes between the two stops. Returns 0.0 if the stops are not found or if no valid time is found.
    """
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


# This is the method responsible for the problems in the "fastest" algorithm
def set_durations(self, start_stop_name, current_datetime):
    """
    Updates the duration of edges in the network graph, considering the possibility of changing lines.
    
    :param start_stop_name: The starting bus stop name to initialize the duration update.
    :param current_datetime: The datetime object used to determine durations.
    """
    if not self.graph:
        print("Network is empty.")
        return
        
    durations = {stop: float('inf') for stop in self.graph.nodes}
    durations[start_stop_name] = 0
    priority_queue = [(0, start_stop_name, None)]  

    for neighbor in self.graph.neighbors(start_stop_name):
        edge_data = self.graph[start_stop_name][neighbor]
        lines = edge_data["line"] if isinstance(edge_data["line"], list) else [edge_data["line"]]

        for line in lines:
            line_duration_go = get_duration(start_stop_name, neighbor, current_datetime, line, direction="go")
            line_duration_back = get_duration(start_stop_name, neighbor, current_datetime, line, direction="back")
            if line_duration_go > line_duration_back:
                if line_duration_back > 0:
                    durations[neighbor] = line_duration_back
                    heapq.heappush(priority_queue, (line_duration_back, neighbor, line))
            else:
                if line_duration_go > 0:
                    durations[neighbor] = line_duration_go
                    heapq.heappush(priority_queue, (line_duration_go, neighbor, line))

    while priority_queue:
        current_time, current_stop, current_line = heapq.heappop(priority_queue)

        for neighbor in self.graph.neighbors(current_stop):
            edge_data = self.graph[current_stop][neighbor]
            lines = edge_data["line"] if isinstance(edge_data["line"], list) else [edge_data["line"]]

            for line in lines:  
                line_duration_go = get_duration(current_stop, neighbor, current_datetime, line, direction="go")
                line_duration_back = get_duration(current_stop, neighbor, current_datetime, line, direction="back")
                if line_duration_go > line_duration_back:
                    if current_line and current_line != line:
                        switch_penalty = get_duration(current_stop, neighbor, current_datetime, line, direction="back") 
                    else:
                        switch_penalty = 0
                    new_duration = line_duration_back + switch_penalty

                else:
                    if current_line and current_line != line:
                        switch_penalty = get_duration(current_stop, neighbor, current_datetime, line, direction="go") 
                    else:
                        switch_penalty = 0
                    new_duration = line_duration_go + switch_penalty
                    
                if new_duration < durations[neighbor]:
                    durations[neighbor] = new_duration
                    heapq.heappush(priority_queue, (new_duration, neighbor, line))
                    self.graph[current_stop][neighbor]["duration"] = new_duration