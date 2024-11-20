import os
import subprocess
import shutil
import re

class Colors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    RESET = '\033[0m'

def print_colored(message, color):
    print(f"{color}{message}{Colors.RESET}")

def get_package_dependencies(pkgbuild_path):
    """Extract dependencies from PKGBUILD file."""
    dependencies = set()
    if os.path.exists(pkgbuild_path):
        with open(pkgbuild_path, 'r') as f:
            content = f.read()
            # Match depends=() and makedepends=() arrays
            dep_arrays = ['depends', 'makedepends']
            for array_name in dep_arrays:
                # Find all dependency arrays
                pattern = fr'{array_name}=\((.*?)\)'
                matches = re.findall(pattern, content, re.DOTALL)
                
                for match in matches:
                    # Remove any comments
                    match = re.sub(r'#.*$', '', match, flags=re.MULTILINE)
                    
                    # First handle quoted packages (which might contain spaces)
                    quoted_deps = re.findall(r'[\'"]([^\'"]+)[\'"]', match)
                    for dep in quoted_deps:
                        # Remove version constraints
                        base_dep = re.split(r'[<>=]', dep)[0].strip()
                        if base_dep and not base_dep.startswith('$'):
                            dependencies.add(base_dep)
                    
                    # Remove the quoted parts we've processed
                    for quoted in quoted_deps:
                        match = match.replace(f"'{quoted}'", '')
                        match = match.replace(f'"{quoted}"', '')
                    
                    # Handle remaining unquoted dependencies
                    unquoted_deps = match.split()
                    for dep in unquoted_deps:
                        # Clean up the dependency name
                        dep = dep.strip("'\" ")
                        # Skip if empty or is a comparative operator
                        if dep and dep not in ['>=', '<=', '=', '>', '<', 'and', 'or']:
                            # Remove version constraints
                            base_dep = re.split(r'[<>=]', dep)[0].strip()
                            if base_dep and not base_dep.startswith('$'):
                                dependencies.add(base_dep)
    
    return dependencies

def update_repo_mappings(package_name, repo_name, repo_mappings_file):
    """Update the repo mappings file with new mapping."""
    print_colored(f"Adding new mapping: {package_name} -> {repo_name}", Colors.GREEN)
    with open(repo_mappings_file, 'a') as f:
        f.write(f"{package_name} {repo_name}\n")

