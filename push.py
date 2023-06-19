import argparse
import pysftp
import os
import stat
from datetime import datetime, timedelta

parser = argparse.ArgumentParser()
parser.add_argument('--local_path', default='/home/minecraft/backup/OriginalBackups/')
parser.add_argument('--sftp_path', default='/home/originalbackups')
parser.add_argument('--hostname', default='u353654.your-storagebox.de')
parser.add_argument('--port', type=int, default=23)
parser.add_argument('--username', default='u353654')
parser.add_argument('--only_second_last', type=bool, default=False)
args = parser.parse_args()

local_path = args.local_path
sftp_path = args.sftp_path
hostname = args.hostname
port = args.port
username = args.username
only_second_last = args.only_second_last

def remove_old_archives(sftp, folder_path):
    today = datetime.now().date()

    # Get the list of files and folders within the folder_path
    files = sftp.listdir_attr(folder_path)

    for file_attr in files:
        file_name = file_attr.filename
        file_path = f"{folder_path}/{file_name}"

        if stat.S_ISDIR(file_attr.st_mode):  # If it's a directory
            remove_old_archives(sftp, file_path)  # Recursively search within the subfolder
        elif file_name.endswith('.tar.gz'):
            file_date = datetime.strptime(file_name.split('.')[0], "%Y-%m-%d_%H-%M-%S").date()
            days_old = (today - file_date).days
            if days_old > 21:
                print(f"Removing file '{file_path}'")
                try:
                    sftp.remove(file_path)
                except IOError as e:
                    print(f"Failed to remove file '{file_path}': {e}")

# Create a connection to the SFTP server
with pysftp.Connection(host=hostname, port=port, username=username) as sftp:
    # Change to the desired directory on the server
    sftp.chdir('/')

    # Check if the directory already exists on the server
    if not sftp.isdir(sftp_path):
        try:
            # Create the desired directory structure on the server
            sftp.makedirs(sftp_path)
        except OSError as e:
            print(f"Failed to create directory '{sftp_path}': {e}")
            exit(1)

    # Change to the desired directory on the server
    sftp.chdir(sftp_path)

    # Walk through the local directory and upload files
    for root, dirs, files in os.walk(local_path):
        # Create the corresponding directory structure on the server
        for dir_name in dirs:
            remote_dir = os.path.join(root.replace(local_path, ''), dir_name)
            if not sftp.isdir(remote_dir):
                try:
                    sftp.makedirs(remote_dir)
                except OSError as e:
                    print(f"Failed to create directory '{remote_dir}': {e}")

        # Sort files by creation time and get the second last one if needed
        if only_second_last:
            files = sorted(files, key=lambda f: os.stat(os.path.join(root, f)).st_mtime)
            if len(files) > 1:
                files = [files[-2]]

        # Upload each file to the server if it doesn't already exist
        for file_name in files:
            local_file = os.path.join(root, file_name)
            remote_file = os.path.join(root.replace(local_path, ''), file_name)

            # Check if the file already exists on the server
            if sftp.exists(remote_file):
                print(f"File '{remote_file}' already exists on the server. Skipping upload.")
                continue

            # Upload the file to the server
            sftp.put(local_file, remote_file)

    # Remove archives older than 21 days
    today = datetime.now().date()

    print("Archives to be removed:")

    remove_old_archives(sftp, sftp_path)

print("File transfer and cleanup completed.")
