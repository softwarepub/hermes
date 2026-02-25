# SPDX-FileCopyrightText: 2026 UOL 
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Ferenz
# SPDX-FileContributor: Aida Jafarbigloo

import os
import re
import shutil
import subprocess
import tempfile
import time
import stat
from pathlib import Path
from urllib.parse import urlparse
from typing import Sequence

# ---------------- utilities ----------------

def _normalize_clone_url(url: str) -> str:
    """
    Normalize a repository "clone target" into a format that `git clone` accepts.

    Supported inputs:
      - SSH scp-like form:      git@host:group/repo(.git)
      - HTTPS URLs:             https://host/group/repo(.git)

    Normalization rules:
      - For SSH and HTTPS, append ".git" when missing (common, but not required by all hosts).
    """
    s = str(url).strip()
    
    # SSH scp-style: git@github.com:org/repo
    if re.match(r'^[\w.-]+@[\w.-]+:.*', s):
        return s if s.endswith('.git') else s + '.git'
    
    # file:// URLs should be passed as-is.
    if s.startswith('file://'):
        return s
    
    # If it's an existing local path
    if os.path.exists(s):
        return s
    
    # Parse normal URLs (http/https).
    p = urlparse(s)
    if p.scheme in ('http', 'https'):
        path = p.path if p.path.endswith('.git') else (p.path.rstrip('/') + '.git')
        return f"{p.scheme}://{p.netloc}{path}"
    
    # If the user already provided a .git suffix but it isn't http/https, accept it as-is.
    if s.endswith('.git'):
        return s
    raise ValueError(f"Unsupported repository URL format: {url!r}")

def _clear_readonly(func, path, excinfo):
    """
    Error handler for `shutil.rmtree(..., onerror=...)`.

    Purpose:
      Some platforms/tools (notably Windows, antivirus scanners, or git itself) can leave files
      marked read-only, causing deletion failures. This handler attempts to:
        1) Remove the read-only attribute, then
        2) Retry removal of the file/directory.

    Parameters:
      func:    The function that raised the exception (provided by shutil).
      path:    The filesystem path that couldn't be removed.
      excinfo: Exception info tuple (type, value, traceback).
    """
    # make the path writable.
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    # retry deletion.
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except Exception:
        pass

def rmtree_with_retries(path: Path, retries: int = 6, initial_wait: float = 0.1):
    """
    Recursive directory deletion with retries and read-only handling, for environments where temporary directories may be locked
    or marked read-only (e.g., Windows, CI systems, antivirus interference).

    Behavior:
      - If `path` doesn't exist: return immediately.
      - Attempts deletion up to `retries` times.
      - Between attempts, sleeps with exponential backoff:
          wait = initial_wait, then wait *= 2 each retry.
      - Makes files/directories writable before trying `shutil.rmtree`.
      - Uses `_clear_readonly` for additional resilience.
      - Never raises: logs warnings/errors and returns.

    Parameters:
      path:         Directory to remove.
      retries:      Number of attempts before giving up.
      initial_wait: Starting sleep duration (seconds) for exponential backoff.
    """
    if not path.exists():
        return

    wait = initial_wait
    for attempt in range(1, retries + 1):
        try:
            # Ensure files are writable where possible
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    p = os.path.join(root, name)
                    try:
                        os.chmod(p, stat.S_IWRITE)
                    except Exception:
                        pass
                for name in dirs:
                    p = os.path.join(root, name)
                    try:
                        os.chmod(p, stat.S_IWRITE)
                    except Exception:
                        pass

            shutil.rmtree(path, onerror=_clear_readonly)
            
            # If deletion succeeded, stop.
            if not path.exists():
                return
        except Exception as e:
            print(f"warn: rmtree attempt {attempt} failed for {path!s}: {e!r}")
        time.sleep(wait)
        wait *= 2

    try:
        alt = path.with_name(path.name + "_TO_DELETE")
        try:
            os.replace(str(path), str(alt))
            shutil.rmtree(alt, onerror=_clear_readonly)
            return
        except Exception:
            pass
    except Exception:
        pass

    # If still present, report and exit without raising.
    if path.exists():
        print(f"error: failed to remove temp dir {path!s} after {retries} attempts. "
              f"Please remove it manually. (Often caused by antivirus or open handles.)")

def _move_or_copy(src: Path, dst: Path):
    """
    Move a directory into place, falling back to copy+delete when a move isn't possible.

    Primary strategy:
      - `os.replace(src, dst)` performs an atomic rename/move when possible.

    Fallback strategy:
      - If atomic move fails (commonly due to cross-device boundaries or permission issues),
        copy the directory tree to `dst`, then remove `src` using robust cleanup.

    Parameters:
      src: Source directory path (typically a temp clone directory).
      dst: Destination directory path.
    """
    try:
        # Fast path: atomic rename (preferred when possible)
        os.replace(str(src), str(dst))
    except Exception:
        # Cross-device or permission failure — fall back to copy + cleanup
        shutil.copytree(str(src), str(dst))
        rmtree_with_retries(src)

# ---------------- clone logic ----------------

