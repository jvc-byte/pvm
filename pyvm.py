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
        config = self._read_config()
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
        for version, path in config["installed_versions"].items():
            current = " (current)" if version == config["current"] else ""
            print(f"- Python {version}{current}")

    def uninstall_version(self, version):
        """Uninstall a specific Python version."""
        config = self._read_config()
        
        if version not in config["installed_versions"]:
            print(f"Python {version} is not installed")
            return False
        
        # Remove version directory
        version_dir = Path(config["installed_versions"][version])
        shutil.rmtree(version_dir)
        
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
        print("  pyvm install <version>  - Install Python version")
        print("  pyvm use <version>      - Switch to Python version")
        print("  pyvm list              - List installed versions")
        print("  pyvm uninstall <version> - Uninstall Python version")
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