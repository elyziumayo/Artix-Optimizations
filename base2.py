import os
import subprocess
import re
import sys
import shutil
import urllib.request

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

# Fetch dependencies from PKGBUILD
def fetch_dependencies(pkgbuild_path):
    makedepends = []
    depends = []

    with open(pkgbuild_path, "r") as file:
        lines = file.readlines()

        # Join all lines to process the array as a whole
        content = ''.join(lines)

        # Find makedepends array and parse dependencies
        makedepends_match = re.search(r"makedepends=\((.*?)\)", content, re.DOTALL)
        if makedepends_match:
            # Extract makedepends and split by spaces or newline, stripping extra quotes
            makedepends = [dep.strip().strip('"').strip("'") for dep in makedepends_match.group(1).split()]
        
        # Find depends array and parse dependencies
        depends_match = re.search(r"depends=\((.*?)\)", content, re.DOTALL)
        if depends_match:
            # Extract depends and split by spaces or newline, stripping extra quotes
            depends = [dep.strip().strip('"').strip("'") for dep in depends_match.group(1).split()]

    return makedepends, depends

# Check if package is installed
def is_package_installed(pkg_name):
    try:
        subprocess.check_call(["pacman", "-Qi", pkg_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

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

# Clone the repo
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

# Build and install a package
def build_and_install(pkg_name, repo_path):
    print_yellow(f"Building and installing package: {pkg_name}...")

    # Navigate to the cloned repo and build the package
    try:
        subprocess.check_call(["makepkg", "-si"], cwd=repo_path)
        print_green(f"Package '{pkg_name}' built and installed successfully.")
    except subprocess.CalledProcessError as e:
        print_red(f"Error building '{pkg_name}': {e}")

# Recursively build dependencies
def build_dependencies(dep_list, custompkg_dir, repo_base_dir):
    for dep in dep_list:
        if not is_package_installed(dep):
            print_yellow(f"Dependency '{dep}' is not installed. Building from source...")
            # Check if the repo for the dependency exists
            if not check_repo_exists(dep):
                dep_repo_name = input(f"{MAGENTA}Repo for '{dep}' not found, please provide the correct repo name: {RESET}").strip()
                while not check_repo_exists(dep_repo_name):
                    dep_repo_name = input(f"{MAGENTA}Repo '{dep_repo_name}' still not found, please provide a correct repo name: {RESET}").strip()

            # Clone the dependency repository
            clone_repo(dep, custompkg_dir)

            # Navigate to the cloned repo
            dep_repo_path = os.path.join(custompkg_dir, dep)

            # Fetch dependencies for this dependency
            dep_makedepends, dep_depends = fetch_dependencies(os.path.join(dep_repo_path, "PKGBUILD"))

            # Build dependencies recursively
            build_dependencies(dep_makedepends, custompkg_dir, dep_repo_path)
            build_dependencies(dep_depends, custompkg_dir, dep_repo_path)

            # After dependencies are built, build and install the dependency
            build_and_install(dep, dep_repo_path)
        else:
            print_green(f"Dependency '{dep}' is already installed.")

# Main function for building dependencies and the main package
def main():
    repo_base_dir = sys.argv[1]  # Path of the main package repo passed from the first script
    custompkg_dir = os.path.join(os.path.expanduser("~"), "custompkg")

    # Fetch dependencies for the main package
    makedepends, depends = fetch_dependencies(os.path.join(repo_base_dir, "PKGBUILD"))

    # Handle makedepends first, then depends
    print_yellow("Building makedepends...")
    build_dependencies(makedepends, custompkg_dir, repo_base_dir)

    print_yellow("Building depends...")
    build_dependencies(depends, custompkg_dir, repo_base_dir)

    # After dependencies are built, build the main package
    build_and_install(os.path.basename(repo_base_dir), repo_base_dir)

if __name__ == "__main__":
    main()

