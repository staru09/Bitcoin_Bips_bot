import requests
from urllib.parse import urlparse

class BitcoinSearchCLI:
    def __init__(self, base_url="https://bitcoinsearch.xyz"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
    
    def search_documents(self):
        """Interactive search interface"""
        print("\n=== Bitcoin Search ===")
        
        # Step 1: Get search query
        query = input("Enter search terms: ").strip()
        if not query:
            print("Search query cannot be empty")
            return

        # Step 2: Build search payload
        payload = {"queryString": query, "size": 5, "page": 1}
        
        # Step 3: Filter options
        if input("Add filters? (y/n): ").lower() == 'y':
            payload["filterFields"] = []
            while True:
                field = input("Filter field (domain/authors/tags) or 'done': ").strip().lower()
                if field == 'done':
                    break
                if field not in ['domain', 'authors', 'tags']:
                    print("Invalid field")
                    continue
                
                value = input(f"Value for {field}: ").strip()
                payload["filterFields"].append({
                    "field": f"{field}.keyword",
                    "value": value
                })

        # Step 4: Sorting
        if input("Add sorting? (y/n): ").lower() == 'y':
            payload["sortFields"] = []
            field = input("Sort by (indexed_at/created_at/title): ").strip()
            direction = input("Direction (asc/desc): ").strip().lower()
            payload["sortFields"].append({
                "field": field,
                "value": direction
            })

        # Execute search
        results = self._api_request("/api/elasticSearchProxy/search", payload)
        self._display_search_results(results)

        # Document exploration
        if results and results.get('success'):
            self._explore_search_results(results['data']['result']['hits']['hits'])

    def _explore_search_results(self, hits):
        """Allow user to explore search results by URL"""
        while True:
            choice = input("\nEnter document URL to view, or type [b]ack: ").strip().lower()
            if choice == 'b':
                break
            elif choice.startswith("http"):
                self._view_document_content(choice)
            else:
                print("Invalid input. Please enter a valid URL or 'b' to go back.")


    def explore_sources(self):
        """Interactive source explorer"""
        print("\n=== Source Explorer ===")
        
        # Get all sources first
        sources = self._api_request("/api/elasticSearchProxy/sources", {})
        if not sources or not sources.get('success'):
            print("Failed to fetch sources")
            return

        # Display available sources
        print("\nAvailable Sources:")
        for idx, source in enumerate(sources['data']['result'], 1):
            print(f"{idx}. {source['domain']} ({source['documentCount']} docs)")

        # Select source
        choice = input("\nSelect source (number) or 'back': ").strip()
        if choice == 'back':
            return

        try:
            selected_source = sources['data']['result'][int(choice)-1]
            self._explore_single_source(selected_source['domain'])
        except (ValueError, IndexError):
            print("Invalid selection")

    def _explore_single_source(self, domain):
        """Explore documents from a specific source"""
        while True:
            print(f"\nExploring: {domain}")
            print("View modes:")
            print("1. Flat view (all documents)")
            print("2. Threaded view (grouped by thread)")
            print("3. Summaries view (only combined summaries)")
            print("4. Back to sources list")

            choice = input("Select view mode: ").strip()
            if choice == '4':
                break

            view_modes = {'1': 'flat', '2': 'threaded', '3': 'summaries'}
            if choice not in view_modes:
                print("Invalid choice")
                continue

            view_mode = view_modes[choice]
            page = 1

            while True:
                payload = {
                    "domain": domain,
                    "viewMode": view_mode,
                    "page": page
                }
                if view_mode == 'threaded':
                    payload["threadsPage"] = page

                results = self._api_request("/api/elasticSearchProxy/sourceDocuments", payload)
                self._display_source_documents(results, view_mode)

                if not results or not results.get('success'):
                    break

                nav = input("\n[n]ext, [p]rev, [v]iew doc, [b]ack to view modes: ").strip().lower()

                if nav == 'n':
                    page += 1
                elif nav == 'p' and page > 1:
                    page -= 1
                elif nav == 'v':
                    doc_url = input("Enter document URL to view: ").strip()
                    self._view_document_content(doc_url)
                elif nav == 'b':
                    break
                else:
                    print("Invalid input. Try again.")



    def _view_document_content(self, url):
        """View full document content, wait for 'ok' to close"""
        result = self._api_request("/api/elasticSearchProxy/getDocumentContent", {"url": url})
        if not result or not result.get('success'):
            print("Failed to fetch document")
            return

        doc = result['data']
        print(f"\n=== {doc.get('title', 'Untitled')} ===")
        print(f"URL: {doc.get('url')}")
        print(f"Source: {doc.get('domain')}")
        print(f"Authors: {', '.join(doc.get('authors', []))}")
        print(f"Indexed: {doc.get('indexed_at')}")
        print("\nContent:\n")

        content = doc.get('body', 'No content available')
        chunk_size = 1000
        start = 0

        while start < len(content):
            end = min(start + chunk_size, len(content))
            print(content[start:end])
            start += chunk_size

            if start < len(content):
                cont = input("\nPress Enter to continue or type 'q' to skip remaining content: ").strip().lower()
                if cont == 'q':
                    break

        # Wait for user to finish reading
        while True:
            exit_input = input("\nType 'ok' to return: ").strip().lower()
            if exit_input == 'ok':
                break
            else:
                print("Type 'ok' when you're ready to return.")

    def _display_search_results(self, results):
        """Display search results"""
        if not results or not results.get('success'):
            print("No results found")
            return
            
        data = results['data']['result']
        total = data['hits']['total']['value']
        print(f"\nFound {total} results:")
        
        for idx, hit in enumerate(data['hits']['hits'], 1):
            doc = hit['_source']
            print(f"\n{idx}. {doc.get('title', 'Untitled')}")
            print(f"   URL: {doc.get('url')}")
            print(f"   Source: {doc.get('domain')}")
            if doc.get('authors'):
                print(f"   Authors: {', '.join(doc.get('authors'))}")
            print(f"   Indexed: {doc.get('indexed_at')}")

    def _display_source_documents(self, results, view_mode):
        """Display source documents"""
        if not results or not results.get('success'):
            print("No documents found")
            return
            
        data = results['data']
        print(f"\nView Mode: {view_mode.upper()}")
        print(f"Total Documents: {data['total']}")
        
        for idx, doc in enumerate(data['documents'], 1):
            print(f"\n{idx}. {doc.get('title', 'Untitled')}")
            print(f"   URL: {doc.get('url')}")
            print(f"   Indexed: {doc.get('indexed_at')}")
            if view_mode == 'threaded' and doc.get('thread_url'):
                print(f"   Thread: {doc.get('thread_url')}")
            if doc.get('type'):
                print(f"   Type: {doc.get('type')}")

    def _api_request(self, endpoint, payload):
        """Generic API request handler"""
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {str(e)}")
            return None

    def run(self):
        """Main interactive loop"""
        while True:
            print("\n=== Bitcoin Search CLI ===")
            print("1. Search Documents")
            print("2. Explore Sources")
            print("3. Exit")
            
            choice = input("Select option: ").strip()
            
            if choice == '1':
                self.search_documents()
            elif choice == '2':
                self.explore_sources()
            elif choice == '3':
                print("Goodbye!")
                break
            else:
                print("Invalid option")

if __name__ == "__main__":
    cli = BitcoinSearchCLI()
    cli.run()