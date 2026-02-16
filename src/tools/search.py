import os
from typing import Optional, Literal
from tavily import TavilyClient

class SearchTool:
    """Web search tool using Tavily API for trip planning queries."""
    
    def __init__(self):
        """Initialize Tavily client with API key."""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        self.client = TavilyClient(api_key=api_key)
    
    def search(self, query: str, search_depth: Literal["basic", "advanced", "fast", "ultra-fast"] = "basic", max_results: int = 5) -> dict:
        """
        Perform a web search using Tavily API.
        
        Args:
            query: Search query for trip planning
            search_depth: "basic", "advanced", "fast", or "ultra-fast" search depth
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=True
            )
            return response
        except Exception as e:
            return {"error": str(e), "query": query}
    
    def search_destination(self, destination: str, query_type: str = "general") -> dict:
        """
        Search for destination-specific information.
        
        Args:
            destination: City or location name
            query_type: Type of search ("attractions", "restaurants", "accommodations", "general")
            
        Returns:
            Search results for the destination
        """
        queries = {
            "attractions": f"Best attractions and things to do in {destination}",
            "restaurants": f"Top rated restaurants and food in {destination}",
            "accommodations": f"Best hotels and accommodations in {destination}",
            "general": f"Travel guide and information about {destination}"
        }
        
        search_query = queries.get(query_type, queries["general"])
        return self.search(search_query, max_results=5)
    
    def search_flights(self, origin: str, destination: str, date: Optional[str] = None) -> dict:
        """
        Search for flight information.
        
        Args:
            origin: Departure city/airport
            destination: Arrival city/airport
            date: Travel date (optional)
            
        Returns:
            Flight search results
        """
        query = f"Flights from {origin} to {destination}"
        if date:
            query += f" on {date}"
        
        return self.search(query, max_results=5)