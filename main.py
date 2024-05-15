import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import json
import os
import requests

CONFIG_FILE = "programs_config.json"


class WInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("WInstaller")

        self.label = tk.Label(root, text="WInstaller", font=("Arial", 14))
        self.label.pack(pady=10)

        self.install_button = tk.Button(
            root,
            text="Install Programs",
            command=self.install_programs,
            font=("Arial", 12),
        )
        self.install_button.pack(pady=10)

        self.add_button = tk.Button(
            root, text="Add Program", command=self.add_program, font=("Arial", 12)
        )
        self.add_button.pack(pady=10)

        self.progress = ttk.Progressbar(
            root, orient="horizontal", length=300, mode="determinate"
        )
        self.progress.pack(pady=10)

        self.log_area = tk.Text(root, height=10, width=50, state="disabled")
        self.log_area.pack(pady=10)

        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.programs_to_install = json.load(f)
        else:
            self.programs_to_install = []

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.programs_to_install, f, indent=4)

    def log_message(self, message):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.config(state="disabled")
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def download_file(self, url, local_filename):
        try:
            self.log_message(f"Downloading {local_filename}...")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            self.log_message(f"Downloaded {local_filename}.")
            return local_filename
        except requests.RequestException as e:
            self.log_message(f"Failed to download {local_filename}: {e}")
            return None

    def install_programs(self):
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.programs_to_install)
        for program in self.programs_to_install:
            installer_path = self.download_file(program["url"], program["filename"])
            if installer_path:
                try:
                    self.log_message(f"Installing {program['name']}...")
                    subprocess.run(
                        program["command"].format(installer=installer_path),
                        shell=True,
                        check=True,
                    )
                    self.log_message(f"{program['name']} installed successfully.")
                except subprocess.CalledProcessError as e:
                    self.log_message(f"Failed to install {program['name']}: {e}")
            self.progress["value"] += 1

    def add_program(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Program")

        tk.Label(add_window, text="Program Name:").pack(pady=5)
        name_entry = tk.Entry(add_window)
        name_entry.pack(pady=5)

        tk.Label(add_window, text="Download URL:").pack(pady=5)
        url_entry = tk.Entry(add_window, width=50)
        url_entry.pack(pady=5)

        tk.Label(add_window, text="Installer Filename:").pack(pady=5)
        filename_entry = tk.Entry(add_window)
        filename_entry.pack(pady=5)

        tk.Label(
            add_window, text="Installation Command (use {installer} for path):"
        ).pack(pady=5)
        command_entry = tk.Entry(add_window, width=50)
        command_entry.pack(pady=5)

        def save_program():
            name = name_entry.get()
            url = url_entry.get()
            filename = filename_entry.get()
            command = command_entry.get()
            if name and url and filename and command:
                self.programs_to_install.append(
                    {"name": name, "url": url, "filename": filename, "command": command}
                )
                self.save_config()
                messagebox.showinfo("Success", f"{name} added successfully.")
                add_window.destroy()
            else:
                messagebox.showwarning("Input Error", "All fields are required.")

        save_button = tk.Button(add_window, text="Save", command=save_program)
        save_button.pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = WInstaller(root)
    root.geometry("500x450")
    root.mainloop()
