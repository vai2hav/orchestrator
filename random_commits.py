import os
import random
import string
import subprocess
import requests
from datetime import datetime

# config
GITHUB_USER = "your-username"
GITHUB_TOKEN = "your-token"
CLONE_DIR = "/tmp/github-repos"
COMMITS_PER_DAY = 10
DAYS_PER_WEEK = 4

# get list of repos
def get_repos():
    resp = requests.get(
        f"https://api.github.com/users/{GITHUB_USER}/repos",
        auth=(GITHUB_USER, GITHUB_TOKEN),
    )
    resp.raise_for_status()
    return [repo["ssh_url"] for repo in resp.json()]

# pick random repo
def pick_repo(repos):
    return random.choice(repos)

# make random file change
def make_change(repo_dir):
    filename = os.path.join(repo_dir, f"dummy_{random.randint(1,10000)}.txt")
    with open(filename, "w") as f:
        f.write("".join(random.choices(string.ascii_letters + string.digits, k=100)))
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Random commit"], cwd=repo_dir, check=True)
    subprocess.run(["git", "push"], cwd=repo_dir, check=True)

# clone if needed
def clone_repo(repo_url):
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(CLONE_DIR, repo_name)
    if not os.path.exists(repo_path):
        subprocess.run(["git", "clone", repo_url], cwd=CLONE_DIR, check=True)
    return repo_path

def today_should_run(selected_days):
    today = datetime.today().weekday()
    return today in selected_days

def main():
    os.makedirs(CLONE_DIR, exist_ok=True)

    # choose 4 random days at start of week (0=Mon, 6=Sun)
    random.seed(datetime.today().isocalendar()[1])  # seed per week
    days_this_week = random.sample(range(7), DAYS_PER_WEEK)

    if not today_should_run(days_this_week):
        print("Today is not one of the selected days. Exiting.")
        return

    repos = get_repos()
    repo_url = pick_repo(repos)
    repo_path = clone_repo(repo_url)

    for _ in range(COMMITS_PER_DAY):
        make_change(repo_path)

if __name__ == "__main__":
    main()
