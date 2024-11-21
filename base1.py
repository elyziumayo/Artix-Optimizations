import os
import subprocess
import urllib.request
import shutil
import re

# ANSI Escape codes for colors
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"

def print_red(msg):
    print(f"{RED}{msg}{RESET}")

def print_green(msg):
    print(f"{GREEN}{msg}{RESET}")

def print_yellow(msg):
    print(f"{YELLOW}{msg}{RESET}")

def print_magenta(msg):
    print(f"{MAGENTA}{msg}{RESET}")

# Check if repo exists
def check_repo_exists(repo_name):
    repo_url = f"https://gitea.artixlinux.org/packages/{repo_name}"
    try:
        with urllib.request.urlopen(repo_url) as response:
            if response.status == 200:
                print_green(f"Repo '{repo_name}' found.")
                return True
    except (urllib.error.HTTPError, urllib.error.URLError):
        print_red(f"Repo '{repo_name}' not found.")
    return False

# Directory management
def check_and_create_directory():
    home_dir = os.path.expanduser("~")
    custompkg_dir = os.path.join(home_dir, "custompkg")

    if not os.path.exists(custompkg_dir):
        print_yellow(f"Creating 'custompkg' directory...")
        os.makedirs(custompkg_dir)
        print_green(f"'{custompkg_dir}' created.")
    else:
        print_green(f"'{custompkg_dir}' exists.")
    
    return custompkg_dir

# Clone repo if not already cloned
def clone_repo(repo_name, custompkg_dir):
    repo_url = f"https://gitea.artixlinux.org/packages/{repo_name}.git"
    print_yellow(f"Cloning '{repo_name}'...")
    
    repo_path = os.path.join(custompkg_dir, repo_name)
    if not os.path.exists(repo_path):
        try:
            subprocess.check_call(["git", "clone", repo_url, repo_path])
            print_green(f"Repo '{repo_name}' cloned successfully.")
        except subprocess.CalledProcessError as e:
            print_red(f"Error cloning '{repo_name}': {e}")
    else:
        print_green(f"Repo '{repo_name}' already exists.")

# Check if package is installed
def is_package_installed(pkg_name):
    try:
        subprocess.check_call(["pacman", "-Qi", pkg_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

# Main program
def main():
    custompkg_dir = check_and_create_directory()

    # Get the package name from user
    pkg_name = input(f"{MAGENTA}Enter package name: {RESET}").strip()

    # Default repo name is the same as the package name
    repo_name = pkg_name

    # Check if the repo exists
    if not check_repo_exists(repo_name):
        repo_name = input(f"{MAGENTA}Repo '{repo_name}' not found, please provide the correct repo name: {RESET}").strip()
        while not check_repo_exists(repo_name):
            repo_name = input(f"{MAGENTA}Repo '{repo_name}' still not found, please provide a correct repo name: {RESET}").strip()

    # Check if the package is already installed
    if is_package_installed(pkg_name):
        install_choice = input(f"{MAGENTA}Package '{pkg_name}' is already installed. Do you want to build it from source? (y/n): {RESET}").strip().lower()
        if install_choice != "y":
            print_green(f"Skipping '{pkg_name}' installation.")
            return

    # Clone the repo
    clone_repo(repo_name, custompkg_dir)

    # Navigate to the cloned directory
    repo_path = os.path.join(custompkg_dir, repo_name)

    # Ask user if they want to edit PKGBUILD
    edit_pkgbuild = input(f"{MAGENTA}Do you want to edit the PKGBUILD file? (y/n): {RESET}").strip().lower()

    if edit_pkgbuild == "y":
        subprocess.check_call(['nano', os.path.join(repo_path, 'PKGBUILD')])  # Use nano to edit PKGBUILD

    # Once cloned and edited, proceed to build dependencies and install the package (call the second script)
    subprocess.check_call(['python3', '/scripts/base2.py', repo_path])  # Replace with your actual second script filename

if __name__ == "__main__":
    main()

