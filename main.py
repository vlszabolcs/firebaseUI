import tkinter as tk
from tkinter import messagebox, ttk
import firebase_admin
from firebase_admin import credentials, db
import time
import threading


def read_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            name, value = line.strip().split('=')
            config[name] = value
    return config

config = read_config('conf.txt')
databaseURL = config.get('databaseURL')
certPath = config.get('certPath')

# Firebase Admin SDK inicializálása
cred = credentials.Certificate("coffeegg-a4840-firebase-adminsdk-bse6a-91727ff1f3.json")  # Szolgáltatási fiók kulcsfájl
firebase_admin.initialize_app(cred, {
    "databaseURL": databaseURL  # RTDB URL
})


# Funkciók a Firebase kezeléséhez
def list_users():
    users_ref = db.reference("users")
    users = users_ref.get()
    return users

def add_user(user_id, name, credit=0, loan=False):
    users_ref = db.reference("users")
    users_ref.child(user_id).set({
        "name": name,
        "credit": credit,
        "loan": loan,
        "update": int(time.time())  # Unix timestamp
    })

    # Log the add user action
    log(user_id, action=20, remaining_credit=credit)

def update_user(user_id, updates):
    user_ref = db.reference(f"users/{user_id}")
    updates["update"] = int(time.time())  # Frissítési idő bélyegző
    user_ref.update(updates)

def delete_user(user_id):
    user_ref = db.reference(f"users/{user_id}")
    user_data = user_ref.get()  # Fetch user data before deletion
    if user_data:
        # Log the remove user action
        log(user_id, action=21, remaining_credit=user_data.get("credit", 0))
        user_ref.delete()

def log(user_id, action, remaining_credit):
    """Log an action to the /Log table in Firebase."""
    log_ref = db.reference("Log")
    log_entry = {
        "action": action,  # Action code
        "remainingCredit": remaining_credit,
        "userID": user_id
    }
    log_ref.child(str(int(time.time()))).set(log_entry)

# Tkinter GUI megvalósítása
def refresh_users():
    for item in tree.get_children():
        tree.delete(item)

    users = list_users()
    if users:
        sorted_users = sorted(users.items(), key=lambda x: x[1]["name"])
        for user_id, user_data in sorted_users:
            tree.insert("", "end", iid=user_id, values=(
                user_id, user_data["name"], user_data["credit"], "0", "Report", "Igen" if user_data["loan"] else "Nem"
            ))
    else:
        messagebox.showinfo("Információ", "Nincsenek felhasználók a rendszerben.")

def save_changes():
    for item in tree.get_children():
        user_id = tree.item(item, "values")[0]
        new_values = tree.item(item, "values")

        # Fetch the current values from the database
        user_ref = db.reference(f"users/{user_id}")
        current_values = user_ref.get()

        # Prepare updates only for changed fields
        updates = {}
        if new_values[1] != current_values["name"]:
            updates["name"] = new_values[1]
        if int(new_values[2]) != current_values["credit"]:
            updates["credit"] = int(new_values[2])

            # Log the credit change
            log(user_id, action=10, remaining_credit=int(new_values[2]))

        if (new_values[5] == "Igen") != current_values["loan"]:
            updates["loan"] = new_values[5] == "Igen"

        # Update the database only if there are changes
        if updates:
            updates["update"] = int(time.time())  # Add a timestamp for the update
            user_ref.update(updates)

    messagebox.showinfo("Mentés", "A módosítások mentésre kerültek.")

# Tkinter főablak
root = tk.Tk()
root.title("GG Coffee")
root.geometry("700x400")
root.minsize(700, 400)

# Stílus beállítása a Treeview-hez
style = ttk.Style()
style.configure("Treeview", rowheight=25)  # Sor magasságának beállítása
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))  # Fejléc stílusa
style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])  # Rács terület
style.map("Treeview", background=[("selected", "green")])  # Kijelölt sor színe

# Felhasználók táblázata
tree = ttk.Treeview(root, columns=("ID", "Név", "Kredit", "Hozzáadás", "Report", "Kölcsön"), show="headings", selectmode="browse")
tree.heading("ID", text="ID")
tree.heading("Név", text="Név")
tree.heading("Kredit", text="Kredit")
tree.heading("Hozzáadás", text="Hozzáadás")  # Új oszlop
tree.heading("Report", text="Report")
tree.heading("Kölcsön", text="Kölcsön")

tree.column("ID", minwidth=80, width=80)
tree.column("Név", minwidth=200, width=100)
tree.column("Kredit", minwidth=80, width=80)
tree.column("Hozzáadás", minwidth=80, width=80)  # Új oszlop szélessége
tree.column("Report", minwidth=80, width=80)
tree.column("Kölcsön", minwidth=20, width=80)

tree.pack(fill=tk.BOTH, expand=True)

def validate_numeric_input(P):
    if P == "" or P == "-" or P.isdigit() or (P.startswith("-") and P[1:].isdigit()):
        return True
    return False

