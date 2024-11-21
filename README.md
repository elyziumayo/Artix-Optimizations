# Custom makepkg.conf & Build Script

This repository provides a custom `makepkg.conf` for optimization and a script that automates the process of fetching, building, and installing packages. The script will prompt the user for the package name, fetch the source, and handle dependencies.

## Features

- **Custom `makepkg.conf`**: Optimized configuration to speed up and improve the building process of Arch Linux packages.
- **Automated Build Script**: A script that prompts the user for the package name, fetches the source, and builds the package, including the installation of necessary dependencies.

## Usage

### Custom `makepkg.conf`

The `makepkg.conf` in this repository includes optimizations for a faster and more efficient build process. To use this configuration:

1. Copy the `makepkg.conf` to `/etc/makepkg.conf`:
   ```bash
   sudo cp makepkg.conf /etc/makepkg.conf
