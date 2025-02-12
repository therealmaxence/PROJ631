from algorithms import is_holiday

class Bus_stop:
    def __init__(self, name, lines=None):
        self.name = name
        self.lines = [] if lines is None else lines # List of Line objects

    def __eq__(self, other):
        return isinstance(other, Bus_stop) and self.name == other.name


def create_bus_stops(lines):
    """
    Creates a list of Bus_stop instances from a list of bus lines.

    Args:
        lines (list of Line objects): A list of bus lines, where each line contains dictionaries of stops.

    Returns:
        list: A list of Bus_stop instances.
    """
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
    """
    Get the next bus stop based on the current stop, date, line, and direction.

    Args:
        stop_name (str): The name of the current bus stop.
        datetime (datetime): The date and time at which you want to find the next stop.
        line (Line object): The bus line object containing stop information.
        direction (str): The direction of the bus ("go" or "back").

    Returns:
        str or None: The name of the next bus stop if it exists, otherwise None (bus stop not found).
    """
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


