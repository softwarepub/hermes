# SPDX-FileCopyrightText: 2026 UOL
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Ferenz
# SPDX-FileContributor: Aida Jafarbigloo

"""
Bulk-test HERMES metadata harvesting across multiple repositories.

This script:
- Loads a list of repository URLs from `test_repositories.json` (located next to this script).
- For each repository, runs `hermes clean` followed by `hermes harvest`.
- Checks whether expected harvested metadata files exist under `.hermes/harvest/`.
- Compares current results to a persisted state file (`hermes_bulk_test_state.json`) to detect regressions
  (previously "yes" turning into "no").
- Writes a CSV report (`hermes_bulk_test_results.csv`).

Notes:
- Tokens are currently set as empty strings, need to be set before use.
"""

import subprocess
import pandas as pd
from pathlib import Path
import json


# ---------------- REPOSITORIES ----------------
# Path to this script's directory
HERE = Path(__file__).resolve().parent

# JSON file containing a list of repository URLs to test.
repositories_file = HERE / "test_repositories.json"

# Load repositories list, fall back to empty list if the file doesn't exist.
if Path(repositories_file).exists():
    with open(repositories_file, "r", encoding="utf-8") as fh:
        repositories = json.load(fh)
else:
    repositories = []
    print(f"Warning: {repositories_file} not found. Creating empty list.")

# ---------------- TOKENS ----------------
# Access tokens for private repos / rate limits.
# Set these before running.
GITHUB_TOKEN = ""
GITLAB_TOKEN = ""

# ---------------- RESULTS STORAGE ----------------
# In-memory accumulation of per-repository run results.
results = []

# JSON file that stores previous yes/no answers per URL to detect regressions across runs.
state_file = "hermes_bulk_test_state.json"

# Load previous state (if any).
if Path(state_file).exists():
    with open(state_file, "r", encoding="utf-8") as fh:
        prev_state = json.load(fh)
else:
    prev_state = {}

# ---------------- HELPER FUNCTIONS----------------
def get_token_for_repo(url: str) -> str:
    """
    Return the correct access token for a given repository URL.

    Heuristic:
    - If the URL contains "github" (case-insensitive), return `GITHUB_TOKEN`.
    - Otherwise return `GITLAB_TOKEN`.

    Args:
        url: Repository URL.

    Returns:
        The token string to use.
    """
    if "github" in url.lower():
        return GITHUB_TOKEN
    else:
        return GITLAB_TOKEN

def get_token_type_for_repo(url: str) -> str:
    """
    Return a human-readable label for the token type selected for the URL.

    Args:
        url: Repository URL.

    Returns:
        "GitHub token" if URL appears to be GitHub, else "GitLab token".
    """
    if "github" in url.lower():
        return "GitHub token"
    else:
        return "GitLab token"
    
def get_repo_name(url: str) -> str:
    """
    Extract the repository name from a URL.

    Example:
        "https://github.com/org/repo/" -> "repo"

    Args:
        url: Repository URL.

    Returns:
        The last non-empty path segment.
    """
    return url.rstrip("/").split("/")[-1]

def check_harvested_metadata(repo_name: str) -> str:
    """
    Check whether expected HERMES-harvested metadata files (under .hermes/harvest/) exist.

    Files checked:
    - githublab.json  -> "githublab_metadata"
    - cff.json        -> "cff_metadata"
    - codemeta.json   -> "codemeta_metadata"

    The overall "harvest_result" is:
    - "success" if *any* of the files exists
    - "failed" otherwise

    Args:
        repo_name: Repository name (currently unused, kept for potential future per-repo paths/logging).

    Returns:
        A dict with yes/no flags and an overall "harvest_result" field:
        {
            "githublab_metadata": "yes"|"no",
            "cff_metadata": "yes"|"no",
            "codemeta_metadata": "yes"|"no",
            "harvest_result": "success"|"failed"
        }
    """
    hermes_dir = Path(".hermes") / "harvest"
    
    # Default: nothing found.
    files_exist = {
        "githublab_metadata": "no",
        "cff_metadata": "no",
        "codemeta_metadata": "no",
        "harvest_result": "failed"
    }
    
    # If HERMES didn't create the directory, there is nothing to check.
    if not hermes_dir.exists():
        return files_exist
    
    # Check file existence for each expected output.
    if (hermes_dir / "githublab.json").exists():
        files_exist["githublab_metadata"] = "yes"
    if (hermes_dir / "cff.json").exists():
        files_exist["cff_metadata"] = "yes"
    if (hermes_dir / "codemeta.json").exists():
        files_exist["codemeta_metadata"] = "yes"
        
    # general harvest_result: success if any metadata exists
    if "yes" in (files_exist["githublab_metadata"], files_exist["cff_metadata"], files_exist["codemeta_metadata"]):
        files_exist["harvest_result"] = "success"
    
    # Debug output (kept verbose to help diagnose missing outputs).
    print("Files exist status:")
    print(files_exist)
    
    return files_exist

