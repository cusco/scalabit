import requests
from fastapi import FastAPI, HTTPException

from src.github_service import (
    get_contributors,
    get_pull_requests,
    get_pull_requests_by_date,
)

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/pull-requests/{num_prs}")
def get_n_pull_requests(num_prs: int, repo: str):
    try:
        return get_pull_requests(repo, num_prs)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repo format")
    except requests.RequestException as err:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(err)}")


@app.get("/pull-requests-by-date")
def get_pull_requests_by_date_endpoint(repo: str, start_date: str, end_date: str):
    try:
        return get_pull_requests_by_date(repo, start_date, end_date)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=f"Invalid format: {str(err)}")
    except requests.RequestException as err:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(err)}")


@app.get("/contributors")
def get_contributors_endpoint(repo: str):
    try:
        return get_contributors(repo)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repo format")
    except requests.RequestException as err:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(err)}")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=5000)
