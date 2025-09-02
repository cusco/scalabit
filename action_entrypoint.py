#!/usr/bin/env python3
import json
import os
import sys

from src.github_service import get_pull_requests, get_pull_requests_by_date, get_contributors


def main():
    # Get inputs from environment variables (GH Actions)
    repo = os.environ.get('INPUT_REPO')
    operation = os.environ.get('INPUT_OPERATION', '1')
    count = int(os.environ.get('INPUT_COUNT', '5'))
    start_date = os.environ.get('INPUT_START_DATE')
    end_date = os.environ.get('INPUT_END_DATE')

    # Default repo, if empty
    if not repo:
        repo = os.environ.get('GITHUB_REPOSITORY')
        if not repo:
            print("Error: repo input is required, GITHUB_REPOSITORY not set?")
            sys.exit(1)
        print(f"Using current repository: {repo}")

    try:
        if operation == '1':
            print(f"Operation 1: Getting {count} most recent pull requests")
            result = get_pull_requests(repo, count)

        elif operation == '2':
            if not start_date or not end_date:
                print("Error: start_date and end_date are required for operation 2")
                sys.exit(1)
            print(f"Operation 2: Getting pull requests from {start_date} to {end_date}")
            result = get_pull_requests_by_date(repo, start_date, end_date)

        elif operation == '3':
            print("Operation 3: Getting contributors")
            result = get_contributors(repo)

        else:
            print(f"Error: Unknown operation '{operation}'. Use 1, 2, or 3")
            sys.exit(1)

        # Print for human in GH
        result_json = json.dumps(result, indent=2)
        print("Result:")
        print(result_json)

        # Output to GH actions file
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
            # Escape for GH Actions output
            escaped_result = result_json.replace('\n', '\\n').replace('"', '\\"')
            f.write(f"result={escaped_result}\n")

    except Exception as error:
        print(f"Error: {str(error)}")
        sys.exit(1)



if __name__ == '__main__':
    main()