# ---------------- BULK TEST LOOP ----------------
for url in repositories:
    # Select token and labels based on URL host.
    token = get_token_for_repo(url)
    token_type = get_token_type_for_repo(url)
    repo_name = get_repo_name(url)

    print(f"\n=== Testing repository: {url} ===")

    # Default values for this repository run.
    error_message = ""
    metadata_info = {}

    try:
        # Step 1: Clean previous metadata
        subprocess.run(["hermes", "clean"], check=True)
        print("✅ 'hermes clean' finished.")

        # Step 2: Run harvest for the repository.
        # Capture stdout/stderr to include HERMES output as an error message when needed.
        proc = subprocess.run(
            ["hermes", "harvest", "--url", url, "--token", token],
            capture_output=True, text=True,
            cwd=Path(".").resolve()
        )
        print("✅ 'hermes harvest' finished.")

        
        # Step 3: Verify expected harvested metadata files are present.
        metadata_info = check_harvested_metadata(repo_name)
        
        # If we failed to find any metadata, use HERMES CLI output to aid debugging.
        if metadata_info["harvest_result"] == "failed":
            error_message = proc.stderr.strip() or proc.stdout.strip()

    except Exception as e:
        # Any exception is treated as a failed harvest with no metadata files.
        metadata_info = {
            "githublab_metadata": "no",
            "cff_metadata": "no",
            "codemeta_metadata": "no",
            "harvest_result": "failed"
        }
        error_message = str(e)

    # ---------------- REGRESSION CHECK vs PREVIOUS RUN ----------------
    # Default is "true" (= no regression detected).
    # A regression is defined as: previously "yes" but now "no" for any check (use prev_state).
    compare_result = "true"  
    prev_for_url = prev_state.get(url, {})
    
    # map displayed columns to metadata_info keys
    checks = [
        ("CFF", "cff_metadata"),
        ("CodeMeta", "codemeta_metadata"),
        ("GitHubLab", "githublab_metadata"),
    ]
    for prev_col, curr_key in checks:
        prev_val = str(prev_for_url.get(prev_col, "")).strip().lower()
        curr_val = str(metadata_info.get(curr_key, "no")).strip().lower()
        # if previously yes and now no => incorrect
        if prev_val == "yes" and curr_val == "no":
            compare_result = "false"
            break

    # Store Results
    # save current answers into results and into state for next run
    results.append({
        "url": url,
        "token_used": token_type,
        "error_message": error_message,
        "harvest_result": compare_result,
        "githublab_metadata": metadata_info["githublab_metadata"],
        "cff_metadata": metadata_info["cff_metadata"],
        "codemeta_metadata": metadata_info["codemeta_metadata"]
    })

    # update prev_state for this url to current answers (CFF/CodeMeta/GitHubLab)
    prev_state[url] = {
        "CFF": metadata_info["cff_metadata"],
        "CodeMeta": metadata_info["codemeta_metadata"],
        "GitHubLab": metadata_info["githublab_metadata"]
    }

# ---------------- PERSIST UPDATED STATE ----------------
# Save updated per-URL state so the next run can detect regressions.
with open(state_file, "w", encoding="utf-8") as fh:
    json.dump(prev_state, fh, indent=2, ensure_ascii=False)

# ---------------- BUILD DATAFRAME AND PRINT TABLE ----------------
# build DataFrame from accumulated results
df = pd.DataFrame(results)

# normalize/rename columns for nicer CLI output
col_map = {
    "url": "URL",
    "token_used": "Token",
    "result": "Compared Result",
    "githublab_metadata": "GitHubLab",
    "cff_metadata": "CFF",
    "codemeta_metadata": "CodeMeta",
    "error_message": "Error"
}
df = df.rename(columns=col_map)

# ensure column order
cols = ["URL", "Token", "Compared Result", "GitHubLab", "CFF", "CodeMeta", "Error"]
df = df[[c for c in cols if c in df.columns]]

# ---------------- SAVE CSV ----------------
csv_file = "hermes_bulk_test_results.csv"
df.to_csv(csv_file, index=False)
print(f"\nResults saved to {csv_file}")
