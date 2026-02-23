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
    s = str(url).strip()
    if re.match(r'^[\w.-]+@[\w.-]+:.*', s):
        return s if s.endswith('.git') else s + '.git'
    if s.startswith('file://'):
        return s
    if os.path.exists(s):
        return s
    p = urlparse(s)
    if p.scheme in ('http', 'https'):
        path = p.path if p.path.endswith('.git') else (p.path.rstrip('/') + '.git')
        return f"{p.scheme}://{p.netloc}{path}"
    if s.endswith('.git'):
        return s
    raise ValueError(f"Unsupported repository URL format: {url!r}")

def _clear_readonly(func, path, excinfo):
    """
    onerror handler for shutil.rmtree: try to remove read-only flag and retry.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except Exception:
        pass

def rmtree_with_retries(path: Path, retries: int = 6, initial_wait: float = 0.1):
    """
    Best-effort removal of path with retries and read-only handling.
    - retries: number of attempts
    - initial_wait: initial sleep (multiplies by 2 each retry)
    Logs exceptions but never raises.
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

    if path.exists():
        print(f"error: failed to remove temp dir {path!s} after {retries} attempts. "
              f"Please remove it manually. (Often caused by antivirus or open handles.)")

def _move_or_copy(src: Path, dst: Path):
    try:
        os.replace(str(src), str(dst))
    except Exception:
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
    Robust clone that guarantees best-effort cleanup of temp dirs.
    - Creates temp directories next to the target dest_dir.
    - Always tries to remove temp dirs (even on success/failure).
    """
    dest_path = Path(dest_dir)
    parent = dest_path.parent
    parent.mkdir(parents=True, exist_ok=True)

    clone_url = _normalize_clone_url(url)
    is_gitlab = "gitlab.com" in url.lower()
    if is_gitlab:
        if verbose:
            print("⚠️ GitLab detected: disabling --depth and --filter=blob:none for safety.")
        depth = None
        filter_blobs = False

    env = os.environ.copy()
    if insecure_ssl:
        env["GIT_SSL_NO_VERIFY"] = "1"

    created_temp_dirs: list[Path] = []  

    def build_cmd_for(temp_path: Path, optimized: bool):
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
            if branch:
                cmd += ["--branch", branch]
        cmd += [clone_url, str(temp_path)]
        return cmd

    def attempt_clone(optimized: bool):
        tmp = Path(tempfile.mkdtemp(prefix="clone_tmp_", dir=str(parent)))
        created_temp_dirs.append(tmp)
        cmd = build_cmd_for(tmp, optimized)
        if verbose:
            print("running:", " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return proc.returncode, proc, tmp

    try:
        # Try optimized
        rc1, p1, tmp1 = attempt_clone(optimized=True)
        if rc1 != 0:
            if verbose:
                print("warn: optimized clone failed. stderr:")
                print(p1.stderr.strip() or "(no stderr)")
            # Try fallback plain clone
            rc2, p2, tmp2 = attempt_clone(optimized=False)
            if rc2 != 0:
                # both failed -> raise with both stderr
                raise RuntimeError(
                    "Both optimized clone AND fallback clone failed.\n\n"
                    f"Optimized STDERR:\n{p1.stderr}\n\n"
                    f"Fallback STDERR:\n{p2.stderr}\n"
                )

            # fallback succeeded: move into place
            if dest_path.exists():
                if any(dest_path.iterdir()):
                    raise RuntimeError(f"Destination '{dest_path}' already exists and is not empty. Won't overwrite.")
                else:
                    rmtree_with_retries(dest_path)

            _move_or_copy(tmp2, dest_path)
            if verbose:
                print("✅ Repository cloned successfully (fallback/full clone).")
            return

        # optimized succeeded (tmp1)
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
        for t in created_temp_dirs:
            try:
                rmtree_with_retries(t)
            except Exception as e:
                print(f"warn: final cleanup failed for {t}: {e!r}")
