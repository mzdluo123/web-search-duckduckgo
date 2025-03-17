# DuckDuckGo Web Search MCP Server

This project provides an MCP (Model Context Protocol) server that allows you to search the web using the DuckDuckGo search engine and optionally fetch and summarize the content of the found URLs.

## Features

*   **Web Search:** Search the web using DuckDuckGo.
*   **Result Extraction:** Extracts titles, URLs, and snippets from search results.
*   **Content Fetching (Optional):** Fetches the content of the URLs found in the search results and converts it to markdown format using jina api.
*   **Parallel Fetching:** Fetches multiple URLs concurrently for faster processing.
*   **Error Handling:** Gracefully handles timeouts and other potential errors during search and fetching.
*   **Configurable:** Allows you to set the maximum number of search results to return.
* **Jina API**: using jina api to convert html to markdown.
* **MCP Compliant**: This server is designed to be used with any MCP-compatible client.

## Usage

1.  **Prerequisites:**
    *   `uvx` package manager


2. **Claude Desktop Configuration**
    * If you are using Claude Desktop, you can add the server to the `claude_desktop_config.json` file.
    ```json
    {
        "mcpServers": {
            "web-search-duckduckgo": {
                "command": "uvx",
                "args": [
                    "--from",
                    "git+https://github.com/kouui/web-search-duckduckgo.git@main",
                    "main.py"
                ]
            }
        }
    }
    ```

3. **Tool**
    *   In your MCP client (e.g., Claude), you can now use the following tools:

    *   **`search_and_fetch`:** Search the web and fetch the content of the URLs.

        *   `query`: The search query string.
        *   `limit`: The maximum number of results to return (default: 3, maximum: 10).


    *   **`fetch`:** Fetch the content of a specific URL.

        *   `url`: The URL to fetch.


## License

This project is licensed under the MIT License. (Add a license file if you want to specify a license).
