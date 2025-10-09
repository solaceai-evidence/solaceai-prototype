import json
import logging
import os
from abc import ABC, abstractmethod

from google.cloud import storage

logger = logging.getLogger(__name__)


class TraceWriter(ABC):
    """Abstract base for writing pipeline execution traces to different storage backends."""
    @abstractmethod
    def write(self, trace_json, file_name: str) -> None:
        """Write trace data to storage backend."""
        pass


class GCSWriter(TraceWriter):
    """Writes execution traces to Google Cloud Storage for production deployments."""
    def __init__(self, bucket_name: str):
        """Initialize GCS writer with target bucket."""
        self.bucket_name = bucket_name

    def write(self, trace_json, file_name: str) -> None:
        """Upload trace JSON to GCS bucket."""
        try:
            trace_json_str = json.dumps(trace_json.__dict__)
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"{file_name}.json")
            blob.upload_from_string(trace_json_str)
            logger.info(f"Pushed event trace: {file_name}.json to GCS")
        except Exception as e:
            logger.info(f"Error pushing {file_name} to GCS: {e}")


class LocalWriter(TraceWriter):
    """Writes execution traces to local filesystem for development and debugging."""
    def __init__(self, local_dir: str):
        """Initialize local writer with target directory, creating it if needed."""
        self.local_dir = local_dir
        if not os.path.exists(local_dir):
            logger.info(f"Creating local directory to record traces: {local_dir}")
            os.makedirs(local_dir)

    def write(self, trace_json, file_name: str) -> None:
        """Write trace JSON to local file with pretty formatting."""
        try:
            with open(f"{self.local_dir}/{file_name}.json", "w") as f:
                json.dump(trace_json.__dict__, f, indent=4)
            logger.info(
                f"Pushed event trace to local path: {self.local_dir}/{file_name}.json"
            )
        except Exception as e:
            logger.info(f"Error pushing {file_name} to local directory: {e}")