vcmd = (root.register(validate_numeric_input), '%P')

def on_double_click(event):
    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)

    if not item or column == "#0":
        return

    column_index = int(column[1:]) - 1
    column_name = tree["columns"][column_index]

    if column_name == "Kredit":
        # Kredit oszlop nem módosítható
        return

    def save_edit(event):
        new_value = entry.get()
        tree.set(item, column_name, new_value)

        # Update Firebase
        user_id = tree.item(item, "values")[0]
        user_ref = db.reference(f"users/{user_id}")

        # Update the corresponding field in Firebase
        if column_name == "Név":
            user_ref.update({"name": new_value, "update": int(time.time())})
        elif column_name == "Hozzáadás":
            try:
                addition = int(new_value)
                current_credit = int(tree.set(item, "Kredit"))
                updated_credit = current_credit + addition

                if updated_credit < 0:
                    messagebox.showerror("Hiba", "A kredit értéke nem lehet negatív!")
                    entry.destroy()
                    return

                # Update the Kredit oszlop értéke
                tree.set(item, "Kredit", updated_credit)
                user_ref.update({"credit": updated_credit, "update": int(time.time())})

                # Log the credit addition or subtraction
                log(user_id, action=10, remaining_credit=updated_credit)
            except ValueError:
                messagebox.showerror("Hiba", "Kérjük, érvényes számot adjon meg!")
        elif column_name == "Kölcsön":
            loan_value = new_value.lower() in ["igen", "true", "1"]
            user_ref.update({"loan": loan_value, "update": int(time.time())})

        entry.destroy()

    # Create an entry widget for editing
    x, y, width, height = tree.bbox(item, column=column)
    entry = tk.Entry(root)
    entry.place(x=x, y=y + height // 2, anchor="w", width=width)
    entry.insert(0, tree.set(item, column_name))
    entry.focus_set()
    entry.bind("<Return>", save_edit)
    entry.bind("<FocusOut>", lambda e: entry.destroy())

tree.bind("<Double-1>", on_double_click)

# Gombok
frame = tk.Frame(root)
frame.pack(pady=10)

tk.Button(frame, text="Frissítés", command=refresh_users).grid(row=0, column=0, padx=10)
tk.Button(frame, text="Mentés", command=save_changes).grid(row=0, column=1, padx=10)

def add_user_gui():
    def submit():
        user_id = entry_id.get()
        name = entry_name.get()
        credit = int(entry_credit.get()) if entry_credit.get().isdigit() else 0
        loan = bool(var_loan.get())
        add_user(user_id, name, credit, loan)
        refresh_users()
        add_window.destroy()

    add_window = tk.Toplevel(root)
    add_window.title("Új felhasználó hozzáadása")

    tk.Label(add_window, text="Felhasználó ID:").grid(row=0, column=0, padx=10, pady=10)
    entry_id = tk.Entry(add_window)
    entry_id.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(add_window, text="Név:").grid(row=1, column=0, padx=10, pady=10)
    entry_name = tk.Entry(add_window)
    entry_name.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(add_window, text="Kredit:").grid(row=2, column=0, padx=10, pady=10)
    entry_credit = tk.Entry(add_window)
    entry_credit.grid(row=2, column=1, padx=10, pady=10)

    tk.Label(add_window, text="Kölcsön:").grid(row=3, column=0, padx=10, pady=10)
    var_loan = tk.IntVar()
    tk.Checkbutton(add_window, variable=var_loan).grid(row=3, column=1, padx=10, pady=10)

    tk.Button(add_window, text="Hozzáadás", command=submit).grid(row=4, column=0, columnspan=2, pady=10)

def delete_user_gui():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Hiba", "Nincs kiválasztva felhasználó törlésre.")
        return

    user_id = tree.item(selected_item[0], "values")[0]
    delete_user(user_id)
    refresh_users()

frame = tk.Frame(root)
frame.pack(pady=10)
tk.Button(frame, text="Új felhasználó", command=add_user_gui).grid(row=0, column=0, padx=10)
tk.Button(frame, text="Felhasználó törlése", command=delete_user_gui).grid(row=0, column=1, padx=10)

refresh_users()

# Global variable to store the Firebase listener thread
listener_thread = None

def listen_to_rtdb_changes():
    """Listen for changes in the RTDB and refresh the user table."""
    users_ref = db.reference("users")

    def listener(event):
        # Refresh the user table whenever a change occurs
        refresh_users()

    # Attach the listener to the "users" reference in a separate thread
    global listener_thread
    listener_thread = threading.Thread(target=users_ref.listen, args=(listener,))
    listener_thread.daemon = True  # Ensure the thread stops when the main program exits
    listener_thread.start()

def on_closing():
    """Handle the application closing event."""
    global listener_thread
    if listener_thread and listener_thread.is_alive():
        # Stop the listener thread
        listener_thread.join(timeout=1)
    root.destroy()

# Call the listener function to start monitoring changes
listen_to_rtdb_changes()

# Bind the on_closing function to the window close event
root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