def clone_repository(
    url: str,
    dest_dir: str,
    recursive: bool = True,
    depth: int | None = 1,
    filter_blobs: bool = True,
    sparse: bool = False,
    branch: str | None = None,
    insecure_ssl: bool = False,
    *,
    root_only: bool = False,
    include_files: Sequence[str] | None = None,
    verbose: bool = False,
) -> None:
    """
    Clone a Git repository into a destination directory with optional
    optimization, fallback, and sparse checkout support.

    Workflow:
        1. Normalize the repository URL.
        2. Attempt an optimized clone (shallow, filtered, sparse-enabled).
        3. If optimized clone fails, retry with a plain clone.
        4. Clone into a temporary directory and atomically move into place.
        5. Optionally configure sparse checkout after cloning.
        6. Clean up temporary directories.

    Parameters:
        url:            Repository URL or local path.
        dest_dir:       Target directory for the clone.
        recursive:      Whether to clone submodules.
        depth:          Shallow clone depth (None disables shallow clone).
        filter_blobs:   Use partial clone filter (`--filter=blob:none`).
        sparse:         Enable sparse checkout mode.
        branch:         Specific branch to checkout.
        insecure_ssl:   Disable SSL verification for Git (not recommended).
        root_only:      Restrict checkout to root-level files only.
        include_files:  Specific file patterns to include in sparse checkout.
        verbose:        Print command execution details and warnings.

    Raises:
        RuntimeError: If both optimized and fallback clones fail,
                      or if destination exists and is non-empty.
        ValueError:   If the repository URL format is invalid.
    """
    dest_path = Path(dest_dir)
    parent = dest_path.parent
    parent.mkdir(parents=True, exist_ok=True)

    clone_url = _normalize_clone_url(url)
    
    # Some GitLab setups have compatibility issues with partial/shallow clones
    is_gitlab = "gitlab.com" in url.lower()
    if is_gitlab:
        if verbose:
            print("⚠️ GitLab detected: disabling --depth and --filter=blob:none for safety.")
        depth = None
        filter_blobs = False

    env = os.environ.copy()
    if insecure_ssl:
        # Disables SSL verification (security risk; use only when necessary)
        env["GIT_SSL_NO_VERIFY"] = "1"

    created_temp_dirs: list[Path] = []  

    def build_cmd_for(temp_path: Path, optimized: bool):
        """Construct the git clone command for optimized or fallback mode."""
        cmd = ["git", "clone"]
        
        if optimized:
            if branch:
                cmd += ["--branch", branch]
            if depth is not None:
                cmd += ["--depth", str(depth)]
            if filter_blobs:
                cmd += ["--filter=blob:none"]
            if sparse or root_only or (include_files and len(include_files) > 0):
                cmd += ["--sparse"]
            if recursive:
                cmd += ["--recurse-submodules"]
        else:
            # Fallback clone uses minimal options for maximum compatibility
            if branch:
                cmd += ["--branch", branch]
        cmd += [clone_url, str(temp_path)]
        return cmd

    def attempt_clone(optimized: bool):
        """Execute a clone attempt into a new temporary directory."""
        tmp = Path(tempfile.mkdtemp(prefix="clone_tmp_", dir=str(parent)))
        created_temp_dirs.append(tmp)
        cmd = build_cmd_for(tmp, optimized)
        if verbose:
            print("running:", " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return proc.returncode, proc, tmp

    try:
        # First attempt: optimized clone
        rc1, p1, tmp1 = attempt_clone(optimized=True)
        if rc1 != 0:
            if verbose:
                print("warn: optimized clone failed. stderr:")
                print(p1.stderr.strip() or "(no stderr)")
            # Second attempt: plain clone
            rc2, p2, tmp2 = attempt_clone(optimized=False)
            if rc2 != 0:
                # both failed -> raise with both stderr
                raise RuntimeError(
                    "Both optimized clone AND fallback clone failed.\n\n"
                    f"Optimized STDERR:\n{p1.stderr}\n\n"
                    f"Fallback STDERR:\n{p2.stderr}\n"
                )

            # Ensure destination is safe to populate
            if dest_path.exists():
                if any(dest_path.iterdir()):
                    raise RuntimeError(f"Destination '{dest_path}' already exists and is not empty. Won't overwrite.")
                else:
                    rmtree_with_retries(dest_path)

            _move_or_copy(tmp2, dest_path)
            if verbose:
                print("✅ Repository cloned successfully (fallback/full clone).")
            return

        # Optimized clone succeeded
        if dest_path.exists():
            if any(dest_path.iterdir()):
                raise RuntimeError(f"Destination '{dest_path}' already exists and is not empty. Won't overwrite.")
            else:
                rmtree_with_retries(dest_path)

        _move_or_copy(tmp1, dest_path)
        if verbose:
            print("✅ Repository cloned successfully (optimized clone).")

        # if sparse/root_only/include_files were requested, apply sparse-checkout
        if sparse or root_only or (include_files and len(include_files) > 0):
            try:
                subprocess.run(
                    ["git", "-C", str(dest_path), "sparse-checkout", "init", "--no-cone"],
                    check=True
                )
                patterns: list[str] = []
                if root_only:
                    # Include root-level files but exclude subdirectories
                    patterns += ["/*", "!/*/"]
                if include_files:
                    for p in include_files:
                        p = p.strip()
                        if p:
                            patterns.append(p if p.startswith("/") else f"/{p}")
                if patterns:
                    subprocess.run(
                        ["git", "-C", str(dest_path), "sparse-checkout", "set", "--no-cone", *patterns],
                        check=True
                    )
                    if verbose:
                        print("📁 Sparse checkout applied:", patterns)
            except subprocess.CalledProcessError as e:
                print("warn: sparse-checkout setup failed:", e)

    finally:
        # Always attempt to clean up temporary directories
        for t in created_temp_dirs:
            try:
                rmtree_with_retries(t)
            except Exception as e:
                print(f"warn: final cleanup failed for {t}: {e!r}")
