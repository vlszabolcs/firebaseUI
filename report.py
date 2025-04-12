import firebase_admin
from firebase_admin import credentials, db
import json
import matplotlib.pyplot as plt
from datetime import datetime

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

# Initialize Firebase Admin SDK
cred = credentials.Certificate("coffeegg-a4840-firebase-adminsdk-bse6a-91727ff1f3.json")  # Service account key file
firebase_admin.initialize_app(cred, {
    "databaseURL": databaseURL  # RTDB URL
})

def get_logs():
    """Fetch logs from the /Log table in Firebase."""
    logs_ref = db.reference("Log")
    logs = logs_ref.get()
    return logs

def organize_logs_by_user(logs):
    """Organize logs by userId."""
    organized_logs = {}
    for timestamp, log in logs.items():
        user_id = log.get("userId")
        if user_id not in organized_logs:
            organized_logs[user_id] = {
                "timestamps": [],
                "actions": [],
                "credits": []
            }
        organized_logs[user_id]["timestamps"].append(timestamp)
        organized_logs[user_id]["actions"].append(log.get("action"))
        organized_logs[user_id]["credits"].append(log.get("remainingCredit"))
    return organized_logs

def save_logs_to_json(logs, file_path):
    """Save logs to a JSON file."""
    with open(file_path, 'w') as json_file:
        json.dump(logs, json_file, indent=4)

if __name__ == "__main__":
    logs = get_logs()
    if logs:
        # Organize logs by userId
        organized_logs = organize_logs_by_user(logs)
        # Save organized logs to a JSON file
        save_logs_to_json(organized_logs, "organized_logs.json")
        print("Organized logs have been saved to organized_logs.json.")
        
        # Load the organized logs from the JSON file
        with open("organized_logs.json", "r") as file:
            data = json.load(file)

        # Extract data for user 2A56E9B4
        user_id = "DA4CF9B4"
        if user_id in data:
            # Filter out timestamps before 2025
            filtered_data = [
                (datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S'), credit)
                for ts, credit in zip(data[user_id]["timestamps"], data[user_id]["credits"])
                if datetime.fromtimestamp(int(ts)).year >= 2025
            ]

            if filtered_data:
                timestamps, credits = zip(*filtered_data)

                # Plot the data
                fig, ax = plt.subplots(figsize=(10, 6))
                scatter = ax.scatter(timestamps, credits, marker="o", label=f"User {user_id}")

                # Add labels and title
                ax.set_xlabel("Date")
                ax.set_ylabel("Credits")
                ax.set_title(f"Credit Changes Over Time for User {user_id}")
                plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
                plt.grid(True)
                plt.legend()

                # Add interactive annotations
                annot = ax.annotate("", xy=(0, 0), xytext=(15, 15),
                                    textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w"),
                                    arrowprops=dict(arrowstyle="->"))
                annot.set_visible(False)

                def update_annot(ind):
                    pos = scatter.get_offsets()[ind["ind"][0]]
                    annot.xy = pos
                    text = f"{timestamps[ind['ind'][0]]}, {credits[ind['ind'][0]]}"
                    annot.set_text(text)
                    annot.get_bbox_patch().set_alpha(0.8)

                def on_hover(event):
                    vis = annot.get_visible()
                    if event.inaxes == ax:
                        cont, ind = scatter.contains(event)
                        if cont:
                            update_annot(ind)
                            annot.set_visible(True)
                            fig.canvas.draw_idle()
                        else:
                            if vis:
                                annot.set_visible(False)
                                fig.canvas.draw_idle()

                fig.canvas.mpl_connect("motion_notify_event", on_hover)

                # Show the plot
                plt.tight_layout()  # Adjust layout to prevent clipping
                plt.show()
            else:
                print(f"No data for user {user_id} in 2025 or later.")
        else:
            print(f"No data found for user {user_id}.")
    else:
        print("No logs found.")