# READ ME
# This is the only file you need to download in-order for the editor to work. Run this with python
# and ensure all libraries are downloaded. 
# Library install command: "python -m pip install pyinstaller" (Windows) "python3 -m pip install pyinstaller" (Mac)

import subprocess
import sys
import tempfile
from pathlib import Path
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

def rgb(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


BG = rgb(20, 10, 30)
BAR = rgb(60, 30, 90)
BUTTON = rgb(45, 30, 60)
HOVER = rgb(90, 30, 125)
PANEL = rgb(40, 40, 60)
EDITOR = rgb(30, 20, 45)
TEXT = "lightgray"
ACCENT = rgb(150, 100, 200)


def empty_story():
    return {
        "start": "entrance",
        "rooms": {
            "entrance": {
                "description": "You are standing in an old entrance.",
                "exits": {},
                "items": []
            }
        },
        "items": {}
    }

class GameEditor:

    def __init__(self, root):
        self.root = root
        self.root.title("Text Adventure Game Engine")
        self.root.geometry("1000x700")
        self.root.minsize(750, 500)
        self.root.configure(bg=BG)

        self.story = empty_story()
        self.file_path = None

        self.current_type = None
        self.current_id = None
        self.refreshing = False

        self.create_menu_bar()
        self.create_layout()
        self.refresh_explorer()
        self.show_welcome()

    def make_button(self, parent, text, command, **kwargs):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=BUTTON,
            fg=TEXT,
            relief="flat",
            cursor="hand2",
            activebackground=HOVER,
            activeforeground=TEXT,
            borderwidth=0,
            font=("arial", 9),
            padx=10,
            pady=6,
            **kwargs
        )

    def make_label(self, parent, text, **kwargs):
        return tk.Label(
            parent,
            text=text,
            bg=kwargs.pop("bg", EDITOR),
            fg=TEXT,
            font=kwargs.pop("font", ("arial", 10)),
            **kwargs
        )

    def make_entry(self, parent, **kwargs):
        return tk.Entry(
            parent,
            bg=rgb(50, 40, 65),
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("arial", 10),
            **kwargs
        )
    
    def create_menu_bar(self):

        self.menu_frame = tk.Frame(self.root, bg=BAR)
        self.menu_frame.pack(side="top", fill="x")

        menus = {
            "File": [
                ("New", self.new_story),
                ("Open", self.open_story),
                ("Save", self.save_story),
                ("Save As", self.save_as),
                ("Exit", self.root.destroy)
            ],
            "Edit": [
                ("Undo", self.undo),
                ("Select All", self.select_all)
            ],
            "Story": [
                ("Add Room", self.add_room),
                ("Add Item", self.add_item),
                ("Delete Selected", self.delete_selected)
            ],
            "View": [
                ("Refresh Explorer", self.refresh_explorer)
            ],
            "Run": [
                ("Play Story", self.play_story),
                ("Validate Story", self.validate_story),
                ("Build Game (.exe)", self.build_project)
            ],
            "Help": [
                ("About", self.about)
            ]
        }

        for name, options in menus.items():

            menu = tk.Menu(
                self.menu_frame,
                tearoff=0,
                bg=PANEL,
                fg=TEXT,
                activebackground=HOVER,
                activeforeground=TEXT
            )

            for label, command in options:
                menu.add_command(label=label, command=command)

            btn = self.make_button(
                self.menu_frame,
                name,
                lambda m=menu, b=None: None
            )

            btn.configure(
                command=lambda m=menu, b=btn:
                    m.tk_popup(
                        b.winfo_rootx(),
                        b.winfo_rooty() + b.winfo_height()
                    )
            )

            btn.pack(side="left")

    def create_layout(self):

        self.main_frame = tk.Frame(self.root, bg=BG)
        self.main_frame.pack(fill="both", expand=True)

        # Explorer

        self.explorer = tk.Frame(
            self.main_frame,
            bg=PANEL,
            width=230
        )

        self.explorer.pack(side="left", fill="y")
        self.explorer.pack_propagate(False)

        self.make_label(
            self.explorer,
            "EXPLORER",
            bg=PANEL,
            font=("arial", 11, "bold")
        ).pack(anchor="w", padx=12, pady=12)

        # Rooms section

        self.make_label(
            self.explorer,
            "ROOMS",
            bg=PANEL,
            font=("arial", 9, "bold")
        ).pack(anchor="w", padx=12, pady=(5, 3))

        self.room_list = tk.Listbox(
            self.explorer,
            bg=EDITOR,
            fg=TEXT,
            selectbackground=ACCENT,
            selectforeground="white",
            borderwidth=0,
            highlightthickness=0,
            font=("arial", 10),
            height=10
        )

        self.room_list.pack(fill="x", padx=8)
        self.room_list.bind("<<ListboxSelect>>", self.select_room)

        self.make_button(
            self.explorer,
            "+ Add Room",
            self.add_room
        ).pack(fill="x", padx=8, pady=5)

        # Items section

        self.make_label(
            self.explorer,
            "ITEMS",
            bg=PANEL,
            font=("arial", 9, "bold")
        ).pack(anchor="w", padx=12, pady=(15, 3))

        self.item_list = tk.Listbox(
            self.explorer,
            bg=EDITOR,
            fg=TEXT,
            selectbackground=ACCENT,
            selectforeground="white",
            borderwidth=0,
            highlightthickness=0,
            font=("arial", 10),
            height=10
        )

        self.item_list.pack(fill="x", padx=8)
        self.item_list.bind("<<ListboxSelect>>", self.select_item)

        self.make_button(
            self.explorer,
            "+ Add Item",
            self.add_item
        ).pack(fill="x", padx=8, pady=5)

        self.make_button(
            self.explorer,
            "Delete Selected",
            self.delete_selected
        ).pack(fill="x", padx=8, pady=(15, 5))

        # Editor area

        self.workspace = tk.Frame(
            self.main_frame,
            bg=BG
        )

        self.workspace.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Editor heading

        self.editor_heading = self.make_label(
            self.workspace,
            "Welcome",
            bg=BG,
            font=("arial", 14, "bold")
        )

        self.editor_heading.pack(
            anchor="w",
            padx=20,
            pady=15
        )

        # Dynamic editor content

        self.editor_content = tk.Frame(
            self.workspace,
            bg=BG
        )

        self.editor_content.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        # Bottom status bar

        self.status = tk.Label(
            self.root,
            text="Ready",
            bg=BAR,
            fg=TEXT,
            anchor="w",
            padx=10,
            pady=5
        )

        self.status.pack(side="bottom", fill="x")

    def refresh_explorer(self):

        self.refreshing = True

        self.room_list.delete(0, tk.END)
        self.item_list.delete(0, tk.END)

        for room_id in self.story["rooms"]:
            self.room_list.insert(tk.END, room_id)

        for item_id in self.story["items"]:
            self.item_list.insert(tk.END, item_id)

        self.refreshing = False

    def select_room(self, event=None):

        if self.refreshing:
            return

        selection = self.room_list.curselection()

        if not selection:
            return

        self.save_current()

        room_id = self.room_list.get(selection[0])
        self.show_room(room_id)

    def select_item(self, event=None):

        if self.refreshing:
            return

        selection = self.item_list.curselection()

        if not selection:
            return

        self.save_current()

        item_id = self.item_list.get(selection[0])
        self.show_item(item_id)

    def clear_editor(self):

        for widget in self.editor_content.winfo_children():
            widget.destroy()

    def show_welcome(self):

        self.current_type = None
        self.current_id = None

        self.editor_heading.configure(text="Welcome")
        self.clear_editor()

        self.make_label(
            self.editor_content,
            "Text Adventure Game Editor",
            font=("arial", 18, "bold")
        ).pack(anchor="w", pady=15)

        self.make_label(
            self.editor_content,
            "Select a room or item from the Explorer to begin.",
        ).pack(anchor="w")

        self.make_label(
            self.editor_content,
            "Create rooms, connect exits, add items and build your story."
        ).pack(anchor="w", pady=5)

    def show_room(self, room_id):

        self.current_type = "room"
        self.current_id = room_id

        room = self.story["rooms"][room_id]

        self.editor_heading.configure(text=f"Room: {room_id}")
        self.clear_editor()

        # Description

        self.make_label(
            self.editor_content,
            "Description"
        ).pack(anchor="w", pady=(5, 5))

        self.description_text = tk.Text(
            self.editor_content,
            height=6,
            bg=EDITOR,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("arial", 10),
            wrap="word"
        )

        self.description_text.pack(fill="x")
        self.description_text.insert("1.0", room.get("description", ""))

        # Start room

        self.make_label(
            self.editor_content,
            "Start room"
        ).pack(anchor="w", pady=(12, 3))

        self.start_var = tk.BooleanVar(
            value=self.story["start"] == room_id
        )

        tk.Checkbutton(
            self.editor_content,
            text="Player starts in this room",
            variable=self.start_var,
            bg=BG,
            fg=TEXT,
            selectcolor=EDITOR,
            activebackground=BG,
            activeforeground=TEXT,
            command=self.set_start_room
        ).pack(anchor="w")

        # Exits

        self.make_label(
            self.editor_content,
            "Exits",
            font=("arial", 11, "bold")
        ).pack(anchor="w", pady=(15, 5))

        self.exit_list = tk.Listbox(
            self.editor_content,
            height=5,
            bg=EDITOR,
            fg=TEXT,
            selectbackground=ACCENT,
            borderwidth=0,
            highlightthickness=0
        )

        self.exit_list.pack(fill="x")

        self.refresh_exits()

        exit_buttons = tk.Frame(
            self.editor_content,
            bg=BG
        )

        exit_buttons.pack(anchor="w", pady=5)

        self.make_button(
            exit_buttons, "+ Add Exit", self.add_exit
        ).pack(side="left", padx=(0, 5))

        self.make_button(
            exit_buttons, "Edit Exit", self.edit_exit
        ).pack(side="left", padx=5)

        self.make_button(
            exit_buttons, "Remove Exit", self.remove_exit
        ).pack(side="left", padx=5)

                # Room contents

        self.make_label(
            self.editor_content,
            "Room Items",
            font=("arial", 11, "bold")
        ).pack(anchor="w", pady=(12, 5))

        # Add/remove controls FIRST
        item_controls = tk.Frame(
            self.editor_content,
            bg=BG
        )
        item_controls.pack(anchor="w", pady=5)

        self.room_item_choice = ttk.Combobox(
            item_controls,
            state="readonly",
            width=20,
            values=list(self.story["items"].keys())
        )
        self.room_item_choice.pack(side="left", padx=(0, 5))

        self.make_button(
            item_controls,
            "Add Item",
            self.add_item_to_room
        ).pack(side="left", padx=5)

        self.make_button(
            item_controls,
            "Remove Item",
            self.remove_item_from_room
        ).pack(side="left", padx=5)

        # List of items already in this room
        self.room_item_list = tk.Listbox(
            self.editor_content,
            height=4,
            bg=EDITOR,
            fg=TEXT,
            selectbackground=ACCENT,
            borderwidth=0,
            highlightthickness=0
        )
        self.room_item_list.pack(fill="x")

        self.refresh_room_items()

    def save_current(self):

        if self.current_type == "room":
            if self.current_id not in self.story["rooms"]:
                return

            room = self.story["rooms"][self.current_id]

            room["description"] = self.description_text.get(
                "1.0", "end-1c"
            )

        elif self.current_type == "item":
            if self.current_id not in self.story["items"]:
                return

            item = self.story["items"][self.current_id]

            item["name"] = self.item_name_entry.get().strip()
            item["takeable"] = self.takeable_var.get()

    def set_start_room(self):

        if self.start_var.get():
            self.story["start"] = self.current_id

            # Keep the start checkbox consistent with the model.
            # Other rooms will display unchecked when reopened.
            self.status.configure(
                text=f"Start room set to {self.current_id}"
            )

    def refresh_exits(self):

        self.exit_list.delete(0, tk.END)

        room = self.story["rooms"][self.current_id]

        for direction, exit_data in room.get("exits", {}).items():

            if isinstance(exit_data, str):
                target = exit_data
                required = None
            else:
                target = exit_data["to"]
                required = exit_data.get("requires")

            description = f"{direction} -> {target}"

            if required:
                description += f" (requires {required})"

            self.exit_list.insert(tk.END, description)

    def add_exit(self):

        self.save_current()

        if not self.story["rooms"]:
            return

        dialog = ExitDialog(self.root, self.story)

        if dialog.result is None:
            return

        direction, target, required = dialog.result

        room = self.story["rooms"][self.current_id]

        if direction in room["exits"]:
            messagebox.showerror(
                "Error", "That direction already has an exit."
            )
            return

        if required:
            room["exits"][direction] = {
                "to": target,
                "requires": required
            }
        else:
            room["exits"][direction] = target

        self.refresh_exits()

    def edit_exit(self):

        selection = self.exit_list.curselection()

        if not selection:
            return

        self.save_current()

        directions = list(
            self.story["rooms"][self.current_id]["exits"].keys()
        )

        direction = directions[selection[0]]
        old = self.story["rooms"][self.current_id]["exits"][direction]

        if isinstance(old, str):
            old_target = old
            old_required = ""
        else:
            old_target = old["to"]
            old_required = old.get("requires", "")

        dialog = ExitDialog(
            self.root,
            self.story,
            direction,
            old_target,
            old_required
        )

        if dialog.result is None:
            return

        new_direction, target, required = dialog.result

        room = self.story["rooms"][self.current_id]

        if new_direction != direction and new_direction in room["exits"]:
            messagebox.showerror(
                "Error", "That direction already exists."
            )
            return

        del room["exits"][direction]

        if required:
            room["exits"][new_direction] = {
                "to": target,
                "requires": required
            }
        else:
            room["exits"][new_direction] = target

        self.refresh_exits()

    def remove_exit(self):

        selection = self.exit_list.curselection()

        if not selection:
            return

        directions = list(
            self.story["rooms"][self.current_id]["exits"].keys()
        )

        direction = directions[selection[0]]

        del self.story["rooms"][self.current_id]["exits"][direction]

        self.refresh_exits()

    def refresh_room_items(self):

        self.room_item_list.delete(0, tk.END)

        room = self.story["rooms"][self.current_id]

        # Ensure the room has an items list
        room.setdefault("items", [])

        for item_id in room["items"]:
            name = self.story["items"].get(
                item_id, {}
            ).get("name", item_id)

            self.room_item_list.insert(tk.END, name)

        self.room_item_choice["values"] = list(
            self.story["items"].keys()
        )

    def add_item_to_room(self):

        item_id = self.room_item_choice.get()

        if not item_id:
            return

        items = self.story["rooms"][self.current_id]["items"]

        if item_id not in items:
            items.append(item_id)

        self.refresh_room_items()

    def remove_item_from_room(self):

        selection = self.room_item_list.curselection()

        if not selection:
            return

        items = self.story["rooms"][self.current_id]["items"]

        del items[selection[0]]

        self.refresh_room_items()

    def show_item(self, item_id):

        self.current_type = "item"
        self.current_id = item_id

        item = self.story["items"][item_id]

        self.editor_heading.configure(text=f"Item: {item_id}")
        self.clear_editor()

        self.make_label(
            self.editor_content,
            "Item Name"
        ).pack(anchor="w", pady=(5, 5))

        self.item_name_entry = self.make_entry(
            self.editor_content
        )

        self.item_name_entry.pack(fill="x")
        self.item_name_entry.insert(
            0, item.get("name", item_id)
        )

        self.takeable_var = tk.BooleanVar(
            value=item.get("takeable", False)
        )

        tk.Checkbutton(
            self.editor_content,
            text="Player can take this item",
            variable=self.takeable_var,
            bg=BG,
            fg=TEXT,
            selectcolor=EDITOR,
            activebackground=BG,
            activeforeground=TEXT
        ).pack(anchor="w", pady=10)

    def add_room(self):

        self.save_current()

        room_id = simpledialog.askstring(
            "New Room",
            "Enter a unique room ID:",
            parent=self.root
        )

        if not room_id:
            return

        room_id = room_id.strip().lower().replace(" ", "_")

        if room_id in self.story["rooms"]:
            messagebox.showerror(
                "Error", "That room already exists."
            )
            return

        self.story["rooms"][room_id] = {
            "description": "New room description.",
            "exits": {},
            "items": []
        }

        self.refresh_explorer()
        self.select_room_by_id(room_id)

    def add_item(self):

        self.save_current()

        item_id = simpledialog.askstring(
            "New Item",
            "Enter a unique item ID:",
            parent=self.root
        )

        if not item_id:
            return

        item_id = item_id.strip().lower().replace(" ", "_")

        if item_id in self.story["items"]:
            messagebox.showerror(
                "Error", "That item already exists."
            )
            return

        self.story["items"][item_id] = {
            "name": item_id.replace("_", " ").title(),
            "takeable": True
        }

        self.refresh_explorer()
        self.select_item_by_id(item_id)

    def delete_selected(self):

        self.save_current()

        if self.current_type == "room":

            room_id = self.current_id

            if len(self.story["rooms"]) <= 1:
                messagebox.showerror(
                    "Error", "You must have at least one room."
                )
                return

            if not messagebox.askyesno(
                "Delete Room",
                f"Delete room '{room_id}'?"
            ):
                return

            del self.story["rooms"][room_id]

            # Remove exits leading to the deleted room
            for room in self.story["rooms"].values():
                exits = room.get("exits", {})

                for direction in list(exits.keys()):
                    exit_data = exits[direction]

                    target = (
                        exit_data if isinstance(exit_data, str)
                        else exit_data.get("to")
                    )

                    if target == room_id:
                        del exits[direction]

            if self.story["start"] == room_id:
                self.story["start"] = next(
                    iter(self.story["rooms"])
                )

        elif self.current_type == "item":

            item_id = self.current_id

            if not messagebox.askyesno(
                "Delete Item",
                f"Delete item '{item_id}'?"
            ):
                return

            del self.story["items"][item_id]

            # Remove the item from every room
            for room in self.story["rooms"].values():
                if item_id in room["items"]:
                    room["items"].remove(item_id)

            # Remove exit requirements referencing the item
            for room in self.story["rooms"].values():
                for exit_data in room.get("exits", {}).values():
                    if isinstance(exit_data, dict):
                        if exit_data.get("requires") == item_id:
                            del exit_data["requires"]

        else:
            return

        self.current_type = None
        self.current_id = None

        self.refresh_explorer()
        self.show_welcome()

    def select_room_by_id(self, room_id):

        self.room_list.selection_clear(0, tk.END)

        index = list(self.story["rooms"]).index(room_id)

        self.room_list.selection_set(index)
        self.room_list.see(index)
        self.show_room(room_id)

    def select_item_by_id(self, item_id):

        self.item_list.selection_clear(0, tk.END)

        index = list(self.story["items"]).index(item_id)

        self.item_list.selection_set(index)
        self.item_list.see(index)
        self.show_item(item_id)

    def new_story(self):

        self.save_current()

        if not messagebox.askyesno(
            "New Story",
            "Create a new story? Unsaved changes will be lost."
        ):
            return

        self.story = empty_story()
        self.file_path = None

        self.refresh_explorer()
        self.show_welcome()

    def open_story(self):

        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                story = json.load(file)

            errors = self.check_story(story)

            if errors:
                messagebox.showerror(
                    "Invalid Story",
                    "\n".join(errors)
                )
                return

            self.story = story
            self.file_path = path

            self.current_type = None
            self.current_id = None

            self.refresh_explorer()
            self.show_welcome()

            self.status.configure(text=f"Opened: {path}")

        except (OSError, json.JSONDecodeError) as error:
            messagebox.showerror("Open Error", str(error))

    def save_story(self):

        self.save_current()

        if self.file_path is None:
            self.save_as()
            return

        self.write_story(self.file_path)

    def save_as(self):

        self.save_current()

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )

        if not path:
            return

        self.file_path = path
        self.write_story(path)

    def write_story(self, path):

        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(
                    self.story,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            self.status.configure(text=f"Saved: {path}")

        except OSError as error:
            messagebox.showerror("Save Error", str(error))

    def check_story(self, story):

        errors = []

        if not isinstance(story, dict):
            return ["Story must be a JSON object."]

        if "start" not in story:
            errors.append("Missing start room.")

        if not isinstance(story.get("rooms"), dict):
            errors.append("Rooms must be an object.")
            return errors

        if not isinstance(story.get("items", {}), dict):
            errors.append("Items must be an object.")
            return errors

        rooms = story["rooms"]
        items = story.get("items", {})

        if not rooms:
            errors.append("Story has no rooms.")

        if story.get("start") not in rooms:
            errors.append("Start room does not exist.")

        for room_id, room in rooms.items():

            if not isinstance(room, dict):
                errors.append(f"Room '{room_id}' must be an object.")
                continue

            if "description" not in room:
                errors.append(f"Room '{room_id}' has no description.")

            if not isinstance(room.get("exits", {}), dict):
                errors.append(f"Room '{room_id}' has invalid exits.")
                continue

            if not isinstance(room.get("items", []), list):
                errors.append(f"Room '{room_id}' has invalid items.")
                continue

            for direction, exit_data in room.get("exits", {}).items():

                if isinstance(exit_data, str):
                    target = exit_data
                elif isinstance(exit_data, dict):
                    target = exit_data.get("to")
                else:
                    errors.append(
                        f"Room '{room_id}': invalid exit '{direction}'."
                    )
                    continue

                if target not in rooms:
                    errors.append(
                        f"Room '{room_id}': unknown destination '{target}'."
                    )

                if isinstance(exit_data, dict):
                    required = exit_data.get("requires")

                    if required and required not in items:
                        errors.append(
                            f"Room '{room_id}': unknown required item '{required}'."
                        )

            for item_id in room.get("items", []):
                if item_id not in items:
                    errors.append(
                        f"Room '{room_id}': unknown item '{item_id}'."
                    )

        return errors

    def validate_story(self):

        self.save_current()

        errors = self.check_story(self.story)

        if errors:
            messagebox.showerror(
                "Validation Failed",
                "\n".join(errors)
            )
            self.status.configure(text="Validation failed.")
        else:
            messagebox.showinfo(
                "Validation",
                "Your story is valid!"
            )
            self.status.configure(text="Story validated successfully.")

    def play_story(self):

        self.save_current()

        errors = self.check_story(self.story)

        if errors:
            messagebox.showerror(
                "Cannot Play",
                "Fix these errors first:\n\n" + "\n".join(errors)
            )
            return

        Playtest(self.root, self.story)

    def undo(self):
        messagebox.showinfo(
            "Undo",
            "Undo history has not been implemented yet."
        )

    def select_all(self):

        widget = self.root.focus_get()

        if isinstance(widget, (tk.Entry, tk.Text)):
            widget.event_generate("<<SelectAll>>")

    def about(self):

        messagebox.showinfo(
            "About",
            "Text Adventure Game Engine\n"
            "A simple visual editor for JSON-based text adventures."
        )
    def build_project(self):

        # Save any changes currently being made
        self.save_current()

        # Check that the story is valid
        errors = self.check_story(self.story)

        if errors:
            messagebox.showerror(
                "Build Failed",
                "Fix these errors before building:\n\n"
                + "\n".join(errors)
            )
            return

        # Ask where to save the executable
        output_path = filedialog.asksaveasfilename(
            title="Build Game",
            defaultextension=".exe",
            filetypes=[("Windows Executable", "*.exe")],
            initialfile="MyTextAdventure.exe"
        )

        if not output_path:
            return

        output_path = Path(output_path)

        if output_path.suffix.lower() != ".exe":
            output_path = output_path.with_suffix(".exe")

        # Convert the story into JSON text
        story_json = json.dumps(
            self.story,
            ensure_ascii=False
        )

        # Standalone game source
        runtime_code = r'''
import json

STORY = json.loads(__STORY_JSON__)

state = {
    "room": STORY["start"],
    "inventory": [],
    "room_items": {
        room_id: list(room.get("items", []))
        for room_id, room in STORY["rooms"].items()
    }
}


def describe_room():

    room = STORY["rooms"][state["room"]]

    print("\n" + room.get("description", ""))

    visible = state["room_items"][state["room"]]

    if visible:
        names = [
            STORY["items"][item_id].get("name", item_id)
            for item_id in visible
        ]

        print("You see:", ", ".join(names))

    exits = room.get("exits", {})

    if exits:
        print("Exits:", ", ".join(exits.keys()))


def find_item(available, noun):

    for item_id in available:

        item = STORY["items"][item_id]

        name = item.get("name", item_id).lower()

        if (
            noun == item_id.lower()
            or noun == name
            or noun in name.split()
        ):
            return item_id

    return None


def go(direction):

    room = STORY["rooms"][state["room"]]

    exit_data = room.get("exits", {}).get(direction)

    if exit_data is None:
        print("You can't go that way.")
        return

    if isinstance(exit_data, str):
        target = exit_data
        required = None
    else:
        target = exit_data["to"]
        required = exit_data.get("requires")

    if required and required not in state["inventory"]:
        print("The way is locked.")
        return

    state["room"] = target

    describe_room()


def take(noun):

    available = state["room_items"][state["room"]]

    item_id = find_item(available, noun)

    if item_id is None:
        print("You don't see that here.")
        return

    if not STORY["items"][item_id].get("takeable", False):
        print("You can't take that.")
        return

    available.remove(item_id)
    state["inventory"].append(item_id)

    print("Taken:", STORY["items"][item_id]["name"])


def drop(noun):

    inventory = state["inventory"]

    item_id = find_item(inventory, noun)

    if item_id is None:
        print("You aren't carrying that.")
        return

    inventory.remove(item_id)

    state["room_items"][state["room"]].append(item_id)

    print("Dropped:", STORY["items"][item_id]["name"])


def handle_command(command):

    words = command.lower().split()

    if not words:
        return True

    verb = words[0]
    noun = " ".join(words[1:])

    aliases = {
        "n": "north",
        "s": "south",
        "e": "east",
        "w": "west",
        "u": "up",
        "d": "down",
        "i": "inventory",
        "inv": "inventory",
        "get": "take",
        "grab": "take",
        "walk": "go"
    }

    verb = aliases.get(verb, verb)

    if verb in ("north", "south", "east", "west", "up", "down"):
        noun = verb
        verb = "go"

    if verb == "look":
        describe_room()

    elif verb == "inventory":

        names = [
            STORY["items"][i].get("name", i)
            for i in state["inventory"]
        ]

        print(
            "Carrying: " + ", ".join(names)
            if names else "You're carrying nothing."
        )

    elif verb == "go":
        go(noun)

    elif verb == "take":
        take(noun)

    elif verb == "drop":
        drop(noun)

    elif verb == "help":
        print("Commands: look, go, north, south, east, west, up, down, take, drop, inventory, quit")

    elif verb == "quit":
        print("Thanks for playing!")
        return False

    else:
        print("I don't understand that command.")

    return True


def main():

    print("=" * 40)
    print("       TEXT ADVENTURE")
    print("=" * 40)

    describe_room()

    running = True

    while running:

        try:
            command = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            break

        running = handle_command(command)

    print("\nGame ended.")


if __name__ == "__main__":
    main()
'''

        # Insert the story directly into the game
        runtime_code = runtime_code.replace(
            "__STORY_JSON__",
            repr(story_json)
        )

        self.status.configure(text="Building game...")

        try:

            # Temporary working directory for PyInstaller
            with tempfile.TemporaryDirectory() as temp:

                temp_dir = Path(temp)

                script_path = temp_dir / "game_runtime.py"

                script_path.write_text(
                    runtime_code,
                    encoding="utf-8"
                )

                command = [
                    sys.executable,
                    "-m",
                    "PyInstaller",
                    "--noconfirm",
                    "--clean",
                    "--onefile",
                    "--console",
                    "--name",
                    output_path.stem,
                    "--distpath",
                    str(output_path.parent),
                    "--workpath",
                    str(temp_dir / "build"),
                    "--specpath",
                    str(temp_dir),
                    str(script_path)
                ]

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:

                    messagebox.showerror(
                        "Build Failed",
                        result.stderr[-4000:]
                        or result.stdout[-4000:]
                    )

                    self.status.configure(text="Build failed.")
                    return

            self.status.configure(text="Build completed successfully!")

            messagebox.showinfo(
                "Build Complete",
                f"Your game was successfully built!\n\n"
                f"Location:\n{output_path}"
            )

        except Exception as error:

            self.status.configure(text="Build failed.")

            messagebox.showerror(
                "Build Error",
                str(error)
            )

class ExitDialog(tk.Toplevel):

    def __init__(
        self,
        parent,
        story,
        direction="",
        target="",
        required=""
    ):

        super().__init__(parent)

        self.title("Exit Editor")
        self.geometry("300x260")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.result = None
        self.story = story

        self.transient(parent)
        self.grab_set()

        self.direction_var = tk.StringVar(value=direction)
        self.target_var = tk.StringVar(value=target)
        self.required_var = tk.StringVar(value=required)

        directions = [
            "north", "south", "east", "west", "up", "down"
        ]

        tk.Label(
            self,
            text="Direction",
            bg=BG,
            fg=TEXT
        ).pack(anchor="w", padx=15, pady=(10, 3))

        ttk.Combobox(
            self,
            textvariable=self.direction_var,
            values=directions,
            state="readonly"
        ).pack(fill="x", padx=15)

        tk.Label(
            self,
            text="Destination Room",
            bg=BG,
            fg=TEXT
        ).pack(anchor="w", padx=15, pady=(10, 3))

        ttk.Combobox(
            self,
            textvariable=self.target_var,
            values=list(story["rooms"].keys()),
            state="readonly"
        ).pack(fill="x", padx=15)

        tk.Label(
            self,
            text="Required Item (optional)",
            bg=BG,
            fg=TEXT
        ).pack(anchor="w", padx=15, pady=(10, 3))

        ttk.Combobox(
            self,
            textvariable=self.required_var,
            values=[""] + list(story["items"].keys()),
            state="readonly"
        ).pack(fill="x", padx=15)

        button_frame = tk.Frame(self, bg=BG)
        button_frame.pack(pady=15)

        tk.Button(
            button_frame,
            text="Save",
            command=self.save,
            bg=BUTTON,
            fg=TEXT,
            relief="flat",
            padx=15
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            bg=BUTTON,
            fg=TEXT,
            relief="flat",
            padx=15
        ).pack(side="left", padx=5)

        self.wait_window()

    def save(self):

        direction = self.direction_var.get()
        target = self.target_var.get()
        required = self.required_var.get()

        if not direction or not target:
            messagebox.showerror(
                "Error",
                "Select a direction and destination.",
                parent=self
            )
            return

        self.result = (direction, target, required)
        self.destroy()

class Playtest(tk.Toplevel):

    def __init__(self, parent, story):

        super().__init__(parent)

        self.title("Story Playtest")
        self.geometry("650x450")
        self.configure(bg=BG)

        # Make a separate copy so playtesting
        # doesn't change the editor's story.
        self.story = json.loads(json.dumps(story))

        self.state = {
            "room": self.story["start"],
            "inventory": [],
            "room_items": {
                rid: list(room.get("items", []))
                for rid, room in self.story["rooms"].items()
            }
        }

        self.output = tk.Text(
            self,
            bg=EDITOR,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            wrap="word",
            state="disabled"
        )

        self.output.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.command_entry = tk.Entry(
            self,
            bg=PANEL,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("arial", 11)
        )

        self.command_entry.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        self.command_entry.bind("<Return>", self.handle_command)
        self.command_entry.focus_set()

        self.write(self.describe_room())

    def write(self, text):

        self.output.configure(state="normal")
        self.output.insert(tk.END, text + "\n\n")
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def describe_room(self):

        room = self.story["rooms"][self.state["room"]]

        lines = [room.get("description", "")]

        visible = self.state["room_items"][self.state["room"]]

        if visible:
            names = [
                self.story["items"][i]["name"]
                for i in visible
            ]

            lines.append("You see: " + ", ".join(names))

        exits = room.get("exits", {})

        if exits:
            lines.append("Exits: " + ", ".join(exits.keys()))

        return "\n".join(lines)

    def handle_command(self, event=None):

        raw = self.command_entry.get().strip().lower()
        self.command_entry.delete(0, tk.END)

        if not raw:
            return

        words = raw.split()
        verb = words[0]
        noun = " ".join(words[1:])

        aliases = {
            "n": "north",
            "s": "south",
            "e": "east",
            "w": "west",
            "u": "up",
            "d": "down",
            "inv": "inventory",
            "i": "inventory",
            "get": "take",
            "grab": "take",
            "walk": "go"
        }

        verb = aliases.get(verb, verb)

        if verb in (
            "north", "south", "east",
            "west", "up", "down"
        ):
            noun = verb
            verb = "go"

        if verb == "look":
            self.write(self.describe_room())

        elif verb == "inventory":

            names = [
                self.story["items"][i]["name"]
                for i in self.state["inventory"]
            ]

            self.write(
                "Carrying: " + ", ".join(names)
                if names else "You're carrying nothing."
            )

        elif verb == "go":
            self.go(noun)

        elif verb == "take":
            self.take(noun)

        elif verb == "drop":
            self.drop(noun)

        elif verb == "quit":
            self.destroy()

        else:
            self.write("I don't understand that command.")

    def find_item(self, available, noun):

        for item_id in available:

            item = self.story["items"][item_id]
            name = item.get("name", item_id).lower()

            if (
                noun == item_id.lower()
                or noun == name
                or noun in name.split()
            ):
                return item_id

        return None

    def go(self, direction):

        room = self.story["rooms"][self.state["room"]]
        exit_data = room.get("exits", {}).get(direction)

        if exit_data is None:
            self.write("You can't go that way.")
            return

        if isinstance(exit_data, str):
            target = exit_data
            required = None
        else:
            target = exit_data["to"]
            required = exit_data.get("requires")

        if required and required not in self.state["inventory"]:
            self.write("The way is locked.")
            return

        self.state["room"] = target
        self.write(self.describe_room())

    def take(self, noun):

        available = self.state["room_items"][self.state["room"]]
        item_id = self.find_item(available, noun)

        if item_id is None:
            self.write(f"I don't see a {noun} here.")
            return

        if not self.story["items"][item_id].get("takeable", False):
            self.write("You can't take that.")
            return

        available.remove(item_id)
        self.state["inventory"].append(item_id)

        self.write(
            "Taken: " + self.story["items"][item_id]["name"]
        )

    def drop(self, noun):

        inventory = self.state["inventory"]
        item_id = self.find_item(inventory, noun)

        if item_id is None:
            self.write(f"You aren't carrying a {noun}.")
            return

        inventory.remove(item_id)
        self.state["room_items"][self.state["room"]].append(item_id)

        self.write(
            "Dropped: " + self.story["items"][item_id]["name"]
        )


app = tk.Tk()
editor = GameEditor(app)
app.mainloop()
