import tkinter as tk
from tkinter import messagebox, ttk
import firebase_admin
from firebase_admin import credentials, db
import time

# Firebase Admin SDK inicializálása
cred = credentials.Certificate("espresso-1d82f-firebase-adminsdk-ejsns-c87b35e13b.json")  # Szolgáltatási fiók kulcsfájl
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://espresso-1d82f-default-rtdb.europe-west1.firebasedatabase.app/"  # RTDB URL
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

def update_user(user_id, updates):
    user_ref = db.reference(f"users/{user_id}")
    updates["update"] = int(time.time())  # Frissítési idő bélyegző
    user_ref.update(updates)

def delete_user(user_id):
    user_ref = db.reference(f"users/{user_id}")
    user_ref.delete()

# Tkinter GUI megvalósítása
def refresh_users():
    for item in tree.get_children():
        tree.delete(item)

    users = list_users()
    if users:
        for user_id, user_data in users.items():
            tree.insert("", "end", iid=user_id, values=(
                user_id, user_data["name"], user_data["credit"], "Igen" if user_data["loan"] else "Nem"
            ))
    else:
        messagebox.showinfo("Információ", "Nincsenek felhasználók a rendszerben.")

def save_changes():
    for item in tree.get_children():
        user_id = tree.item(item, "values")[0]
        new_values = tree.item(item, "values")

        updates = {
            "name": new_values[1],
            "credit": int(new_values[2]),
            "loan": new_values[3] == "Igen"
        }
        update_user(user_id, updates)

    messagebox.showinfo("Mentés", "A módosítások mentésre kerültek.")

# Tkinter főablak
root = tk.Tk()
root.title("GG Coffee")
root.geometry("700x400")
root.minsize(700, 400)

# Felhasználók táblázata
tree = ttk.Treeview(root, columns=("ID", "Név", "Kredit", "Kölcsön"), show="headings", selectmode="browse")
tree.heading("ID", text="ID")
tree.heading("Név", text="Név")
tree.heading("Kredit", text="Kredit")
tree.heading("Kölcsön", text="Kölcsön")

tree.column("ID", minwidth=80,width=80)
tree.column("Név",minwidth=200, width=100)
tree.column("Kredit", minwidth=80,width=2)
tree.column("Kölcsön", minwidth=20,width=1)

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

    def save_edit(event):
        new_value = entry.get()
        tree.set(item, column=column_name, value=new_value)
        entry.destroy()
        save_changes()  # Mentés az Enter lenyomása után

    def save_checkbox():
        new_value = "Igen" if var.get() else "Nem"
        tree.set(item, column=column_name, value=new_value)
        checkbox.destroy()
        save_changes()  # Mentés a jelölőnégyzet változtatása után

    x, y, width, height = tree.bbox(item, column=column)

    if column_name == "Kölcsön":
        var = tk.BooleanVar(value=tree.set(item, column_name) == "Igen")
        checkbox = tk.Checkbutton(root, variable=var, command=save_checkbox)
        checkbox.place(x=x, y=y + height // 2, anchor="w")
    else:
        entry = tk.Entry(root, validate="key", validatecommand=vcmd if column_name == "Kredit" else None)
        entry.place(x=x, y=y + height // 2, anchor="w", width=width)
        entry.insert(0, tree.set(item, column_name))
        entry.focus_set()
        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

tree.bind("<Double-1>", on_double_click)
tree.pack(fill=tk.BOTH, expand=True)

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

root.mainloop()
