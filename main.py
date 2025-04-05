from config import settings
import logging
from celery import group
from parsers.tasks import parse_city_task
from indexing.tasks import build_all_indices_task, search_index_task, search_all_cities_task
import json
import time


logging.basicConfig(level=logging.INFO if settings.DEBUG_MODE else logging.ERROR, 
                    format='%(asctime)s [%(levelname)s] %(message)s')


def main():
    # Start data parsing
    # logging.info("Starting data parsing...")
    # task_group = group(parse_city_task.s(city) for city in settings.CITIES)
    # result = task_group.apply_async()
    # results = result.get()
    
    # Start indexing after parsing completes
    logging.info("Starting data indexing...")
    index_result = build_all_indices_task.delay()
    index_results = index_result.get()
    
    # Run search tests if indexing was successful
    if index_results.get("status") == "success":
        run_search_tests()
    
    logging.info("All tasks completed!")
    # return {"parse_results": results, "index_results": index_results}


def run_search_tests():
    """Run a series of search tests to demonstrate the search functionality."""
    logging.info("Running search tests...")
    
    # Define test cases
    test_cases = [
        {"name": "Simple search", "city": settings.CITIES[0], "query": "музей", "limit": 5},
        {"name": "Wildcard search - prefix", "city": settings.CITIES[0], "query": "музе*", "limit": 5},
        {"name": "Wildcard search - suffix", "city": settings.CITIES[0], "query": "*театр", "limit": 5},
        {"name": "Wildcard search - middle", "city": settings.CITIES[0], "query": "рест*ран", "limit": 5},
        {"name": "Multi-city search", "query": "парк", "cities": settings.CITIES, "limit": 10}
    ]
    
    # Run each test case
    for i, test in enumerate(test_cases):
        logging.info(f"Test {i+1}: {test['name']}")
        
        # Execute the search
        start_time = time.time()
        if "cities" in test:
            # Multi-city search
            result = search_all_cities_task.delay(test["query"], test.get("cities"), test.get("limit", 10))
            search_results = result.get()
        else:
            # Single city search
            result = search_index_task.delay(test["city"], test["query"], test.get("limit", 10))
            search_results = result.get()
        
        # Calculate search time
        search_time = time.time() - start_time
        
        # Process and display results
        status = search_results.get("status")
        results_count = len(search_results.get("results", []))
        total_found = search_results.get("total_found", 0)
        message = search_results.get("message", "No message")
        
        logging.info(f"Search completed in {search_time:.2f}s - Status: {status}")
        logging.info(f"Results: {results_count}/{total_found} - {message}")
        
        # Print top results
        results = search_results.get("results", [])
        if results:
            logging.info("Top results:")
            for j, res in enumerate(results[:3]):  # Show only top 3 for brevity
                name = res.get("name", "Unknown")
                score = res.get("score", 0)
                location_type = res.get("type", "Unknown type")
                city = res.get("city", test.get("city", "unknown"))
                logging.info(f"  {j+1}. {name} ({city}) - {location_type} - Score: {score:.4f}")
            
            # Save results to file for detailed inspection
            with open(f"tests/search_test_{i+1}_{test['name'].replace(' ', '_').lower()}.json", "w", encoding="utf-8") as f:
                json.dump(search_results, f, ensure_ascii=False, indent=2)
        else: logging.warning(f"No results for test {i+1}: {test}\ntokens:{search_results.get('query_tokens', [])}")
        
        # Pause between tests
        time.sleep(1)
    
    logging.info("All search tests completed")


def only_search_tests():
    """
    Run only search tests without data parsing and indexing.
    Useful when indices are already built and you want to test search functionality.
    """
    logging.info("Running only search tests (skipping parsing and indexing)...")
    run_search_tests()
    return {"status": "success", "message": "Search tests completed"}


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--only-search":
        only_search_tests()
    else:
        main()