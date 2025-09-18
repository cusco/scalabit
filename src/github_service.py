import os

import requests

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


def get_pull_requests(repo_url, count):
    """Get the most recent N PR's in a repo."""
    owner, repo_name = parse_repo_url(repo_url)

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls"
    params = {'state': 'all', 'per_page': int(min(count, 100)), 'sort': 'updated', 'direction': 'desc'}

    response = requests.get(url, headers=get_github_headers(), params=params, timeout=30)
    response.raise_for_status()
    pull_requests = response.json()

    formatted_prs = []
    for pull_request in pull_requests[:count]:
        formatted_prs.append(format_pull_request(pull_request))

    return {'repository': f"{owner}/{repo_name}", 'count': len(formatted_prs), 'pull_requests': formatted_prs}


def get_pull_requests_by_date(repo_url, start_date, end_date):
    """Get PR's within a date range."""

    # http://localhost:5000/pull-requests-by-date?repo=microsoft/vscode&start_date=2025-08-20&end_date=2025-08-30
    owner, repo_name = parse_repo_url(repo_url)

    # Let's use the search/issues endpoint that supports date filtering
    # https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28
    # https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax
    url = f"{GITHUB_API_URL}/search/issues"
    query = f"repo:{owner}/{repo_name} type:pr created:{start_date}..{end_date}"
    # Ambiguous date type requirement
    # query = f"repo:{owner}/{repo_name} type:pr updated:{start_date}..{end_date}"
    # query = f"repo:{owner}/{repo_name} type:pr pushed:{start_date}..{end_date}"

    params = {'q': query, 'sort': 'updated', 'order': 'desc', 'per_page': 100}

    all_prs = []
    page = 1

    while page <= 100:  # Limit to 100 pages (10,000 results max)
        params['page'] = page
        response = requests.get(url, headers=get_github_headers(), params=params, timeout=30)
        response.raise_for_status()

        search_results = response.json()
        pull_requests = search_results.get('items', [])

        if not pull_requests:
            break

        for pr in pull_requests:
            all_prs.append(format_pull_request(pr))

        # Last page Stop
        if len(pull_requests) < 100:
            break

        page += 1

    return {
        'repository': f"{owner}/{repo_name}",
        'date_range': f"{start_date} to {end_date}",
        'count': len(all_prs),
        'pull_requests': all_prs,
    }


def get_contributors(repo_url):
    """Get all contributors for a repo."""
    owner, repo_name = parse_repo_url(repo_url)

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/contributors"
    params = {'per_page': 100}

    all_contributors = []
    page = 1

    while page <= 100:  # Limit to 100 pages (10,000 results max)
        params['page'] = page
        response = requests.get(url, headers=get_github_headers(), params=params, timeout=30)
        response.raise_for_status()
        contributors = response.json()

        if not contributors:
            break

        for contributor in contributors:
            all_contributors.append(format_contributor(contributor))

        # Check if we've reached the last page
        if len(contributors) < 100:
            break

        page += 1

    return {
        'repository': f"{owner}/{repo_name}",
        'count': len(all_contributors),
        'contributors': all_contributors,
    }
