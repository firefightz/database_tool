#!/usr/bin/env python3
import argparse
import json
import subprocess

def invoke_lambda(payload):
    """
    Invokes the AWS Lambda via CLI and returns JSON result
    """
    process = subprocess.run(
        [
            "aws", "lambda", "invoke",
            "--function-name", "myCrudLambda",  # Replace with your Lambda name
            "--payload", json.dumps(payload),
            "output.json"
        ],
        capture_output=True,
        text=True
    )

    if process.returncode != 0:
        print("Error invoking Lambda:", process.stderr)
        return None

    with open("output.json") as f:
        result = json.load(f)
    return result

def main():
    parser = argparse.ArgumentParser(description="Admin CLI for bundle and book tables")
    parser.add_argument("action", choices=["select","insert","update","delete","lookup"], help="Action to perform")
    parser.add_argument("--table", required=True, choices=["bundle","book"], help="Table name")
    parser.add_argument("--filters", type=str, help="Filters as JSON string, e.g., '{\"group_name\":\"Old Group\"}'")
    parser.add_argument("--values", type=str, help="Values as JSON string for insert/update")
    parser.add_argument("--term", type=str, help="Search term for lookup")

    args = parser.parse_args()

    payload = {
        "action": args.action.upper(),
        "table": args.table
    }

    if args.filters:
        try:
            payload["filters"] = json.loads(args.filters)
        except json.JSONDecodeError:
            print("Invalid JSON for filters")
            return

    if args.values:
        try:
            payload["values"] = json.loads(args.values)
        except json.JSONDecodeError:
            print("Invalid JSON for values")
            return

    if args.term:
        payload["term"] = args.term

    result = invoke_lambda(payload)
    if result:
        # Pretty print results
        try:
            body = json.loads(result["body"])
            if "result" in body:
                print(json.dumps(body["result"], indent=2))
            else:
                print(body)
        except Exception as e:
            print("Error parsing Lambda response:", e)
            print(result)

if __name__ == "__main__":
    main()
