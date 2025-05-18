from typing import Dict, List, Any


def prepare_context_from_results(
        search_results: Dict, 
        limit: int
    ) -> str:
    """
    Prepare a formatted context string from search results for the LLM.
    """
    detailed_results = search_results.get("detailed_results", [])[:limit]
    context_items = ['City: ' + detailed_results[0].get("city", "Unknown")]
    
    for i, res in enumerate(detailed_results):
        context_items.append(f"[Place {res['doc_id']}]: {res.get('name', '')}")
        context_items.append(f"Address: {res.get('address', '')}")
        context_items.append(f"Types: {', '.join(res.get('types', []))}")
        context_items.append(f"Other information: {res.get('search_text', '')}")
        context_items.append(f"Reviews: {res.get('reviews_flattened', '')}")
        context_items.append("")
        
    return "\n".join(context_items) 