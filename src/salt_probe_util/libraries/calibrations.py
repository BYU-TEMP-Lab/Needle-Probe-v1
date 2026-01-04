import json
from pathlib import Path
from .materials import options as materials

class Calibration:
    def __init__ (self, json_filepath: Path):
        self.json_filepath = json_filepath
        self.read_json()
        print(self.data)
        self.probe = self.data["probe"]
        self.crucible = self.data["crucible"]
        self.date = self.data["date"]
        self.sample = self.data["sample"]

        self.name = f"{self.probe} - {self.crucible} - {self.sample} - {self.date}"



    def read_json(self):
        # .is_file() is more specific than .exists() (it ensures it's not a folder)
        if self.json_filepath.is_file():
            try:
                data = self.json_filepath.read_text(encoding='utf-8')
                self.data = json.loads(data)
            except json.JSONDecodeError as e:
                print(f"Error: {self.json_filepath.name} is not a valid JSON file. {e}")
            except Exception as e:
                print(f"Unexpected error reading file: {e}")
        else:
            # Use .resolve() to show the full absolute path in the warning
            # This helps you debug exactly where Python is looking
            print(f"Warning: File not found at {self.json_filepath.resolve()}")

# 1. Setup the directory path relative to this file
# Adjust .parent count depending on exactly where this code lives
CAL_DIR = Path(__file__).resolve().parent.parent / "config" / "calibration_data"

# initialize the dictionary
options = {}

# 2. Iterate through all .json files in that directory
for json_file in CAL_DIR.glob("*.json"):
    try:
        # # Load the data from the file
        # data = json.loads(json_file.read_text(encoding='utf-8'))
        # print(data)
        # # 3. Create your Calibration object
        # # This assumes your Calibration class takes a dict as input
        cal = Calibration(json_file)
        
        # 4. Store in your dictionary
        options[cal.name] = cal
        
    except Exception as e:
        print(f"Failed to load calibration {json_file.name}: {e}")