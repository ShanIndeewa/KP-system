"""
Generate OpenAPI specification files from the FastAPI app.

Usage:
    python generate_openapi.py

Outputs:
    - openapi.json  (OpenAPI 3.1 JSON spec)
    - openapi.yaml  (OpenAPI 3.1 YAML spec)
"""

import json
import sys

from main import app


def generate():
    """Extract the OpenAPI schema from FastAPI and write to files."""
    schema = app.openapi()

    # Write JSON
    with open("openapi.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print("✅ Generated openapi.json")

    # Write YAML (try with PyYAML, fall back to manual if unavailable)
    try:
        import yaml

        with open("openapi.yaml", "w", encoding="utf-8") as f:
            yaml.dump(schema, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print("✅ Generated openapi.yaml")
    except ImportError:
        print("⚠️  PyYAML not installed — skipping YAML generation.")
        print("   Install with: pip install pyyaml")


if __name__ == "__main__":
    generate()
