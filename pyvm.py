import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
import urllib.request
import zipfile
import winreg

class PyVersionManager:
    def __init__(self):
        self.base_dir = Path(os.path.expanduser("~")) / ".pyvm"
        self.versions_dir = self.base_dir / "versions"
        self.config_file = self.base_dir / "config.json"
        self.python_download_url = "https://www.python.org/ftp/python/{version}/python-{version}-embed-amd64.zip"
        self.setup()

    def setup(self):
        """Initialize directory structure and config file."""
        self.base_dir.mkdir(exist_ok=True)
        self.versions_dir.mkdir(exist_ok=True)
        
        if not self.config_file.exists():
            self._write_config({"installed_versions": {}, "current": None})
        
        # Detect existing Python installations
        self._detect_existing_python()

    def _detect_existing_python(self):
        """Detect existing Python installations on the system."""
        config = self._read_config()
        
        # Check common Python installation paths
        paths_to_check = [
            r"C:\Python*",
            r"C:\Program Files\Python*",
            r"C:\Program Files (x86)\Python*",
            os.path.expanduser(r"~\AppData\Local\Programs\Python\Python*")
        ]

        # Try to detect current Python version
        try:
            result = subprocess.run(['python', '--version'], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split()[1]
                python_path = subprocess.run(['where', 'python'], 
                                          capture_output=True, 
                                          text=True).stdout.strip()
                if python_path:
                    python_dir = str(Path(python_path).parent)
                    config["installed_versions"][version] = python_dir
                    config["current"] = version
        except Exception as e:
            print(f"Warning: Could not detect current Python version: {e}")

        # Check registry for installed Python versions
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SOFTWARE\Python\PythonCore", 
                              0, 
                              winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                i = 0
                while True:
                    try:
                        version = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, f"{version}\\InstallPath", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as path_key:
                            install_path, _ = winreg.QueryValueEx(path_key, "")
                            if install_path and version not in config["installed_versions"]:
                                config["installed_versions"][version] = install_path
                        i += 1
                    except WindowsError:
                        break
        except WindowsError:
            pass

        self._write_config(config)

    def _write_config(self, config):
        """Write configuration to config file."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def _read_config(self):
        """Read configuration from config file."""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def install_version(self, version):
        """Install a specific Python version."""
        print(f"Installing Python {version}...")
        
        # Check if version is already installed
        config = self._read_config()
        if version in config["installed_versions"]:
            print(f"Python {version} is already installed")
            return True
        
        # Create version directory
        version_dir = self.versions_dir / version
        version_dir.mkdir(exist_ok=True)
        
        # Download Python
        download_url = self.python_download_url.format(version=version)
        zip_path = version_dir / f"python-{version}.zip"
        
        try:
            urllib.request.urlretrieve(download_url, zip_path)
        except urllib.error.URLError:
            print(f"Failed to download Python {version}")
            return False
        
        # Extract Python
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(version_dir)
        
        # Update config
        config["installed_versions"][version] = str(version_dir)
        self._write_config(config)
        
        print(f"Successfully installed Python {version}")
        return True

    def use_version(self, version):
        """Switch to a specific Python version."""
        config = self._read_config()
        
        if version not in config["installed_versions"]:
            print(f"Python {version} is not installed")
            return False
        
        # Update PATH in Windows registry
        try:
            version_dir = Path(config["installed_versions"][version])
            self._update_path(version_dir)
            config["current"] = version
            self._write_config(config)
            print(f"Switched to Python {version}")
            return True
        except Exception as e:
            print(f"Failed to switch Python version: {e}")
            return False

    def _update_path(self, version_dir):
        """Update system PATH to use selected Python version."""
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            "Environment", 
                            0, 
                            winreg.KEY_ALL_ACCESS)
        
        try:
            path, _ = winreg.QueryValueEx(key, "PATH")
            # Remove other Python paths
            paths = path.split(";")
            paths = [p for p in paths if "Python" not in p]
            # Add new Python path
            paths.insert(0, str(version_dir))
            new_path = ";".join(paths)
            
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            # Broadcast environment change
            subprocess.run(['setx', 'PATH', new_path])
        finally:
            winreg.CloseKey(key)

    def list_versions(self):
        """List installed Python versions."""
        config = self._read_config()
        print("\nInstalled Python versions:")
        if not config["installed_versions"]:
            print("No Python versions are currently tracked by PyVM")
            return
        
        for version, path in config["installed_versions"].items():
            current = " (current)" if version == config["current"] else ""
            print(f"- Python {version}{current}")
            print(f"  Location: {path}")

    def uninstall_version(self, version):
        """Uninstall a specific Python version."""
        config = self._read_config()
        
        if version not in config["installed_versions"]:
            print(f"Python {version} is not installed")
            return False
        
        version_dir = Path(config["installed_versions"][version])
        
        # Only remove if it's in our versions directory
        if str(self.versions_dir) in str(version_dir):
            shutil.rmtree(version_dir)
        else:
            print(f"Warning: Cannot uninstall system Python at {version_dir}")
            print("Only Python versions installed by PyVM can be uninstalled")
            return False
        
        # Update config
        del config["installed_versions"][version]
        if config["current"] == version:
            config["current"] = None
        self._write_config(config)
        
        print(f"Uninstalled Python {version}")
        return True

def main():
    manager = PyVersionManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print(" python pyvm.py install <version>  - Install Python version")
        print(" python pyvm.py use <version>      - Switch to Python version")
        print(" python pyvm.py list              - List installed versions")
        print(" python pyvm.py uninstall <version> - Uninstall Python version")
        return

    command = sys.argv[1]
    
    if command == "install" and len(sys.argv) == 3:
        manager.install_version(sys.argv[2])
    elif command == "use" and len(sys.argv) == 3:
        manager.use_version(sys.argv[2])
    elif command == "list":
        manager.list_versions()
    elif command == "uninstall" and len(sys.argv) == 3:
        manager.uninstall_version(sys.argv[2])
    else:
        print("Invalid command")

if __name__ == "__main__":
    main()