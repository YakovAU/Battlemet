import requests
import tkinter as tk
from tkinter import font as tkfont
import random
from threading import Timer


class ServerFrame(tk.Frame):
    def __init__(self, parent, server_id, refresh_interval=60, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.server_id = server_id
        self.refresh_interval = refresh_interval
        self.prev_player_count = None
        self.refresh_timer = None  # Initialize refresh_timer in __init__

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
        url = f"https://api.battlemetrics.com/servers/{self.server_id}"
        response = requests.get(url)
        data = response.json()

        server_name = data['data']['attributes']['name']
        player_count = data['data']['attributes']['players']
        current_time = data['data']['attributes']['details'].get('time', 'N/A')

        return server_name, player_count, current_time

    def refresh_data(self):
        if self.refresh_timer is not None:
            self.refresh_timer.cancel()  # Cancel the previous timer before starting a new one

        server_name, player_count, current_time = self.get_server_data()

        # Determine the trend
        trend = ''
        if self.prev_player_count is not None:
            if player_count > self.prev_player_count:
                trend = ' 🟢'
            elif player_count < self.prev_player_count:
                trend = ' 🔴'
        self.prev_player_count = player_count

        self.server_name_label['text'] = "Server Name: " + server_name
        self.player_count_label['text'] = "Player Count: " + str(player_count) + trend
        self.current_time_label['text'] = "Current Time: " + current_time
        self.counter_var.set(str(self.refresh_interval))
        self.counter_label['text'] = "Refresh in: " + self.counter_var.get() + " seconds"

        self.refresh_timer = Timer(self.refresh_interval, self.refresh_data)
        self.refresh_timer.start()

        self.update_counter()

    def update_counter(self):
        current_counter = int(self.counter_var.get())
        if current_counter > 0:
            self.counter_var.set(str(current_counter - 1))
            Timer(1, self.update_counter).start()


root = tk.Tk()

server_ids = ['5526400', '5526399', '5526398', '1720719', '21395315', '21268704']

for server_id in server_ids:
    frame = ServerFrame(root, server_id, refresh_interval=random.randint(55, 65))
    frame.pack()

root.mainloop()
