#!/usr/bin/env python3
import json

# Paths to your JSON files.
json_file1 = 'JSONs/individual_assessment.json'
json_file2 = 'JSONs/pre-package.json'
merged_output_file = 'JSONs/final.json'

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def save_json(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")

def main():
    # Load data from both JSON files.
    data1 = load_json(json_file1)
    data2 = load_json(json_file2)
    
    # Merge the lists. If both JSON files contain a list of objects.
    merged_data = data1 + data2
    
    # Write the merged data out to a new JSON file.
    save_json(merged_data, merged_output_file)

if __name__ == "__main__":
    main()
