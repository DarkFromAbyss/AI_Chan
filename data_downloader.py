import os
import gdown
import zipfile

import logging
from tqdm import tqdm
from urllib.parse import urlparse

import argparse
import yaml

def download_and_extract_data(gdrive_url: str, target_dir: str):
    """
    Downloads data from a shared Google Drive URL (file or folder) and saves it to the specified target directory.
    Automatically extracts .zip files and deletes the original archive.
    Creates necessary subdirectories if they do not exist.

    Args:
        gdrive_url (str): The shared Google Drive URL (file or folder link).
        target_dir (str): The target directory path to save the data.

    Raises:
        Exception: If download fails due to invalid URL, connection issues, or other errors.
    """
    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)

    # Define subdirectories to create
    subdirs = ['vector_store', 'raw_datasets', 'processed_datasets']
    for sub in subdirs:
        os.makedirs(os.path.join(target_dir, sub), exist_ok=True)

    try:
        # Check if the URL is a folder link (contains '/folders/')
        parsed_url = urlparse(gdrive_url)
        if 'folders' in parsed_url.path:
            # Download the entire folder with progress
            downloaded_files = gdown.download_folder(gdrive_url, output=target_dir, quiet=False)  # quiet=False to show progress
            print("Downloaded files:")
            for file in downloaded_files:
                print(f"  - {os.path.basename(file)}")
        else:
            # Download the single file with progress
            downloaded_file = gdown.download(gdrive_url, output=target_dir, quiet=False, fuzzy=True)  # quiet=False for progress

            if downloaded_file and os.path.isfile(downloaded_file):
                print(f"Downloaded: {os.path.basename(downloaded_file)}")
                # Check if the downloaded file is a .zip archive
                if downloaded_file.lower().endswith('.zip'):
                    # Extract the zip file into the target directory with progress
                    with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        with tqdm(total=len(file_list), desc="Extracting", unit="file") as pbar:
                            for file in file_list:
                                zip_ref.extract(file, target_dir)
                                pbar.update(1)
                    # Delete the original zip file after extraction
                    os.remove(downloaded_file)
                    print(f"Extracted and removed: {os.path.basename(downloaded_file)}")

        print("Download and extraction completed successfully.")

    except Exception as e:
        print(f"Error during download: {e}")
        raise

def print_directory_tree(root_dir: str):
    """
    Scans the specified directory and prints a visual directory tree to the console,
    similar to the 'tree' command in Linux.

    Args:
        root_dir (str): The root directory to scan and print.
    """
    def _print_tree(dir_path: str, prefix: str = ""):
        try:
            items = sorted(os.listdir(dir_path))
        except PermissionError:
            return

        for i, item in enumerate(items):
            path = os.path.join(dir_path, item)
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            print(prefix + connector + item)
            if os.path.isdir(path):
                extension = "    " if is_last else "│   "
                _print_tree(path, prefix + extension)

    if os.path.exists(root_dir):
        print(root_dir)
        _print_tree(root_dir)
    else:
        print(f"Directory {root_dir} does not exist.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and extract data from a Google Drive URL to the specified directory.")
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="The shared Google Drive URL (file or folder link) to download from."
    )
    parser.add_argument(
        "--file", "-f",
        default="./data",
        help="The target directory to save the downloaded data (default: ./data)."
    )
    
    args = parser.parse_args()

    target_dir = args.file

    # Load or create config.yaml
    config_file = 'config.yaml'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # Update the data_directory
    config['data_directory'] = target_dir

    # Save back to config.yaml
    with open(config_file, 'w') as f:
        yaml.safe_dump(config, f)

    gdrive_url = args.url
    download_and_extract_data(gdrive_url, target_dir)
    print_directory_tree(target_dir)