# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import subprocess
import threading
import time

class TrafficOptimizerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Traffic Flow Optimizer")

        self.method_label = ttk.Label(master, text="Optimization Method:")
        self.method_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.method_var = tk.StringVar(master)
        methods = ['fc', 'lqf', 'search', 'qlearning', 'adaptive']
        self.method_var.set(methods[0])  # Default value
        self.method_dropdown = ttk.Combobox(master, textvariable=self.method_var, values=methods)
        self.method_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.episodes_label = ttk.Label(master, text="Number of Episodes:")
        self.episodes_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.episodes_entry = ttk.Entry(master)
        self.episodes_entry.insert(0, "1")  # Default value
        self.episodes_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.render_var = tk.BooleanVar(master)
        self.render_check = ttk.Checkbutton(master, text="Render Simulation", variable=self.render_var)
        self.render_check.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.merging_var = tk.BooleanVar(master)
        self.merging_check = ttk.Checkbutton(master, text="Enable Merging", variable=self.merging_var)
        self.merging_check.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.run_button = ttk.Button(master, text="Run Optimizer", command=self.run_optimizer)
        self.run_button.grid(row=4, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

        self.output_label = ttk.Label(master, text="Output:")
        self.output_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")

        self.output_text = tk.Text(master, height=10, width=60)
        self.output_text.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.output_text.config(state=tk.DISABLED)  # Make it read-only

        self.image_label = ttk.Label(master, text="Simulation Output Image:")
        self.image_label.grid(row=7, column=0, padx=5, pady=5, sticky="w")

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(6, weight=1)
        master.grid_rowconfigure(8, weight=1)

        self.is_running = False

    def run_optimizer(self):
        if self.is_running:
            messagebox.showinfo("Info", "Optimizer is already running.")
            return

        method = self.method_var.get()
        try:
            episodes = int(self.episodes_entry.get())
            if episodes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Number of episodes must be a positive integer.")
            return

        render = self.render_var.get()
        enable_merging = self.merging_var.get()

        command = [
            "python",
            "main.py",
            "-m",
            method,
            "-e",
            str(episodes),
        ]
        if render:
            command.append("-r")
        if enable_merging:
            command.append("--enable_merging")

        self.is_running = True
        self.run_button.config(state=tk.DISABLED, text="Running...")
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.ax.clear()
        self.canvas.draw()

        threading.Thread(target=self._run_subprocess, args=(command,)).start()

    def _run_subprocess(self, command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self._update_output(output.strip())
                if "simulation_output.png" in output:
                    self._load_image("simulation_output.png")

        stderr_output = process.stderr.read()
        if stderr_output:
            self._update_output(f"Error: {stderr_output.strip()}")

        self.is_running = False
        self.master.after(0, self.run_button.config, {"state": tk.NORMAL, "text": "Run Optimizer"})

    def _update_output(self, message):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def _load_image(self, image_path):
        try:
            img = plt.imread(image_path)
            self.ax.clear()
            self.ax.imshow(img)
            self.ax.axis('off')
            self.canvas.draw()
        except FileNotFoundError:
            self._update_output(f"Error: Image file not found: {image_path}")
        except Exception as e:
            self._update_output(f"Error loading image: {e}")

def main():
    root = tk.Tk()
    gui = TrafficOptimizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()