#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check and create optimize folder
create_optimize_folder() {
    local optimize_dir="$HOME/optimize"
    if [ ! -d "$optimize_dir" ]; then
        echo -e "${YELLOW}Creating optimize folder in home directory...${NC}"
        mkdir -p "$optimize_dir"
    fi
    echo "$optimize_dir"
}

# Function to clone package repository
clone_package_repo() {
    local package_name="$1"
    local optimize_dir="$2"
    local repo_url="https://gitea.artixlinux.org/packages/${package_name}"
    
    echo -e "${YELLOW}Cloning package repository for ${package_name}...${NC}"
    git clone "$repo_url" "${optimize_dir}/${package_name}"
}

# Function to extract dependencies from PKGBUILD
extract_dependencies() {
    local pkgbuild_path="$1"
    
    # Extract dependencies using grep, removing comments and the libcairo.so entry
    local dependencies=$(grep -E "^(make)?depends=" "$pkgbuild_path" | \
                         sed -E "s/^(make)?depends=\(|\)//g" | \
                         tr -d "'" | tr ' ' '\n' | \
                         grep -v -E "(#|libcairo.so)")  # Exclude comments and libcairo.so
    
    echo "$dependencies"
}

# Function to build and install a package
build_and_install_package() {
    local package_path="$1"
    
    cd "$package_path" || exit 1
    
    echo -e "${YELLOW}Building package...${NC}"
    makepkg -si --noconfirm
}

# Main script
main() {
    # Create optimize folder
    optimize_dir=$(create_optimize_folder)
    
    # Ask user for package name
    read -p "Enter the package name to build: " package_name
    
    # Clone package repository
    clone_package_repo "$package_name" "$optimize_dir"
    package_path="${optimize_dir}/${package_name}"
    
    # Find PKGBUILD file
    pkgbuild_file="${package_path}/PKGBUILD"
    
    if [ ! -f "$pkgbuild_file" ]; then
        echo -e "${RED}Error: PKGBUILD file not found!${NC}"
        exit 1
    fi
    
    # Extract and process dependencies
    dependencies=$(extract_dependencies "$pkgbuild_file")
    
    echo -e "${GREEN}Found dependencies:${NC}"
    echo "$dependencies"
    
    # Build and install dependencies
    for dep in $dependencies; do
        echo -e "${YELLOW}Processing dependency: ${dep}${NC}"
        
        # Clone dependency repository
        clone_package_repo "$dep" "$optimize_dir"
        dep_path="${optimize_dir}/${dep}"
        
        # Build and install dependency
        build_and_install_package "$dep_path"
    done
    
    # Build and install main package
    echo -e "${GREEN}Building main package: ${package_name}${NC}"
    build_and_install_package "$package_path"
    
    # Clean up make dependencies
    echo -e "${YELLOW}Cleaning up make dependencies...${NC}"
    cd "$package_path" && makepkg -c
    
    echo -e "${GREEN}Package ${package_name} and its dependencies have been successfully built and installed!${NC}"
}

# Run the main 
main

