# Bitcoin Search CLI

The **Bitcoin Search CLI** is a command-line tool designed to interact with the BitcoinSearch API. It allows users to search for Bitcoin-related documents, explore sources, and view document content in an interactive manner.

## Features

- **Search Documents**: Perform advanced searches with filters and sorting options.
- **Explore Sources**: Browse and explore documents from specific sources.
- **View Document Content**: Fetch and display the full content of documents.

## Prerequisites

- Python 3.6 or higher
- `requests` library (`pip install requests`)

## Installation

1. Clone the repository or download the script.
2. Ensure you have Python installed on your system.
3. Install the required dependencies:
    ```bash
    pip install requests
    ```

## Usage

1. Run the script:
    ```bash
    python <script_name>.py
    ```

2. Follow the interactive prompts to:
    - Search for documents.
    - Explore sources.
    - View document content.

### Main Menu Options

1. **Search Documents**:
    - Enter search terms.
    - Optionally add filters (e.g., by domain, authors, or tags).
    - Optionally add sorting (e.g., by indexed date, creation date, or title).
    - View search results and explore document URLs.

2. **Explore Sources**:
    - View a list of available sources.
    - Select a source to explore its documents.
    - Choose a view mode (flat, threaded, or summaries).
    - Navigate through documents and view their content.

3. **Exit**:
    - Exit the CLI tool.

## Example Workflow

1. **Search Documents**:
    - Enter search terms: `Bitcoin`
    - Add filters: `domain = bitcoin.org`
    - Add sorting: `indexed_at desc`
    - View results and select a document URL to explore.

2. **Explore Sources**:
    - Select a source (e.g., `bitcoin.org`).
    - Choose a view mode (e.g., `flat`).
    - Navigate through documents and view their content.

## Notes
All data is fetched from the Bitcoin Search API: https://bitcoinsearch.xyz

This CLI is a user-facing client for exploring Bitcoin documentation and discussions.
