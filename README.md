# JSONL Viewer

A powerful desktop application for viewing and filtering JSONL (JSON Lines) files with an intuitive GUI built with Python and Tkinter.

## Features

- 📁 **Directory Navigation** - Browse folders and load JSONL/JSON files with an interactive file tree sidebar
- 🔍 **Advanced Multi-Filter System** - Apply multiple filter conditions with AND/OR logic
- 📍 **JSON Path Queries** - Use flexible path syntax to target specific nested values:
  - Standard array wildcards: `data.test[*].id`
  - Multi-array concatenation: `data.test[*].reagentBarcode[*]`
  - Explicit indexes: `data.test[0].id` or `data.test[-1].id`
  - Fuzzy search: Leave path blank to search entire record
- 💾 **Syntax-Highlighted JSON Inspector** - View and inspect records with color-coded JSON syntax
- 📋 **Copy to Clipboard** - Quick copy of formatted JSON records
- ⚡ **Real-Time Filtering** - Instantly filter records with live progress indication
- 🚀 **Performance Optimized** - Efficiently loads large JSONL files with threaded operations

## Installation

### Requirements
- Python 3.8+
- tkinter (usually included with Python)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/gorkalertxundi/jsonl_viewer.git
```

2. Ensure Python and tkinter are installed:
```bash
python -m tkinter  # Test if tkinter is available
```

3. Run the application:
```bash
python app.py
```

## Usage

### Basic Workflow

1. **Open Folder** - Click the "📁 Open Folder" button or the app automatically opens your home directory on startup
2. **Browse Files** - Navigate the file tree to find your JSONL files
3. **Select a File** - Click on a file to load it (progress bar shows loading status)
4. **View Records** - Records appear in the list view with key information
5. **Filter Data** - Add filter conditions using the filter matrix

### Filter Matrix Guide

- **Match Mode**: Choose between "ALL Conditions (AND)" or "ANY Condition (OR)"
- **Add Condition Row**: Click "➕ Add Condition Row" to add more filters
- **Path**: JSON path to the field (leave blank for global search)
- **Value contains**: Text to search for (case-insensitive)
- **Apply Filter**: Click "Apply Filter Matrix" to execute
- **Reset & Show All**: Show all records without filters

### JSON Path Examples

```
# Access array elements
data.samples[*].id          → Get all IDs from samples array
data.samples[0].name        → Get name of first sample
data.samples[-1].timestamp  → Get timestamp of last sample

# Nested arrays
results[*].details[*].value → Get all values from nested arrays

# Fuzzy search
(leave path blank, enter text in "Value contains")
```

### Record Inspector

- Select a record from the list to view its full JSON
- Color-coded syntax highlighting:
  - 🔵 Blue: JSON keys
  - ⚫ Gray: String values
  - 🔴 Red: Numbers
  - 🟢 Teal: Booleans
  - 🟣 Magenta: Null values
- Use "📋 Copy JSON" button to copy the formatted JSON to clipboard

## Application Features

### File Tree Sidebar
- Hierarchical folder navigation
- Lazy-loading of subdirectories for performance
- Color-coded items (📁 folders, 📄 files)
- Automatic filtering for JSON/JSONL files

### Status Bar
- Shows current file name and number of loaded records
- Displays filter statistics (e.g., "Showing 50 of 1000 total rows")

### Performance Optimizations
- Multi-threaded file loading
- Progress indication during large file reads
- Efficient JSON parsing with error handling
- Lazy evaluation of directory expansion

## Requirements

- Python 3.8 or higher
- tkinter (included with most Python distributions)

## Architecture

```
JSONLViewer
├── File Tree Navigation
├── Filter Matrix Engine
├── JSON Parser & Query Engine
├── Records List View
└── JSON Inspector (Syntax Highlighted)
```

## EXE Generation
To create a standalone executable for Windows:
1. Install pyinstaller:
```bash
   pip install pyinstaller
```
2. Run the following command in the project directory:
```bash
   pyinstaller --onefile --windowed app.py
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Author

Created by **Gorka Lertxundi**

- GitHub: [gorkalertxundi](https://github.com/gorkalertxundi)
- Repository: [Advanced_JSONL_Multi-Filter_Viewer](https://github.com/gorkalertxundi/Advanced_JSONL_Multi-Filter_Viewer)

## Support

If you encounter any issues or have suggestions, please open an issue on the [GitHub repository](https://github.com/gorkalertxundi/Advanced_JSONL_Multi-Filter_Viewer).

---

**Happy filtering! 🚀**
