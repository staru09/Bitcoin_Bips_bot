import os
import requests
import argparse
import csv
from dotenv import load_dotenv

load_dotenv
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_github_contents(repo_url):
    parts = repo_url.rstrip('/').split('/')

    if len(parts) < 5 or parts[2] != "github.com":
        raise ValueError("Invalid GitHub URL. Ensure the URL is in the format: https://github.com/user/repo/tree/branch/path")

    user = parts[3]
    repo = parts[4]

    if "tree" in parts:
        branch = parts[6]
        subpath = '/'.join(parts[7:]) if len(parts) > 7 else ''
        api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{subpath}?ref={branch}"
    else:
        api_url = f"https://api.github.com/repos/{user}/{repo}/contents/"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    return response.json()


def process_contents(contents, paths=[], parent_path="", exclude_folders=[]):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    for item in contents:
        path = parent_path + item['name']
        extension = os.path.splitext(path)[1]

        if item['type'] == 'dir' and item['name'] in exclude_folders:
            print(f"Skipping folder: {path}")
            continue

        if item['type'] == 'dir':
            dir_response = requests.get(item['url'], headers=headers)
            dir_response.raise_for_status()
            dir_contents = dir_response.json()
            process_contents(dir_contents, paths, path + "/", exclude_folders)

        elif item['type'] == 'file':
            if extension not in ['.md', '.mediawiki']:
                print(f"Skipping file: {path}")
                continue

            print(f"Processing: {path}")
            file_response = requests.get(item['download_url'], headers=headers)
            file_response.raise_for_status()
            file_content = file_response.text
            paths.append({"Path": path, "Content": file_content})

    print(f"Finished processing. Total files processed: {len(paths)}.")
    return paths


def transform_and_write_csv(data, output_csv):
    with open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        for row in data:
            path = row['Path']
            content = row['Content']
            extension = os.path.splitext(path)[1]

            if extension == '.md':
                formatted_content = f"The following is a markdown document located at {path}\n------\n{content}\n------"
            elif extension == '.mediawiki':
                formatted_content = f"The following is a mediawiki document located at {path}\n------\n{content}\n------"
            else:
                continue  # Should not happen due to earlier filtering

            writer.writerow([formatted_content])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch only .mediawiki and .md files from a GitHub repository and save to a CSV file.")
    parser.add_argument("repo_url", help="URL of the GitHub repository (e.g., https://github.com/user/repo/tree/branch)")
    parser.add_argument("output_path", help="Path to the output CSV file")
    parser.add_argument("--exclude", nargs='*', default=[], help="List of folder names to exclude")

    args = parser.parse_args()

    try:
        print(f"Starting script for repository: {args.repo_url}")
        contents = get_github_contents(args.repo_url)
        paths = process_contents(contents, exclude_folders=args.exclude)
        transform_and_write_csv(paths, args.output_path)
        print(f"CSV file '{args.output_path}' generated successfully.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
