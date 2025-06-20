from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
from bs4 import BeautifulSoup
import asyncio


# Initialize FastMCP and load environment variables
mcp = FastMCP("search")
load_dotenv()

USER_AGENT = "search-app/1.0"
DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"

async def search_duckduckgo(query: str, limit: int) -> list:
    """Fetch search results from DuckDuckGo"""
    try:
        # Format query for URL
        formatted_query = query.replace(" ", "+")
        url = f"{DUCKDUCKGO_URL}?q={formatted_query}"
        
        # Set headers to avoid blocking
        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            # Parse HTML response
            soup = BeautifulSoup(response.text, "html.parser")
            result_elements = soup.select('.result__body')
            
            # Extract results up to limit
            results = []
            for result in result_elements[:limit]:
                title_elem = result.select_one('.result__a')
                url_elem = result.select_one('.result__url')
                snippet_elem = result.select_one('.result__snippet')
                
                if title_elem and url_elem:
                    result_dict = {
                        "title": title_elem.get_text().strip(),
                        "url": url_elem.get_text().strip(),
                        "snippet": snippet_elem.get_text().strip() if snippet_elem else ""
                    }
                    results.append(result_dict)
            
            return results
            
    except httpx.TimeoutException:
        return [{"error": "Request timed out"}]
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]
    

async def fetch_url(url: str):
    jina_timeout = 15.0
    raw_html_timeout = 5.0
    url = f"https://r.jina.ai/{url}"
    async with httpx.AsyncClient() as client:
        try:
            print(f"fetching result from\n{url}")
            response = await client.get(url, timeout=jina_timeout)
            """ using jina api to convert html to markdown """
            text = response.text
            return text
        except httpx.TimeoutException:
            try:
                print("Jina API timed out, fetching raw HTML...")
                response = await client.get(url, timeout=raw_html_timeout)
                """ using raw html """
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text()
                return text
            except httpx.TimeoutException:
                return "Timeout error"

@mcp.tool()
async def search_and_fetch(query: str, limit: int = 3):
    """
    Search the web using DuckDuckGo and return results.

    Args:
        query: The search query string
        limit: Maximum number of results to return (default: 3, maximum 10)

    Returns:
        List of dictionaries containing 
        - title
        - url
        - snippet 
        - summary markdown (empty if not available)
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")
    
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("Limit must be a positive integer")
    
    # Cap limit at reasonable maximum
    limit = min(limit, 10)
    
    results = await search_duckduckgo(query, limit)
    
    if not results:
        return [{"message": f"No results found for '{query}'"}]
    
    # Create a list of fetch_url coroutines
    fetch_tasks = [fetch_url(item["url"]) for item in results]
    
    # Execute all fetch requests in parallel and wait for results
    summaries = await asyncio.gather(*fetch_tasks)
    
    # Assign summaries to their respective result items
    for item, summary in zip(results, summaries):
        item["summary"] = summary
    
    return results

# @mcp.tool()
async def search(query: str, limit: int = 3):
    """
    Search the web using DuckDuckGo and return results without scraping.

    Args:
        query: The search query string
        limit: Maximum number of results to return (default: 3, maximum 10)

    Returns:
        List of dictionaries containing 
        - title
        - url
        - snippet 
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")
    
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("Limit must be a positive integer")
    
    # Cap limit at reasonable maximum
    limit = min(limit, 10)
    
    results = await search_duckduckgo(query, limit)
    
    if not results:
        return [{"message": f"No results found for '{query}'"}]
    
    return results

@mcp.tool()
async def fetch(url: str):
    """
    scrape the html content and return the markdown format using jina api.

    Args:
        url: The search query string

    Returns:
        text : html in markdown format 
    """
    if not isinstance(url, str):
        raise ValueError("Query must be a non-empty string")
    
    text = await fetch_url(url)
    
    return text

def test_fetch_url():
    import asyncio
    async def run_test():
        # Mocking. In a real test, you would mock this, but for this example, we will call a real url.
        result = await fetch_url("communityforums.atmeta.com/t5/Get-Help/Beat-saber-wont-load/td-p/1187498")
        # In a real test you would assert the returned result with a known good result.
        # For this example, we will just test that a result is returned.
        assert isinstance(result, str)
        # Add more specific assertions here.
        print("result recieved")
        print(result)

    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"Test failed: {e}")
        assert False

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()