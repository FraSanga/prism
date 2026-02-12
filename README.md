# Prism Ray Tracer

A Python simulation for ray tracing through prisms with error tolerance visualization.

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the environment:
* Windows:
```bash
venv\Scripts\activate
```

* macOS/Linux:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

![Prism Simulation Screenshot](images/Screenshot2.png)

Run the simulation:

```bash
python prism.py
```

The script processes test cases from `canonical-data.json`.
Generated graphs are saved in the `png_result/` directory.

## Editor

![Editor Screenshot](images/Screenshot.png)

This project includes a graphical editor to create and edit prism configurations. To run the editor, execute the following command:

```bash
python editor.py
```

For detailed instructions on how to use the editor, please refer to the [MANUAL.md](MANUAL.md) file.

## Utilities

### Shuffle Canonical Data

The `utils/shuffle_prisms_and_ids.py` script can be used to shuffle the prisms and their IDs in the `canonical-data.json` file. This is useful for creating new test cases.

To run the script:

```bash
python utils/shuffle_prisms_and_ids.py
```

This will create a new file named `shuffled-canonical-data.json` with the shuffled data.