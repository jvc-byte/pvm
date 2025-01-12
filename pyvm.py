import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
import urllib.request
import zipfile
import winreg
import ctypes

class PyVersionManager:
    def __init__(self):
        self.base_dir = Path(os.path.expanduser("~")) / ".pyvm"
        self.versions_dir = self.base_dir / "versions"
        self.config_file = self.base_dir / "config.json"
        self.python_download_url = "https://www.python.org/ftp/python/{version}/python-{version}-embed-amd64.zip"
        self.setup()

    def setup(self):
        """Initialize directory structure and config file."""
        try:
            self.base_dir.mkdir(exist_ok=True)
            self.versions_dir.mkdir(exist_ok=True)
            
            if not self.config_file.exists():
                self._write_config({"installed_versions": {}, "current": None})
        except Exception as e:
            print(f"Setup error: {e}")

    def _write_config(self, config):
        """Write configuration to config file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error writing config: {e}")

    def _read_config(self):
        """Read configuration from config file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading config: {e}")
            return {"installed_versions": {}, "current": None}

    def _is_admin(self):
        """Check if the script has admin privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def _disable_app_execution_alias(self):
        """Disable Python App Execution Alias in Windows."""
        try:
            # Path to the App Execution Aliases
            alias_path = r"C:/Users/dell/AppData/Local/Microsoft/WindowsApps/python.exe"
            
            # Try to delete the key
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, alias_path, 0, 
                                  winreg.KEY_ALL_ACCESS) as key:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, alias_path)
            except WindowsError:
                pass
            
            print("Disabled Windows Python App Execution Alias")
            return True
        except Exception as e:
            print(f"Failed to disable App Execution Alias: {e}")
            return False

    def _get_current_python_info(self):
        """Get information about current Python installation."""
        try:
            # Get version
            version_proc = subprocess.run(['python', '--version'], 
                                        capture_output=True, 
                                        text=True)
            version = version_proc.stdout.strip() if version_proc.returncode == 0 else None

            # Get location
            where_proc = subprocess.run(['where', 'python'], 
                                      capture_output=True, 
                                      text=True)
            location = where_proc.stdout.strip().split('\n')[0] if where_proc.returncode == 0 else None

            return version, location
        except Exception:
            return None, None

    def _update_path(self, version_dir):
        """Update system PATH to use selected Python version."""
        if not self._is_admin():
            print("Error: Administrative privileges required.")
            print("Please run the command prompt as Administrator.")
            return False

        try:
            
            # Check if python.exe exists
            python_exe = version_dir / "python.exe"
            if not python_exe.exists():
                print(f"Error: {python_exe} not found.")
                return False
            
            # Disable Windows App Execution Alias
            self._disable_app_execution_alias()

            # Access PATH
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
            
            try:
                user_path, _ = winreg.QueryValueEx(key, "PATH")
            except WindowsError:
                user_path = ""

            # Remove old Python paths
            user_paths = [p for p in user_path.split(";") if "Python" not in p and "WindowsApps" not in p]
            
            # Add new Python paths
            python_paths = [str(version_dir), str(version_dir / "Scripts")]
            new_path = ";".join(python_paths + user_paths)
            
            # Update user PATH
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
            
            # Apply the change immediately
            os.environ["PATH"] = new_path
            
            print(f"PATH updated to include Python {version_dir}")
            return True

        except Exception as e:
            print(f"Failed to update PATH: {e}")
            return False

    def scan_for_python(self):
        """Scan the system for Python installations."""
        installations = {}
        
        # Get current Python version and location
        current_version, current_location = self._get_current_python_info()
        if current_version and current_location:
            version = current_version.split()[1]  # Remove "Python" from string
            installations[version] = current_location
            
        # Check Windows Registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Python\PythonCore", 
                               0, 
                               winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                i = 0
                while True:
                    try:
                        version = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, f"{version}\\InstallPath", 
                                          0, 
                                          winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as path_key:
                            install_path, _ = winreg.QueryValueEx(path_key, "")
                            if install_path:
                                python_exe = os.path.join(install_path, "python.exe")
                                if os.path.exists(python_exe):
                                    installations[version] = python_exe
                        i += 1
                    except WindowsError:
                        break
        except WindowsError:
            pass
        
        return installations

    def list_versions(self):
        """List all detected Python versions."""
        print("\nScanning for Python installations...")
        
        # Get PyVM-managed versions
        config = self._read_config()
        pyvm_versions = config.get("installed_versions", {})
        
        # Get system Python versions
        system_versions = self.scan_for_python()
        
        if not pyvm_versions and not system_versions:
            print("No Python installations detected.")
            return

        # Show current active Python
        current_version, current_location = self._get_current_python_info()
        if current_version:
            print(f"\nActive Python: {current_version}")
            if current_location:
                print(f"Location: {current_location}")

        # Show PyVM-managed versions
        if pyvm_versions:
            print("\nPyVM-managed versions:")
            for version, path in pyvm_versions.items():
                print(f"- Python {version}")
                print(f"  Location: {path}")

        # Show system-wide versions
        if system_versions:
            print("\nSystem-wide installations:")
            for version, path in system_versions.items():
                print(f"- Python {version}")
                print(f"  Location: {path}")

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
        
        try:
            # Download Python
            download_url = self.python_download_url.format(version=version)
            zip_path = version_dir / f"python-{version}.zip"
            
            print(f"Downloading from {download_url}...")
            urllib.request.urlretrieve(download_url, zip_path)
            
            print("Extracting files...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(version_dir)
            
            # Update config
            config["installed_versions"][version] = str(version_dir)
            self._write_config(config)
            
            print(f"Successfully installed Python {version}")
            return True
            
        except Exception as e:
            print(f"Installation failed: {e}")
            shutil.rmtree(version_dir, ignore_errors=True)
            return False

    def use_version(self, version):
        """Switch to a specific Python version."""
        if not self._is_admin():
            print("Error: Administrative privileges required.")
            print("Please run Command Prompt or PowerShell as Administrator.")
            return False

        config = self._read_config()
        
        if version not in config["installed_versions"]:
            print(f"Python {version} is not installed or tracked by PyVM")
            return False
        
        version_dir = Path(config["installed_versions"][version])
        if not version_dir.exists():
            print(f"Python installation directory not found: {version_dir}")
            return False

        print(f"\nSwitching to Python {version}...")
        if self._update_path(version_dir):
            config["current"] = version
            self._write_config(config)
            print(f"\nSuccessfully configured Python {version}")
            print("\nIMPORTANT: To complete the switch:")
            print("1. Close all open terminal windows")
            print("2. Open a new terminal")
            print("3. Run 'python --version' to verify the change")
            return True
        return False

    def uninstall_version(self, version):
        """Uninstall a specific Python version."""
        config = self._read_config()
        
        if version not in config["installed_versions"]:
            print(f"Python {version} is not installed through PyVM")
            return False
        
        try:
            version_dir = Path(config["installed_versions"][version])
            
            # Only remove if it's in our versions directory
            if str(self.versions_dir) in str(version_dir):
                shutil.rmtree(version_dir)
            else:
                print(f"Cannot uninstall system Python at {version_dir}")
                return False
            
            # Update config
            del config["installed_versions"][version]
            if config["current"] == version:
                config["current"] = None
            self._write_config(config)
            
            print(f"Uninstalled Python {version}")
            return True
            
        except Exception as e:
            print(f"Uninstallation failed: {e}")
            return False

def main():
    try:
        manager = PyVersionManager()
        
        if len(sys.argv) < 2:
            print("\nPython Version Manager (PyVM) for Windows")
            print("\nUsage:")
            print("  python pyvm.py install <version>  - Install Python version")
            print("  python pyvm.py use <version>      - Switch to Python version")
            print("  python pyvm.py list               - List installed versions")
            print("  python pyvm.py uninstall <version> - Uninstall Python version")
            print("\nNote: 'use' and 'uninstall' commands require administrative privileges")
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
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()