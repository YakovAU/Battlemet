import os
import time
import webbrowser

import requests
import tkinter as tk
from tkinter import font as tkfont, simpledialog, messagebox
import random
from threading import Timer
from collections import deque

import yaml


class ServerFrame(tk.Frame):
    def __init__(self, parent=None, server_id=None, refresh_interval=60, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.server_id = server_id
        self.refresh_interval = refresh_interval
        self.refresh_timer = None

        # We will use deque for its automatic removal of excess elements
        self.player_counts = deque(maxlen=60)

        self.server_name_label = tk.Label(self)
        self.server_name_label.pack()

        self.player_count_label = tk.Label(self)
        self.player_count_label.pack()

        self.current_time_label = tk.Label(self)
        self.current_time_label.pack()

        self.counter_var = tk.StringVar(value='0')
        self.counter_label = tk.Label(self, textvariable=self.counter_var)
        self.counter_label.pack()

        self.refresh_button = tk.Button(self, text='Refresh Now', command=self.refresh_data)
        self.refresh_button.pack()

        self.separator = tk.Label(self, text="-" * 40)
        self.separator.pack()

        self.refresh_data()

    def get_server_data(self):
        try:
            url = f"https://api.battlemetrics.com/servers/{self.server_id}"
            response = requests.get(url, timeout=5)  # 5 seconds timeout
            response.raise_for_status()  # Raise an HTTPError if the response was unsuccessful
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                # Server ID is invalid
                messagebox.showerror("Error", f"Invalid server ID: {self.server_id}")
                self.parent.log(f"Invalid server ID: {self.server_id}")
            else:
                # Other HTTP error
                self.parent.log(f"Error occurred for server ID {self.server_id}: {e}")
            return None, None, None  # Return None for all values
        except requests.exceptions.RequestException as e:
            # Other request error
            self.parent.log(f"Error occurred for server ID {self.server_id}: {e}")
            return None, None, None  # Return None for all values

        data = response.json()

        server_name = data['data']['attributes']['name']
        player_count = data['data']['attributes']['players']
        current_time = data['data']['attributes']['details'].get('time', 'N/A')

        self.parent.log(f"Server {server_name} (ID: {self.server_id}) response: {data}")
        self.parent.log(f"Server {server_name} (ID: {self.server_id}) player count: {player_count}")

        return server_name, player_count, current_time

    def refresh_data(self):
        if self.refresh_timer is not None:
            self.after_cancel(self.refresh_timer)

        server_name, player_count, current_time = self.get_server_data()

        if server_name is None and player_count is None and current_time is None:
            # Server is not responsive
            self.server_name_label['text'] = "Server Name: " + self.server_id
            self.player_count_label['text'] = "Server Status: DOWN"
            self.current_time_label['text'] = ""
            self.counter_var.set("Server Down")
            self.refresh_button.configure(state='disabled')  # Disable refresh button
        else:
            # Server is responsive
            self.player_counts.append(player_count)

            if len(self.player_counts) > 1:
                if player_count > self.player_counts[-2]:
                    self.player_count_label.configure(fg='green')
                elif player_count < self.player_counts[-2]:
                    self.player_count_label.configure(fg='red')
            else:
                self.player_count_label.configure(fg='black')

            self.server_name_label['text'] = "Server Name: " + server_name
            self.player_count_label['text'] = f"Player Count: {player_count}"
            self.current_time_label['text'] = "Current Time: " + current_time
            self.counter_var.set(str(self.refresh_interval))
            self.refresh_button.configure(state='normal')  # Enable refresh button

        self.refresh_timer = self.after(self.refresh_interval * 1000, self.refresh_data)
        self.update_counter()

    def update_counter(self):
        current_counter = self.counter_var.get()
        if current_counter.isdigit():
            current_counter = int(current_counter)
            if current_counter > 0:
                self.counter_var.set(str(current_counter - 1))
                self.after(1000, self.update_counter)


class App(tk.Tk):
    def __init__(self, server_ids, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console_window = None
        self.console_text = None
        self.server_ids = server_ids
        self.log_messages = []
        self.title("BattleTracker")
        if not os.path.exists('config.yaml'):
            # Default server IDs
            self.server_ids = ['5526400', '5526399', '5526398', '1720719', '21395315', '21268704', '20237846']
            with open('config.yaml', 'w') as f:
                yaml.safe_dump({'server_ids': self.server_ids}, f)
        else:
            with open('config.yaml') as f:
                config = yaml.safe_load(f)
            self.server_ids = config.get('server_ids', [])

        self.init_menu()
        self.server_frames = []
        self.update_server_frames()

    def init_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set Server IDs", command=self.set_server_ids)
        settings_menu.add_command(label="Open Console", command=self.open_console)

        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="Created by Yakov. 2023.", command=self.open_github)

    def set_server_ids(self):
        server_ids_str = simpledialog.askstring("Set Server IDs",
                                                "Enter Server IDs (comma separated):\nIDs can be found in the "
                                                "battlemetrics URL",
                                                initialvalue=",".join(self.server_ids))
        if server_ids_str is not None:
            self.server_ids = [id.strip() for id in server_ids_str.split(",") if id.strip()]
            self.update_server_frames()

            # Save the new server IDs to the configuration file
            with open('config.yaml', 'w') as f:
                yaml.safe_dump({'server_ids': self.server_ids}, f)

    def open_github(self):
        webbrowser.open('https://github.com/YakovAU')

    def open_console(self):
        if self.console_window is None:
            self.console_window = tk.Toplevel(self)
            self.console_window.title("Console Window")
            self.console_window.protocol("WM_DELETE_WINDOW", self.on_close_console)

            self.console_text = tk.Text(self.console_window, wrap='word', height=30, width=100)
            self.console_text.pack(expand=True, fill='both')

        self.console_window.lift()

    def on_close_console(self):
        self.console_window.destroy()
        self.console_window = None
        self.console_text = None

    def log(self, msg):
        if self.console_text is not None:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            self.console_text.insert('end', f"{timestamp} - {msg}\n")
            self.console_text.see('end')

    def update_server_frames(self):
        # Clear the server frame
        for frame in self.server_frames:
            frame.grid_remove()

        self.server_frames = []

        # Add new server frames
        max_columns = 6
        rows_per_column = 7
        for i, server_id in enumerate(self.server_ids):
            column = i // rows_per_column
            row = i % rows_per_column
            if column >= max_columns:
                break
            frame = ServerFrame(parent=self, server_id=server_id, refresh_interval=random.randint(55, 65))
            frame.grid(row=row, column=column, sticky='nsew')
            self.server_frames.append(frame)

        self.update_idletasks()  # Force an update of the GUI


if __name__ == "__main__":
    server_ids = ['5526400', '5526399', '5526398', '1720719', '21395315', '21268704', '20237846']
    app = App(server_ids)
    app.mainloop()

root = tk.Tk()

server_ids = ['5526400', '5526399', '5526398', '1720719', '21395315', '21268704', '20237846']

for server_id in server_ids:
    frame = ServerFrame(root, server_id, refresh_interval=random.randint(55, 65))
    frame.pack()

root.mainloop()