def try_clone_package(repo_name, package_dir):
    """Attempt to clone a package repository."""
    package_url = f"https://gitea.artixlinux.org/packages/{repo_name}.git"
    try:
        result = subprocess.run(
            ["git", "clone", package_url, package_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print_colored(f"Error cloning repository: {result.stderr}", Colors.RED)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_colored(f"Exception occurred: {e}", Colors.RED)
        return False

def handle_package_clone(package_name, repo_mappings, custompkg_dir, repo_mappings_file):
    """Handle the package cloning process with proper repo name resolution."""
    package_dir = os.path.join(custompkg_dir, package_name)
    
    # Remove existing directory if it exists
    if os.path.exists(package_dir):
        print_colored(f"Removing old folder: {package_name}", Colors.YELLOW)
        shutil.rmtree(package_dir)
    
    # First check if package exists in mappings
    if package_name in repo_mappings:
        repo_name = repo_mappings[package_name]
        print_colored(f"Found mapping: {package_name} -> {repo_name}", Colors.BLUE)
    else:
        repo_name = package_name  # For most packages, repo name is the same as package name
        print_colored(f"No mapping found for {package_name}, using package name as repo name.", Colors.BLUE)
    
    # Try cloning with the determined repo_name
    if try_clone_package(repo_name, package_dir):
        print_colored(f"Successfully cloned {package_name} using repo name: {repo_name}", Colors.GREEN)
        return True
    else:
        print_colored(f"Failed to clone using repo name: {repo_name}", Colors.RED)
    
    # If both attempts fail, ask user for correct repo name
    print_colored(f"Failed to clone repository for {package_name}", Colors.RED)
    print_colored("Examples of package -> repo name mappings:", Colors.YELLOW)
    print_colored("libudev -> udev", Colors.YELLOW)
    print_colored("gcc-libs -> gcc", Colors.YELLOW)
    print_colored("opengl-driver -> lib32-mesa", Colors.YELLOW)
    
    while True:
        repo_name = input(f"{Colors.BLUE}Please enter the correct repository name for {package_name} (or 'skip' to skip this dependency): {Colors.RESET}").strip()
        if repo_name.lower() == 'skip':
            return False
        if try_clone_package(repo_name, package_dir):
            print_colored(f"Successfully cloned {package_name} using repo name: {repo_name}", Colors.GREEN)
            update_repo_mappings(package_name, repo_name, repo_mappings_file)
            return True
        else:
            retry = input(f"{Colors.RED}Failed to clone. Try another repo name? (y/n): {Colors.RESET}").strip().lower()
            if retry != 'y':
                return False

def build_package(package_dir):
    """Build a package using makepkg."""
    try:
        subprocess.run(["makepkg", "-si", "--noconfirm"], cwd=package_dir, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"Failed to build package: {e}", Colors.RED)
        return False

def check_installed_package(package_name):
    """Check if a package is already installed."""
    try:
        result = subprocess.run(
            ["pacman", "-Q", package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def process_dependency(dep_name, repo_mappings, custompkg_dir, repo_mappings_file, processed_deps=None):
    """Process a single dependency, handling recursive dependencies."""
    if processed_deps is None:
        processed_deps = set()
    
    if dep_name in processed_deps:
        return True
    
    if check_installed_package(dep_name):
        print_colored(f"{dep_name} is already installed.", Colors.GREEN)
        return True
    
    print_colored(f"\nProcessing dependency: {dep_name}", Colors.BLUE)
    install_choice = input(f"Do you want to (1) install {dep_name} from package manager or (2) build from source? (1/2): ").strip()
    
    if install_choice == "1":
        try:
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm", dep_name], check=True)
            print_colored(f"Successfully installed {dep_name} from package manager", Colors.GREEN)
            return True
        except subprocess.CalledProcessError:
            print_colored(f"Failed to install {dep_name} from package manager", Colors.RED)
            install_choice = "2"  # Fallback to building from source
    
    if install_choice == "2":
        if handle_package_clone(dep_name, repo_mappings, custompkg_dir, repo_mappings_file):
            package_dir = os.path.join(custompkg_dir, dep_name)
            pkgbuild_path = os.path.join(package_dir, "PKGBUILD")
            
            # Process recursive dependencies
            sub_dependencies = get_package_dependencies(pkgbuild_path)
            for sub_dep in sub_dependencies:
                if sub_dep not in processed_deps:
                    if not process_dependency(sub_dep, repo_mappings, custompkg_dir, repo_mappings_file, processed_deps):
                        return False
            
            # Build the package
            if build_package(package_dir):
                processed_deps.add(dep_name)
                return True
    
    return False

def main():
    home_dir = os.path.expanduser("~")
    custompkg_dir = os.path.join(home_dir, "custompkg")
    repo_mappings_file = os.path.join(home_dir, "repo_mappings.txt")

    # Create custompkg directory if it doesn't exist
    if not os.path.exists(custompkg_dir):
        os.makedirs(custompkg_dir)
        print_colored("custompkg directory created", Colors.GREEN)

    # Load repo mappings
    repo_mappings = {}
    if os.path.exists(repo_mappings_file):
        with open(repo_mappings_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    repo_mappings[parts[0]] = parts[1]
    else:
        print_colored("Creating new repo_mappings.txt file", Colors.YELLOW)
        open(repo_mappings_file, 'w').close()

    # Get package name from user
    package_name = input(f"{Colors.BLUE}Enter package name: {Colors.RESET}").strip()
    
    # Clone and process main package
    if handle_package_clone(package_name, repo_mappings, custompkg_dir, repo_mappings_file):
        package_dir = os.path.join(custompkg_dir, package_name)
        pkgbuild_path = os.path.join(package_dir, "PKGBUILD")
        
        # Ask user if they want to customize PKGBUILD
        customize = input(f"{Colors.BLUE}Do you want to customize the PKGBUILD? (y/n): {Colors.RESET}").strip().lower()
        if customize == 'y':
            subprocess.run(["nano", pkgbuild_path])
        
        # Process dependencies
        dependencies = get_package_dependencies(pkgbuild_path)
        processed_deps = set()
        
        print_colored("\nProcessing dependencies...", Colors.BLUE)
        for dep in dependencies:
            if not process_dependency(dep, repo_mappings, custompkg_dir, repo_mappings_file, processed_deps):
                print_colored(f"Failed to process dependency: {dep}", Colors.RED)
                break
        else:
            print_colored(f"Successfully processed all dependencies for {package_name}", Colors.GREEN)

if __name__ == "__main__":
    main()

