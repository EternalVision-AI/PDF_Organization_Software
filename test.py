import os
import json

script_path = os.path.abspath(__file__)
base_path = os.path.dirname(script_path)
print("Script Directory:", base_path)

# Initialize the data dictionary with category names
data = {
    "categories": {
        "Schule": "Schule",
        "Versicherung": "Versicherung",
        "Immobile - Hertastr": "Immobile - Hertastr",
        "Immobile - Saarbrückerplatz": "Immobile - Saarbrückerplatz",
        "Auto": "Auto"
    }
}

# Update the output paths for each category
for category in data["categories"]:
    data["categories"][category] = os.path.join(base_path, "Output", data["categories"][category])

# Function to save the dictionary as a JSON file
def save_data_to_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Save the updated data to 'config1.json'
save_data_to_json(data, 'config1.json')