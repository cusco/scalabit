import os
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

GITHUB_API_URL = "https://api.github.com"


def get_github_headers():
    headers = {'Accept': 'application/vnd.github.v3+json'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'token {token}'
    return headers


def parse_repo_url(repo_url):
    if repo_url.startswith('https://github.com/'):
        repo_path = repo_url.replace('https://github.com/', '').rstrip('/')
    else:
        repo_path = repo_url.rstrip('/')

    parts = repo_path.split('/')
    if len(parts) != 2:
        raise ValueError("Invalid repository format")
    return parts[0], parts[1]


def format_pull_request(pull_request):
    return {
        'number': pull_request['number'],
        'title': pull_request['title'],
        'state': pull_request['state'],
        'author': pull_request['user']['login'],
        'created_at': pull_request['created_at'],
        'updated_at': pull_request['updated_at'],
        'url': pull_request['html_url'],
    }


def format_contributor(contributor):
    return {
        'login': contributor['login'],
        'contributions': contributor['contributions'],
        'url': contributor['html_url'],
        'avatar_url': contributor['avatar_url'],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/pull-requests/{num_prs}")
def get_n_pull_requests(num_prs: int, repo: str):
    try:
        owner, repo_name = parse_repo_url(repo)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repo format")

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls"
    params = {'state': 'all', 'per_page': int(min(num_prs, 100)), 'sort': 'updated', 'direction': 'desc'}

    try:
        response = requests.get(url, headers=get_github_headers(), params=params)  # type: ignore
        response.raise_for_status()
        pull_requests = response.json()

        formatted_prs = []
        for pull_request in pull_requests[:num_prs]:
            formatted_prs.append(format_pull_request(pull_request))

        return {'repository': f"{owner}/{repo_name}", 'count': len(formatted_prs), 'pull_requests': formatted_prs}

    except requests.RequestException as error:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(error)}")


@app.get("/pull-requests-by-date")
def get_pull_requests_by_date(repo: str, start_date: str, end_date: str):
    try:
        owner, repo_name = parse_repo_url(repo)
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError as error:
        raise HTTPException(status_code=400, detail=f"Invalid format: {str(error)}")

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls"
    params = {'state': 'all', 'per_page': 100, 'sort': 'updated', 'direction': 'desc'}

    try:
        response = requests.get(url, headers=get_github_headers(), params=params)  # type: ignore
        response.raise_for_status()
        all_pull_requests = response.json()

        matching_prs = []
        for pull_request in all_pull_requests:
            pr_date = datetime.strptime(pull_request['updated_at'][:10], '%Y-%m-%d')
            if start_datetime <= pr_date <= end_datetime:
                matching_prs.append(format_pull_request(pull_request))

        return {
            'repository': f"{owner}/{repo_name}",
            'date_range': f"{start_date} to {end_date}",
            'count': len(matching_prs),
            'pull_requests': matching_prs,
        }

    except requests.RequestException as error:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(error)}")


@app.get("/contributors")
def get_contributors(repo: str):
    try:
        owner, repo_name = parse_repo_url(repo)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repo format")

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/contributors"
    params = {'per_page': 100}

    try:
        response = requests.get(url, headers=get_github_headers(), params=params)
        response.raise_for_status()
        contributors = response.json()

        formatted_contributors = []
        for contributor in contributors:
            formatted_contributors.append(format_contributor(contributor))

        return {
            'repository': f"{owner}/{repo_name}",
            'count': len(formatted_contributors),
            'contributors': formatted_contributors,
        }

    except requests.RequestException as error:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(error)}")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=5000)
