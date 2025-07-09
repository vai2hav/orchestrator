import os
import random
import string
import subprocess
import requests
from datetime import datetime

# Configuration (all from environment)
GITHUB_USER = os.environ["GITHUB_USER"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

CLONE_DIR = "workspace"
COMMITS_PER_DAY = 10
DAYS_PER_WEEK = 7

# Headers for GitHub API
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def get_repos():
    """Fetch all repositories owned by the user"""
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&type=owner"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    repos = resp.json()
    ssh_urls = [repo["ssh_url"] for repo in repos if not repo["archived"]]
    if not ssh_urls:
        raise RuntimeError("No repositories found.")
    return ssh_urls


def pick_repo(repos):
    """Pick one random repo"""
    return random.choice(repos)


def make_random_change(repo_dir):
    """Create a random file with random contents"""
    filename = os.path.join(
        repo_dir, f"file_{random.randint(1000,9999)}.txt"
    )
    content = "".join(random.choices(string.ascii_letters + string.digits, k=200))
    with open(filename, "w") as f:
        f.write(content)

    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    msg = f"Random commit {datetime.utcnow().isoformat()}"
    subprocess.run(["git", "commit", "-m", msg], cwd=repo_dir, check=True)


def push(repo_dir):
    subprocess.run(["git", "push"], cwd=repo_dir, check=True)


def clone_repo(ssh_url):
    """Clone the repo into workspace if not already cloned"""
    repo_name = ssh_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(CLONE_DIR, repo_name)
    if os.path.exists(repo_path):
        subprocess.run(["git", "pull"], cwd=repo_path, check=True)
    else:
        subprocess.run(["git", "clone", ssh_url, repo_path], cwd=CLONE_DIR, check=True)
    return repo_path


def today_is_selected(selected_days):
    """Return True if today is one of the selected days"""
    today = datetime.today().weekday()
    return today in selected_days


def main():
    os.makedirs(CLONE_DIR, exist_ok=True)

    # Seed random per week number so days stay same within week
    week_num = datetime.today().isocalendar()[1]
    random.seed(week_num)
    selected_days = random.sample(range(7), DAYS_PER_WEEK)

    if not today_is_selected(selected_days):
        print("✅ Today is not one of the 4 selected days. Skipping.")
        return

    repos = get_repos()
    chosen_repo = pick_repo(repos)
    print(f"🎯 Chosen repo: {chosen_repo}")

    repo_path = clone_repo(chosen_repo)

    for i in range(COMMITS_PER_DAY):
        make_random_change(repo_path)
        print(f"✅ Commit {i+1} done")

    push(repo_path)
    print("🚀 All commits pushed.")


if __name__ == "__main__":
    main()
