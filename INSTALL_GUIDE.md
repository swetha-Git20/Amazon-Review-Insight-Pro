# Installation Guide for Amazon Review Insight Pro

## Prerequisites

- Python 3.10 or higher must be installed on your system
- pip (Python package installer) should be available

## Python Installation (if not already installed)

### Windows
1. Download Python from https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT:** Check "Add Python to PATH" during installation
4. Verify installation by opening Command Prompt and running: `python --version`

### Mac
1. Install Homebrew if not already installed: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. Install Python: `brew install python@3.11`
3. Verify installation: `python3 --version`

### Linux (Ubuntu/Debian)
1. Update package list: `sudo apt update`
2. Install Python: `sudo apt install python3.10 python3.10-venv python3-pip`
3. Verify installation: `python3 --version`

## Project Installation Steps

1. **Navigate to project directory**
   ```bash
   cd "C:\Users\laksh\Music\Amazon Review Insight Pro"
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   
   # Mac/Linux
   python3 -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Open in browser**
   The application will automatically open at http://localhost:8501

## Troubleshooting

### "Python is not recognized" error
- Make sure Python is installed and added to PATH
- Restart your terminal/command prompt after installation
- Try using `python3` instead of `python`

### pip install fails
- Upgrade pip first: `python -m pip install --upgrade pip`
- Use the --user flag: `pip install --user -r requirements.txt`

### spaCy model download fails
- Try: `python -m spacy download en_core_web_sm --direct`
- Or manually download from: https://github.com/explosion/spacy-models/releases

### Streamlit not found
- Make sure virtual environment is activated
- Install streamlit directly: `pip install streamlit`

### Database errors
- The database will be auto-created on first run
- Make sure the `data/` directory exists
- Check file permissions

## Testing

Run unit tests:
```bash
python tests/test_core.py
```

## Deactivating Virtual Environment

When done, deactivate the virtual environment:
```bash
   deactivate
```

## Next Time You Run the Project

1. Navigate to project directory
2. Activate virtual environment (step 3 above)
3. Run: `streamlit run app.py`
