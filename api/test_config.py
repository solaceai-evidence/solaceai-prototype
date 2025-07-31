#!/usr/bin/env python3
"""
Configuration tester for ScholarQA reranker configurations.
Tests all config files and validates their structure.
"""
import json
import sys
from pathlib import Path


def test_config_file(config_path: Path) -> dict:
    """Test a single configuration file"""
    result = {
        "file": config_path.name,
        "valid": False,
        "reranker_service": None,
        "args": {},
        "issues": [],
    }

    try:
        with open(config_path, "r") as f:
            data = json.load(f)

        # Extract reranker config
        run_config = data.get("run_config", {})
        reranker_service = run_config.get("reranker_service")
        reranker_args = run_config.get("reranker_args", {})

        result["reranker_service"] = reranker_service
        result["args"] = reranker_args

        # Validate based on service type
        if reranker_service == "remote":
            if "service_name" not in reranker_args:
                result["issues"].append("Missing service_name for remote reranker")
            if "batch_size" not in reranker_args:
                result["issues"].append("Missing batch_size for remote reranker")

        elif reranker_service in ["crossencoder", "biencoder", "flag_embedding"]:
            if "model_name_or_path" not in reranker_args:
                result["issues"].append(
                    f"Missing model_name_or_path for {reranker_service}"
                )

        elif reranker_service == "modal":
            required = ["app_name", "api_name"]
            missing = [field for field in required if field not in reranker_args]
            if missing:
                result["issues"].append(f"Missing required fields for modal: {missing}")

        else:
            result["issues"].append(f"Unknown reranker service: {reranker_service}")

        result["valid"] = len(result["issues"]) == 0

    except Exception as e:
        result["issues"].append(f"Failed to load config: {e}")

    return result


def main():
    """Test all configuration files"""
    config_dir = Path("run_configs")

    if not config_dir.exists():
        print("❌ run_configs directory not found")
        sys.exit(1)

    config_files = list(config_dir.glob("*.json"))

    if not config_files:
        print("❌ No JSON config files found")
        sys.exit(1)

    print("🔍 Testing configuration files...\n")

    all_valid = True

    for config_file in sorted(config_files):
        result = test_config_file(config_file)

        status = "✅" if result["valid"] else "❌"
        print(f"{status} {result['file']}")
        print(f"   Service: {result['reranker_service']}")
        print(f"   Args: {list(result['args'].keys())}")

        if result["issues"]:
            for issue in result["issues"]:
                print(f"   ⚠️  {issue}")
            all_valid = False

        print()

    if all_valid:
        print("🎉 All configurations are valid!")

        # Show usage examples
        print("\n📖 Usage Examples:")
        print("export CONFIG_PATH='run_configs/default.json'        # Remote reranker")
        print(
            "export CONFIG_PATH='run_configs/crossencoder.json'   # Local CrossEncoder"
        )
        print("export CONFIG_PATH='run_configs/biencoder.json'      # Local BiEncoder")
        print(
            "export CONFIG_PATH='run_configs/flag_embedding.json' # Local FlagEmbedding"
        )
        print(
            "export CONFIG_PATH='run_configs/remote_with_fallback.json' # Remote + Fallback"
        )

    else:
        print("❌ Some configurations have issues!")
        sys.exit(1)


if __name__ == "__main__":
    main()
