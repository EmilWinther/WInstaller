import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import json
import os
import requests
import threading

CONFIG_FILE = "programs_config.json"
LOGO_FILE = "WInstallerLogo.png"


class WInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("WInstaller")
        self.cancel_installation = False

        # Set the application icon
        if os.path.exists(LOGO_FILE):
            self.root.iconphoto(True, tk.PhotoImage(file=LOGO_FILE))

        self.label = tk.Label(root, text="WInstaller", font=("Arial", 14))
        self.label.pack(pady=10)

        self.program_frame = tk.Frame(root)
        self.program_frame.pack(pady=10)

        self.check_all_button = tk.Button(
            root,
            text="Check All",
            command=self.check_all,
            font=("Arial", 12),
        )
        self.check_all_button.pack(pady=5)

        self.add_button = tk.Button(
            root, text="Add Program", command=self.add_program, font=("Arial", 12)
        )
        self.add_button.pack(pady=5)

        self.progress = ttk.Progressbar(
            root, orient="horizontal", length=300, mode="determinate"
        )
        self.progress.pack(pady=10)

        self.install_button = tk.Button(
            root,
            text="Install Programs",
            command=self.start_installation_thread,
            font=("Arial", 12),
        )
        self.install_button.pack(pady=5)

        self.cancel_button = tk.Button(
            root,
            text="Cancel Installation",
            command=self.cancel_install,
            font=("Arial", 12),
        )
        self.cancel_button.pack(pady=5)

        self.log_area = tk.Text(root, height=10, width=50, state="disabled")
        self.log_area.pack(pady=10)

        self.load_config()
        self.create_checkboxes()

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
                        if self.cancel_installation:
                            self.log_message("Download cancelled.")
                            return None
                        f.write(chunk)
            self.log_message(f"Downloaded {local_filename}.")
            return local_filename
        except requests.RequestException as e:
            self.log_message(f"Failed to download {local_filename}: {e}")
            return None

    def install_programs(self):
        selected_programs = [
            program
            for program, var in zip(self.programs_to_install, self.program_vars)
            if var.get()
        ]
        if not selected_programs:
            messagebox.showwarning(
                "No Selection", "No programs selected for installation."
            )
            return

        self.progress["value"] = 0
        self.progress["maximum"] = len(selected_programs)
        self.cancel_installation = False
        for program in selected_programs:
            if self.cancel_installation:
                self.log_message("Installation cancelled.")
                break

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

    def create_checkboxes(self):
        for widget in self.program_frame.winfo_children():
            widget.destroy()

        self.program_vars = []
        for idx, program in enumerate(self.programs_to_install):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(
                self.program_frame,
                text=program["name"],
                variable=var,
                font=("Arial", 12),
            )
            chk.grid(row=idx, column=0, sticky="w")
            self.program_vars.append(var)

            edit_button = tk.Button(
                self.program_frame,
                text="Edit",
                command=lambda idx=idx: self.edit_program(idx),
            )
            edit_button.grid(row=idx, column=1)

            delete_button = tk.Button(
                self.program_frame,
                text="Delete",
                command=lambda idx=idx: self.delete_program(idx),
            )
            delete_button.grid(row=idx, column=2)

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
                self.create_checkboxes()
            else:
                messagebox.showwarning("Input Error", "All fields are required.")

        save_button = tk.Button(add_window, text="Save", command=save_program)
        save_button.pack(pady=10)

    def edit_program(self, idx):
        program = self.programs_to_install[idx]
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit {program['name']}")

        tk.Label(edit_window, text="Program Name:").pack(pady=5)
        name_entry = tk.Entry(edit_window)
        name_entry.insert(0, program["name"])
        name_entry.pack(pady=5)

        tk.Label(edit_window, text="Download URL:").pack(pady=5)
        url_entry = tk.Entry(edit_window, width=50)
        url_entry.insert(0, program["url"])
        url_entry.pack(pady=5)

        tk.Label(edit_window, text="Installer Filename:").pack(pady=5)
        filename_entry = tk.Entry(edit_window)
        filename_entry.insert(0, program["filename"])
        filename_entry.pack(pady=5)

        tk.Label(
            edit_window, text="Installation Command (use {installer} for path):"
        ).pack(pady=5)
        command_entry = tk.Entry(edit_window, width=50)
        command_entry.insert(0, program["command"])
        command_entry.pack(pady=5)

        def save_edits():
            program["name"] = name_entry.get()
            program["url"] = url_entry.get()
            program["filename"] = filename_entry.get()
            program["command"] = command_entry.get()
            self.save_config()
            messagebox.showinfo("Success", f"{program['name']} updated successfully.")
            edit_window.destroy()
            self.create_checkboxes()

        save_button = tk.Button(edit_window, text="Save", command=save_edits)
        save_button.pack(pady=10)

    def delete_program(self, idx):
        program_name = self.programs_to_install[idx]["name"]
        if messagebox.askyesno(
            "Delete Program", f"Are you sure you want to delete {program_name}?"
        ):
            del self.programs_to_install[idx]
            self.save_config()
            messagebox.showinfo("Deleted", f"{program_name} has been deleted.")
            self.create_checkboxes()

    def cancel_install(self):
        self.cancel_installation = True

    def check_all(self):
        for var in self.program_vars:
            var.set(not var.get())

    def start_installation_thread(self):
        install_thread = threading.Thread(target=self.install_programs)
        install_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = WInstaller(root)
    root.geometry("500x600")
    root.mainloop()