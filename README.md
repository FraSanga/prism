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

Run the simulation:

```bash
python prism.py
```

The script processes test cases from `canonical-data.json`.
Generated graphs are saved in the `png_result/` directory.