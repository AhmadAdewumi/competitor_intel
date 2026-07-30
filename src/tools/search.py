import os
from re import search
from typing import Dict, Any

import requests

from src.core.tool import BaseTool
from src.utils.logger import log


class SearchTool(BaseTool):
    """
    A tool that searches the web using Tavily API.
    it is a search API optimized for AI agents.
    """

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            log.warning("TAVILY_API_KEY not found in environment. Search will fail.")

        super().__init__(
            name="search",
            description="Searches the web for information and returns relevant results with titles, URLs, and snippets.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )

    # def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Execute a web search using DuckDuckGo.
    #
    #     Args:
    #         input_data: {
    #             "query": "search terms",
    #             "max_results": 5 (optional)
    #         }
    #
    #     Returns:
    #         {
    #             "success": bool,
    #             "results": [
    #                 {
    #                     "title": str,
    #                     "url": str,
    #                     "snippet": str
    #                 }
    #             ],
    #             "query": str,
    #             "error": str (if failed)
    #         }
    #     """
    #
    #     # Extract inputs
    #     query = input_data.get("query")
    #     max_results = input_data.get("max_results", 5)
    #
    #     # Validate
    #     if not query:
    #         return {"success": False, "error": "Query is required", "results": []}
    #
    #     log.info(f"Searching for: '{query}' (max_results={max_results})")
    #
    #     try:
    #         # Using DuckDuckGo's free search API
    #         # This uses the HTML search endpoint (no API key needed)
    #         response = requests.get(
    #             "https://api.duckduckgo.com/",
    #             params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
    #             timeout=300,
    #         )
    #
    #         response.raise_for_status()
    #         data = response.json()
    #
    #         # Extract results
    #         results = []
    #
    #         # Get related topics (these are the search results)
    #         related_topics = data.get("RelatedTopics", [])
    #
    #         for topic in related_topics[:max_results]:
    #             # Extract title and URL from the result
    #             text = topic.get("Text", "")
    #             first_url = topic.get("FirstURL", "")
    #
    #             # Try to extract a title from the text
    #             title = text.split(" - ")[0] if " - " in text else text[:100]
    #             snippet = text
    #
    #             results.append({"title": title, "url": first_url, "snippet": snippet})
    #
    #         # If no results from RelatedTopics, try Abstract
    #         if not results and data.get("Abstract"):
    #             results.append(
    #                 {
    #                     "title": data.get("Heading", "Result"),
    #                     "url": data.get("AbstractURL", ""),
    #                     "snippet": data.get("Abstract", ""),
    #                 }
    #             )
    #
    #         log.info(f"Search found {len(results)} results")
    #
    #         return {
    #             "success": True,
    #             "results": results,
    #             "query": query,
    #             "count": len(results),
    #             "error": None,
    #         }
    #
    #     except requests.exceptions.Timeout:
    #         log.error("Search request timed out")
    #         return {"success": False, "error": "Search request timed out", "results": []}
    #     except requests.exceptions.RequestException as e:
    #         log.error(f"Search request failed: {e}")
    #         return {"success": False, "error": f"Search failed: {str(e)}", "results": []}
    #     except Exception as e:
    #         log.error(f"Search error: {e}")
    #         return {"success": False, "error": f"Unexpected error: {str(e)}", "results": []}

#------ tavily
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a web search.

        Args:
            input_data: {
                "query": "search terms",
                "max_results": 5 (optional)
            }

        Returns:
            {
                "success": bool,
                "results": [
                    {
                        "title": str,
                        "url": str,
                        "snippet": str,
                        "score": float (relevance score)
                    }
                ],
                "query": str,
                "error": str (if failed)
            }
        """

        #Extract Digit
        query = input_data.get("query")
        max_results= input_data.get("max_results")

        # validate
        if not query:
            return {"success": False, "error": "Query is required", "results": []}

        if not self.api_key:
            return {
                "success": False,
                "error": "TAVILY_API_KEY not configured. Please add it to .env",
                "results": [],
            }

        log.info(f"Searching for: '{query}' (max_results={max_results})")


        try:
            # call travily api key
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                    "include_raw_content": False
                },
                timeout=30
            )

            # check if the requests succeeded
            response.raise_for_status()

            #parse the response
            data = response.json()
            results = data.get("results", [])

            log.info(f"Search found {len(results)} results")

            return {
                "success": True,
                "results": results,
                "query": query,
                "count": len(results),
                "error": None
            }

        except requests.exceptions.Timeout:
            log.error("Search request timed out")
            return {
                "success": False,
                "error": "Search timed out",
                "results": []
            }

        except requests.exceptions.RequestException as e:
            log.error("Search request failed")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "results": []
            }

        except Exception as e:
            log.error("Unexpected error")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "results": []
            }
