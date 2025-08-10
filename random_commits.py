import os
import random
import subprocess
import requests
from datetime import datetime

# Configuration
GH_USER = os.environ["GH_USER"]
GH_PAT = os.environ["GH_PAT"]
TARGET_REPO = os.environ["TARGET_REPO"]  # NEW: required repo name

CLONE_DIR = "/tmp/workspace"
COMMITS_PER_DAY_PLAN = [5, 2, 1, 1]  # Total 8 commits over 4 days

HEADERS = {
    "Authorization": f"token {GH_PAT}",
    "Accept": "application/vnd.github+json",
}


def setup_git_config(repo_dir):
    subprocess.run(["git", "config", "user.name", GH_USER], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.email", f"{GH_USER}@users.noreply.github.com"],
        cwd=repo_dir,
        check=True,
    )


def get_target_repo():
    url = f"https://api.github.com/repos/{GH_USER}/{TARGET_REPO}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        raise RuntimeError(f"Repository '{TARGET_REPO}' not found.")
    repo = resp.json()
    if repo.get("archived"):
        raise RuntimeError(f"Repository '{TARGET_REPO}' is archived.")
    if not repo.get("private"):
        raise RuntimeError(f"Repository '{TARGET_REPO}' is not private.")
    return repo["clone_url"]


def make_random_change(repo_dir):
    filename = os.path.join(repo_dir, "logger.txt")
    line = f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | {random.randint(1000,9999)}\n"
    with open(filename, "a") as f:
        f.write(line)

    subprocess.run(["git", "add", filename], cwd=repo_dir, check=True)

    # Make the commit message look natural
    messages = [
        "Refactor code",
        "Fix typo",
        "Update documentation",
        "Improve logging",
        "Minor fixes",
        "Update dependencies",
        "Cleanup",
        "Adjust config",
    ]
    msg = random.choice(messages)

    # Check if there’s actually anything to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repo_dir
    )
    if result.returncode == 0:
        print("⚠️ Nothing to commit, skipping.")
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
        subprocess.run(
            ["git", "clone", authenticated_url, repo_path],
            cwd=CLONE_DIR,
            check=True,
        )

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

    # selected_days = random.sample(range(7), 4)
    selected_days = random.sample(range(14), 4)
    random.shuffle(COMMITS_PER_DAY_PLAN)
    day_commit_map = dict(zip(selected_days, COMMITS_PER_DAY_PLAN))

    today = datetime.today().weekday()
    if today not in day_commit_map:
        print("✅ Today is not one of the selected days. Skipping.")
        return

    commits_today = day_commit_map[today]
    print(f"📆 Today is selected. Planned commits: {commits_today}")

    repo_url = get_target_repo()
    authenticated_url = repo_url.replace(
        "https://", f"https://{GH_USER}:{GH_PAT}@"
    )

    repo_path = clone_repo(authenticated_url)
    setup_git_config(repo_path)

    for i in range(commits_today):
        make_random_change(repo_path)
        print(f"✅ Commit {i+1} done")

    push(repo_path)
    print("🚀 All commits pushed.")


if __name__ == "__main__":
    main()
