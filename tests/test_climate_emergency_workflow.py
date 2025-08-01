#!/usr/bin/env python3
"""
Test the full workflow with a dummy climate emergency query.
"""
import requests
import time

API_URL = (
    "http://localhost:8000/query_corpusqa"  # Adjust if your main API endpoint differs
)

# Dummy user query and passages
query = "What are the main risks and impacts of the current climate emergency?"
passages = [
    "Rising sea levels threaten coastal cities and small island nations.",
    "Extreme weather events such as hurricanes and wildfires are becoming more frequent.",
    "Climate change is causing biodiversity loss and ecosystem disruption.",
    "Transitioning to renewable energy is essential to mitigate global warming.",
    "Food security is at risk due to changing weather patterns and droughts.",
    "Public health is impacted by heatwaves and the spread of vector-borne diseases.",
    "Economic losses are increasing due to climate-related disasters.",
    "International cooperation is needed to address the climate crisis effectively.",
    "Greenhouse gas emissions must be reduced to limit temperature rise.",
    "Adaptation strategies are required for vulnerable communities.",
]

payload = {"query": query, "passages": passages, "batch_size": 8}


def main():
    print("Testing climate emergency workflow...")
    start = time.time()
    response = requests.post(API_URL, json=payload, timeout=60)
    elapsed = time.time() - start
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Scores: {data.get('scores', [])}")
        print(f"Processing time: {data.get('processing_time', 'N/A')}s")
        print(f"Device used: {data.get('device_used', 'N/A')}")
        print(f"Documents processed: {data.get('documents_processed', 'N/A')}")
        print("Workflow test successful!")
    else:
        print(f"Error: {response.text}")
    print(f"Total elapsed time: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
