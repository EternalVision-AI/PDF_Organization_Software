import os
import json

def initialize_data(filename):
    """ Initialize a dictionary with categories and their base names. """
    data = {
        "categories": {
            "Schule": "Schule",
            "Versicherung": "Versicherung",
            "Immobile - Hertastr": "Immobile - Hertastr",
            "Immobile - Saarbrückerplatz": "Immobile - Saarbrückerplatz",
            "Auto": "Auto"
        }
    }
    script_path = os.path.abspath(__file__)
    base_path = os.path.dirname(script_path)
    print("Script Directory:", base_path)
    # Update the output paths for each category
    for category in data["categories"]:
        data["categories"][category] = os.path.join(base_path, "Output", data["categories"][category])

    """ Save the dictionary to a JSON file. """
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully written to {filename}")
    except Exception as e:
        print(f"Failed to write to {filename}: {e}")

def serialize_data(data):
    """ Prepare data for JSON serialization by ensuring all values are serializable. """
    for category, path in data["categories"].items():
        # Ensure the path is a string (this should always be true in this context)
        if not isinstance(path, str):
            data["categories"][category] = str(path)  # Convert PathLike objects to string if necessary
    return data

def write_json_file(filename, data):
    """ Serialize the data to a JSON file. """
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        print("Data successfully written to", filename)
    except TypeError as e:
        print("Data provided is not serializable:", e)
    except Exception as e:
        print("Failed to write to", filename, ":", e)
def read_json_file(filename):
    """ Read a JSON file and return the data as a dictionary. """
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: The file {filename} does not exist.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: The file {filename} is not a valid JSON file.")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}

def get_categories(data):
    """ Extract category names from data dictionary. """
    # Get the 'categories' dictionary from data
    categories = data.get('categories', {})
    # Return the list of keys from the categories dictionary
    return list(categories.keys())

def get_category_folder(filename, category):
    data = None
    data = read_json_file(filename)
    if data is not None and "categories" in data:
        return data["categories"].get(category, "Category not found.")
    else:
        return "Invalid or missing data."
      
def add_new_category(filename, category_name, folder_path):
    """ Add a new category and its folder path to the configuration file. """
    data = read_json_file(filename)
    if data is not None:
        if "categories" not in data:
            data["categories"] = {}  # Initialize if not already present

        if category_name in data["categories"]:
            print(f"Category '{category_name}' already exists.")
        else:
            data["categories"][category_name] = folder_path
            write_json_file(filename, data)
            print(f"Category '{category_name}' added successfully with folder '{folder_path}'.")
    else:
        print("Error: Could not load data.")      

def update_category_folder(filename, category, output_path):
    """ Update the output path for a specific category. """
    config_data = read_json_file(filename)
    config_data['categories'][category] = output_path
    write_json_file(filename, config_data)
    
def update_category_name_and_folder(filename, old_category_name, new_category_name, new_folder_path):
    data = read_json_file(filename)
    if data is not None:
        if "categories" in data:
            if old_category_name in data["categories"]:
                if new_category_name in data["categories"] and new_category_name != old_category_name:
                    print(f"Error: A category with the name '{new_category_name}' already exists.")
                else:
                    # Update the category name and folder
                    data["categories"][new_category_name] = new_folder_path
                    if new_category_name != old_category_name:
                        del data["categories"][old_category_name]
                    write_json_file(filename, data)
                    print(f"Category '{old_category_name}' updated to '{new_category_name}' with new path '{new_folder_path}'.")
            else:
                print(f"Error: Category '{old_category_name}' does not exist.")
        else:
            print("Error: No categories found in the configuration.")
    else:
        print("Error: Could not load data from file.")
        
def delete_category(filename, category_name):
    """ Delete a category from the configuration file. """
    data = read_json_file(filename)
    if data is not None and "categories" in data:
        if category_name in data["categories"]:
            del data["categories"][category_name]  # Remove the category
            write_json_file(filename, data)
            print(f"Category '{category_name}' has been successfully deleted.")
        else:
            print(f"Category '{category_name}' does not exist.")
    else:
        print("Error: Could not load data or 'categories' key is missing.")