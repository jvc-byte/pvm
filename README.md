# Python Version Manager for Windows (PyVM)

A lightweight Python version manager that allows you to install, manage, and switch between different Python versions on Windows.

## Features

- Install multiple Python versions side by side
- Switch between installed Python versions easily
- Manage Python versions through simple commands
- Automatically handles PATH environment variables
- Clean uninstallation of Python versions

## Prerequisites

- Windows operating system
- Administrator privileges (required for PATH manipulation)
- Internet connection (for downloading Python versions)
- Git installed on your system
- Python installed on your PC 

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pyvm.git
   cd pyvm
   ```

2. Run your first command to verify installation:
   ```bash
   python pyvm.py
   ```

3. (Optional) Add to PATH:
   - Add the pyvm directory to your system's PATH
   - Or create a shortcut in a directory that's already in your PATH

## Usage

### Important: Always run commands with administrator privileges

Right-click on PowerShell or Command Prompt and select "Run as administrator" before executing any PyVM commands.

### Basic Commands

1. View available commands:
   ```bash
   python pyvm.py
   ```

2. List installed Python versions:
   ```bash
   python pyvm.py list
   ```

3. Install a specific Python version:
   ```bash
   python pyvm.py install 3.9.0
   ```

4. Switch to an installed Python version:
   ```bash
   python pyvm.py use 3.9.0
   ```

5. Uninstall a Python version:
   ```bash
   python pyvm.py uninstall 3.9.0
   ```

### Step-by-Step Example

1. First time setup:
   ```bash
   # Open PowerShell as Administrator
   git clone https://github.com/YOUR_USERNAME/pyvm.git
   cd pyvm
   python pyvm.py list  # Will show no versions installed
   ```

2. Install your first Python version:
   ```bash
   python pyvm.py install 3.9.0
   # Wait for installation to complete
   ```

3. Switch to the installed version:
   ```bash
   python pyvm.py use 3.9.0
   ```

4. Verify the active Python version:
   ```bash
   python --version
   ```

## Directory Structure

PyVM creates the following directory structure in your user home folder:

```
~/.pyvm/
├── versions/
│   ├── 3.9.0/
│   ├── 3.8.0/
│   └── ...
└── config.json

Repository Structure:
pyvm/
├── pyvm.py
├── README.md
├── LICENSE
└── .gitignore
```

## Troubleshooting

1. "Access Denied" errors:
   - Make sure you're running PowerShell or Command Prompt as Administrator

2. Python version not found after switching:
   - Close and reopen your terminal
   - Verify PATH environment variable is updated
   - Check if the version is properly installed using `pyvm list`

3. Download failures:
   - Check your internet connection
   - Verify the Python version exists on python.org
   - Try running the command again

4. PATH issues:
   - Check if multiple Python installations exist in PATH
   - Verify the registry changes were successful
   - Log out and log back in to refresh environment variables

## Limitations

- Only supports 64-bit Python versions
- Requires administrator privileges
- Windows-only support
- Internet connection required for installation
- Does not support beta/alpha versions

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Justin Anazor was here... 