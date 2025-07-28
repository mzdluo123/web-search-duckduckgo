from mcp.server.fastmcp import FastMCP
#from dotenv import load_dotenv
import httpx
from bs4 import BeautifulSoup
import asyncio
from markdownify import markdownify as md


# Initialize FastMCP and load environment variables
# mcp = FastMCP("search",settings={
#     "port":8000
# })
mcp = FastMCP("search")
#load_dotenv()

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
    

async def fetch_url(url: str, client: httpx.AsyncClient):
    """
    Fetch the content of a URL using a provided httpx.AsyncClient.
    优先用 Jina API 获取 markdown，超时则回退到原始 HTML。
    建议调用方复用 client。
    """
    jina_timeout = 30.0
    raw_html_timeout = 5.0
    jina_url = f"https://r.jina.ai/{url}"
    # Jina API重试3次
    for attempt in range(3):
        try:
            response = await client.get(jina_url, timeout=jina_timeout, headers={"X-Retain-Images": "none",
                                                                                 "X-With-Links-Summary": "all"})
            # using jina api to convert html to markdown
            return response.text
        except httpx.TimeoutException:
            if attempt < 2:
                await asyncio.sleep(1)
            else:
                try:
                    response = await client.get(jina_url, timeout=raw_html_timeout)
                    # using raw html
                    soup = BeautifulSoup(response.text, "html.parser")
                    return soup.get_text()
                except httpx.TimeoutException:
                    return "Timeout error"
                
# async def fetch_url(url: str, client: httpx.AsyncClient):
#     html_timeout = 5.0
#     if not url.startswith("http"):
#         url = "http://" + url  # Ensure URL starts with http:// or https://
#     # 重试3次
#     for attempt in range(3):
#         try:
#             response = await client.get(url, timeout=html_timeout, follow_redirects=True)
#             return md(response.text)
#         except httpx.TimeoutException:
#             if attempt < 2:
#                 await asyncio.sleep(1)
#             else:
#                 try:
#                     response = await client.get(url, timeout=html_timeout)
#                     # using raw html
#                     soup = BeautifulSoup(response.text, "html.parser")
#                     return md(soup.get_text())
#                 except httpx.TimeoutException:
#                     return "Timeout error"

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
    
    # 复用 httpx.AsyncClient
    async with httpx.AsyncClient() as client:
        fetch_tasks = [fetch_url(item["url"], client) for item in results]
        summaries = await asyncio.gather(*fetch_tasks)
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
    
    async with httpx.AsyncClient() as client:
        text = await fetch_url(url, client)
    return text

def test_fetch_url():
    import asyncio
    async def run_test():
            result = await search_and_fetch("hello")
            print(result)
            assert isinstance(result, str)
            print("result recieved")
            print(result)

    
    asyncio.run(run_test())


def main():
    mcp.run(transport="stdio")
    #mcp.run(transport="sse")

if __name__ == "__main__":
    main()
    #test_fetch_url()