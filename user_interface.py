import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import Network


def get_user_input(start, end, date_input, algo_choice):
    """
    Retrieves and validates user input for the starting location, 
    ending location, date, and chosen algorithm.
    
    Args:
    start (str): The starting location input by the user.
    end (str): The ending location input by the user.
    date_input (str): The date input by the user in the format "YYYY-MM-DD-HH-MM".
    algo_choice (str): The algorithm choice made by the user ("shortest" or "fastest").
    
    Returns:
    tuple: A tuple containing validated start location, end location, 
           datetime object (parsed from date_input or current date), and algorithm choice.
    """
    if date_input:
        try:
            datetime_object = datetime.strptime(date_input, "%Y-%m-%d-%H-%M")
        except ValueError:
            messagebox.showerror("Invalid Date", "Invalid date format. Using current date instead.")
            datetime_object = datetime.now()
    else:
        datetime_object = datetime.now()

    if algo_choice not in ['shortest', 'fastest']:
        messagebox.showinfo("Info", "shortest by default.")
        algo_choice = 'shortest'

    return start, end, datetime_object, algo_choice

def on_run_algorithm():
    """
    Handles the logic to run the selected algorithm based on user input, 
    validates the input, and displays the result along with any travel time (if fastest() is chosen).
    """
    start = start_entry.get()
    end = end_entry.get()
    date_input = date_entry.get()
    algo_choice = algo_choice_var.get()

    if not start or not end:
        messagebox.showerror("Missing Information", "Please provide both start and end locations.")
        return

    start, end, date_time, algorithm = get_user_input(start, end, date_input, algo_choice)

    network = Network.Network(datetime=date_time)

    if algorithm == 'fastest':
        result_text.set(f"Running the fastest algorithm from {start} to {end}...")
        path, duration = network.fastest(start, end)
    elif algorithm == 'shortest':
        result_text.set(f"Running the shortest algorithm from {start} to {end}...")
        path = network.shortest(start, end)
        duration = None

    if path:
        result_text.set(f"Path found: {' -> '.join(path)}")
        if duration is not None:
            duration_label.config(text=f"Travel Time: {duration} minutes")
        else:
            duration_label.config(text="")  
    else:
        result_text.set("No path found.")
        duration_label.config(text="")

    network.visualize_network_interactive(path)

# Main window
root = tk.Tk()
root.title("Sibra")
root.geometry("450x500")

# Start Location 
start_label = tk.Label(root, text="Start:")
start_label.pack(pady=5)
start_entry = tk.Entry(root)
start_entry.pack(pady=5)

# End Location 
end_label = tk.Label(root, text="End:")
end_label.pack(pady=5)
end_entry = tk.Entry(root)
end_entry.pack(pady=5)

# Date Input 
date_label = tk.Label(root, text="Date (YYYY-MM-DD-HH-MM):")
date_label.pack(pady=5)
date_entry = tk.Entry(root)
date_entry.pack(pady=5)

# Algorithm Choice 
algo_choice_var = tk.StringVar(value="shortest")
algo_choice_label = tk.Label(root, text="How do you want to travel ?")
algo_choice_label.pack(pady=5)

shortest_radio = tk.Radiobutton(root, text="Shortest", variable=algo_choice_var, value="shortest")
shortest_radio.pack(pady=5)

fastest_radio = tk.Radiobutton(root, text="Fastest", variable=algo_choice_var, value="fastest")
fastest_radio.pack(pady=5)

# Foremost ????

# Run Algorithm Button
run_button = tk.Button(root, text="Run Algorithm", command=on_run_algorithm)
run_button.pack(pady=20)

# Result Display Label
result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text, wraplength=350)
result_label.pack(pady=10)

# Travel Time Label
duration_label = tk.Label(root, text="", font=("Helvetica", 10, "italic"), fg="blue")
duration_label.pack(pady=10)

root.mainloop()
