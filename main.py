from config import settings
import logging
from celery import group
from parsers.tasks import parse_city_task
from indexing.tasks import build_all_indices_task, search_index_task, search_all_cities_task
from tree_based_retrieval.tasks import build_all_cities_ball_trees_task, search_ball_tree_task, search_all_cities_ball_tree_task
import json
import time
import os


logging.basicConfig(level=logging.INFO if settings.DEBUG_MODE else logging.ERROR, 
                    format='%(asctime)s [%(levelname)s] %(message)s')


def main():
    # Start data parsing
    logging.info("Starting data parsing...")
    task_group = group(parse_city_task.s(city) for city in settings.CITIES)
    result = task_group.apply_async()
    results = result.get()
    
    # Start indexing and ball tree building in parallel
    logging.info("Starting data indexing and ball tree building in parallel...")
    index_result = build_all_indices_task.delay()
    ball_tree_result = build_all_cities_ball_trees_task.delay()
    
    # Wait for both tasks to complete
    index_results = index_result.get()
    ball_tree_results = ball_tree_result.get()
    
    # Run search tests if both tasks were successful
    if index_results.get("status") == "success" and ball_tree_results.get("status") == "success":
        run_search_tests()
        run_ball_tree_search_tests()
    else:
        if index_results.get("status") != "success":
            logging.error(f"Indexing failed: {index_results.get('message', 'Unknown error')}")
        if ball_tree_results.get("status") != "success":
            logging.error(f"Ball tree building failed: {ball_tree_results.get('message', 'Unknown error')}")
    
    logging.info("All tasks completed!")


def run_search_tests():
    """Run a series of search tests to demonstrate the inverted index search functionality."""
    test_cases = [
        {
            "name": "Single city search - Moscow restaurants",
            "city": "Москва",
            "query": "restaurant",
            "limit": 5
        },
        {
            "name": "Single city search - Saint Petersburg museums",
            "city": "Санкт-Петербург",
            "query": "museum",
            "limit": 5
        },
        {
            "name": "Multi-city search - All restaurants",
            "query": "restaurant",
            "cities": settings.CITIES,
            "limit": 5
        },
        {
            "name": "Wildcard search - All cafes and restaurants",
            "query": "rest*",
            "cities": settings.CITIES,
            "limit": 5
        }
    ]
    
    # Create tests directory if it doesn't exist
    os.makedirs("tests", exist_ok=True)
    
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
        for j, result in enumerate(results[:test.get("limit", 5)]):
            logging.info(f"{j+1}. {result.get('name', 'Unknown')} - Score: {result.get('score', 0):.3f}")
        
        # Save results to file
        test_name = test["name"].lower().replace(" ", "_")
        filename = f"tests/search_test_{i+1}_{test_name}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(search_results, f, ensure_ascii=False, indent=2)
        logging.info(f"Test results saved to {filename}")


def run_ball_tree_search_tests():
    """Run a series of search tests to demonstrate the ball tree search functionality."""
    test_cases = [
        {
            "name": "Single city semantic search - Moscow restaurants",
            "city": "Москва",
            "query": "место где можно поесть",
            "limit": 5
        },
        {
            "name": "Single city semantic search - Saint Petersburg cultural places",
            "city": "Санкт-Петербург",
            "query": "культурные места для посещения",
            "limit": 5
        },
        {
            "name": "Multi-city semantic search - Entertainment places",
            "query": "места для развлечений",
            "cities": settings.CITIES,
            "limit": 5
        }
    ]
    
    # Create tests directory if it doesn't exist
    os.makedirs("tests", exist_ok=True)
    
    # Run each test case
    for i, test in enumerate(test_cases):
        logging.info(f"Ball Tree Test {i+1}: {test['name']}")
        
        # Execute the search
        start_time = time.time()
        if "cities" in test:
            # Multi-city search
            result = search_all_cities_ball_tree_task.delay(test["query"], test.get("cities"), test.get("limit", 10))
            search_results = result.get()
        else:
            # Single city search
            result = search_ball_tree_task.delay(test["city"], test["query"], test.get("limit", 10))
            search_results = result.get()
        
        # Calculate search time
        search_time = time.time() - start_time
        
        # Process and display results
        status = search_results.get("status")
        results_count = len(search_results.get("results", []))
        total_found = search_results.get("total_found", 0)
        message = search_results.get("message", "No message")
        
        logging.info(f"Ball Tree Search completed in {search_time:.2f}s - Status: {status}")
        logging.info(f"Results: {results_count}/{total_found} - {message}")
        
        # Print top results
        results = search_results.get("results", [])
        for j, result in enumerate(results[:test.get("limit", 5)]):
            logging.info(f"{j+1}. {result.get('name', 'Unknown')} - Score: {result.get('score', 0):.3f}")
        
        # Save results to file
        test_name = test["name"].lower().replace(" ", "_")
        filename = f"tests/ball_tree_test_{i+1}_{test_name}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(search_results, f, ensure_ascii=False, indent=2)
        logging.info(f"Test results saved to {filename}")


if __name__ == "__main__":
    main()