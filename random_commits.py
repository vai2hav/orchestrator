import os
import random
import string
import subprocess
import requests
from datetime import datetime

# Configuration
GH_USER = os.environ["GH_USER"]
GH_PAT = os.environ["GH_PAT"]

CLONE_DIR = "/tmp/workspace"
COMMITS_PER_DAY = 10
DAYS_PER_WEEK = 7  # Run on 7 days

HEADERS = {
    "Authorization": f"token {GH_PAT}",
    "Accept": "application/vnd.github+json",
}

def setup_git_config(repo_dir):
    subprocess.run(["git", "config", "user.name", GH_USER], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", f"{GH_USER}@users.noreply.github.com"], cwd=repo_dir, check=True)

def get_repos():
    url = f"https://api.github.com/users/{GH_USER}/repos?per_page=100&type=owner"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    repos = resp.json()
    https_urls = [repo["clone_url"] for repo in repos if not repo["archived"]]
    if not https_urls:
        raise RuntimeError("No repositories found.")
    return https_urls


def pick_repo(repos):
    return random.choice(repos)


# def make_random_change(repo_dir):
#     filename = os.path.join(
#         repo_dir, f"file_{random.randint(1000,9999)}.txt"
#     )
#     os.makedirs(repo_dir, exist_ok=True)  # make sure path exists
#     content = "".join(random.choices(string.ascii_letters + string.digits, k=200))
#     with open(filename, "w") as f:
#         f.write(content)

#     subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
#     msg = f"Random commit {datetime.utcnow().isoformat()}"
#     subprocess.run(["git", "commit", "-m", msg], cwd=repo_dir, check=True)
def make_random_change(repo_dir):
    filename = os.path.join(repo_dir, "heartbeat.txt")
    content = f"{datetime.utcnow().isoformat()} | random: {random.randint(1000,9999)}\n"
    with open(filename, "a") as f:
        f.write(content)

    subprocess.run(["git", "add", filename], cwd=repo_dir, check=True)

    msg = f"Random commit {datetime.utcnow().isoformat()}"

    # Check if there’s actually anything to commit
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo_dir)
    if result.returncode == 0:
        print("⚠️ Nothing to commit, skipping this commit.")
    else:
        subprocess.run(["git", "commit", "-m", msg], cwd=repo_dir, check=True)

def push(repo_dir):
    subprocess.run(["git", "push"], cwd=repo_dir, check=True)


def clone_repo(authenticated_url):
    repo_name = authenticated_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(CLONE_DIR, repo_name)

    os.makedirs(CLONE_DIR, exist_ok=True)

    if os.path.exists(repo_path):
        print(f"✅ Repo already cloned at {repo_path}, pulling latest")
        subprocess.run(["git", "pull"], cwd=repo_path, check=True)
    else:
        print(f"🚀 Cloning repo into {repo_path}")
        subprocess.run(["git", "clone", authenticated_url, repo_path], cwd=CLONE_DIR, check=True)

    if not os.path.exists(repo_path):
        raise RuntimeError(f"Failed to clone repository into {repo_path}")
    return repo_path


def today_is_selected(selected_days):
    today = datetime.today().weekday()
    return today in selected_days


def main():
    os.makedirs(CLONE_DIR, exist_ok=True)

    week_num = datetime.today().isocalendar()[1]
    random.seed(week_num)
    selected_days = random.sample(range(7), DAYS_PER_WEEK)

    if not today_is_selected(selected_days):
        print("✅ Today is not one of the selected days. Skipping.")
        return

    repos = get_repos()
    chosen_repo = pick_repo(repos)
    print(f"🎯 Chosen repo: {chosen_repo}")

    authenticated_url = chosen_repo.replace(
        "https://", f"https://{GH_USER}:{GH_PAT}@"
    )
    
    repo_path = clone_repo(authenticated_url)
    setup_git_config(repo_path)

    for i in range(COMMITS_PER_DAY):
        make_random_change(repo_path)
        print(f"✅ Commit {i+1} done")

    push(repo_path)
    print("🚀 All commits pushed.")


if __name__ == "__main__":
    main()
