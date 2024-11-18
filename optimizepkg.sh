#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base directory for package building
PACKAGE_DIR="$HOME/packages"
GITEA_BASE_URL="https://gitea.artixlinux.org/packages"

# Log function
log() {
    local level=$1
    shift
    case "$level" in
        "info")
            echo -e "${GREEN}[INFO]${NC} $*"
            ;;
        "warn")
            echo -e "${YELLOW}[WARN]${NC} $*"
            ;;
        "error")
            echo -e "${RED}[ERROR]${NC} $*"
            ;;
    esac
}

# Error handling
set -e
trap 'log error "An error occurred on line $LINENO. Exiting..."; exit 1' ERR

# Check if required commands exist
check_requirements() {
    local required_commands=("git" "pacman" "makepkg")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log error "$cmd is required but not installed. Please install it first."
            exit 1
        fi
    done
}

# Initialize package directory
init_package_dir() {
    if [[ ! -d "$PACKAGE_DIR" ]]; then
        log info "Creating package directory at $PACKAGE_DIR"
        mkdir -p "$PACKAGE_DIR"
    fi
}

# Clone package repository
clone_package() {
    local package_name=$1
    local repo_url="$GITEA_BASE_URL/$package_name"
    local package_path="$PACKAGE_DIR/$package_name"

    if [[ -d "$package_path" ]]; then
        log info "Updating existing repository for $package_name"
        (cd "$package_path" && git pull)
    else
        log info "Cloning repository for $package_name"
        git clone "$repo_url" "$package_path"
    fi
}

# Parse dependencies from PKGBUILD
parse_dependencies() {
    local pkgbuild_path=$1
    local deps=()
    
    # Source PKGBUILD in a subshell to get variables
    source "$pkgbuild_path"
    
    # Combine all dependency arrays
    deps+=("${depends[@]}" "${makedepends[@]}" "${checkdepends[@]}")
    
    echo "${deps[@]}"
}

# Build package
build_package() {
    local package_name=$1
    local package_path="$PACKAGE_DIR/$package_name"
    local pkgbuild_path="$package_path/trunk/PKGBUILD"

    if [[ ! -f "$pkgbuild_path" ]]; then
        log error "PKGBUILD not found for $package_name"
        return 1
    }

    log info "Building $package_name"
    
    # Change to package directory
    cd "$package_path/trunk"
    
    # Handle dependencies
    local dependencies
    dependencies=($(parse_dependencies "$pkgbuild_path"))
    
    for dep in "${dependencies[@]}"; do
        # Remove version constraints
        dep=${dep%%[<>=]*}
        
        # Check if dependency is already installed
        if ! pacman -Q "$dep" >/dev/null 2>&1; then
            log info "Installing dependency: $dep"
            if ! sudo pacman -S --needed --noconfirm "$dep"; then
                # If not found in repos, try building it
                build_package "$dep"
            fi
        fi
    done
    
    # Build package
    makepkg -si --noconfirm

    # Clean up
    log info "Cleaning up build files"
    rm -rf src pkg
}

# Handle system upgrade
handle_system_upgrade() {
    log info "Checking for system updates"
    
    # Get list of packages that need updating
    local updates
    updates=$(pacman -Qu | cut -d' ' -f1)
    
    if [[ -z "$updates" ]]; then
        log info "System is up to date"
        return 0
    fi
    
    log info "Building and installing updates for:"
    echo "$updates"
    
    for pkg in $updates; do
        build_package "$pkg"
    done
}

# Main function
main() {
    local package_name=$1
    
    if [[ -z "$package_name" ]]; then
        log error "Please provide a package name"
        exit 1
    fi
    
    check_requirements
    init_package_dir
    
    if [[ "$package_name" == "syu" ]]; then
        handle_system_upgrade
    else
        clone_package "$package_name"
        build_package "$package_name"
    fi
}

# Execute main function with all arguments
main "$@"
