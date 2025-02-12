from algorithms import dates2dic


class Line:
    # All the schedules are stored in dictionaries which have been given with th exercise (as well as the data sheets)
    def __init__(self, regular_date_go, regular_date_back, we_holidays_date_go, we_holidays_date_back):
        self.regular_date_go = regular_date_go
        self.regular_date_back = regular_date_back
        self.we_holidays_date_go = we_holidays_date_go
        self.we_holidays_date_back = we_holidays_date_back


def create_lines():
    """
    Reads bus line data from predefined files in data folder and creates Line objects.
    Each file is expected to contain bus schedule information in a specific format.
    If a file is not found, it is skipped with a warning message.
    If the content format of a file is invalid, it is also skipped with a warning message.
    Returns:
        list: A list of Line objects created from the valid files.
    Raises:
        FileNotFoundError: If any of the files are not found.
        IndexError: If the content format of any file is invalid.
    """

    # List of Sibra bus schedule, I tried adding a new file to the list but I couldn't recreate the same data format
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