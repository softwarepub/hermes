import subprocess

from git import Repo

# Get the repository for this directory, which is the hermes-hmc/workflow clone
repo = Repo('.')
assert not repo.bare

# Get the git instance for this repository
git = repo.git

# Get a list of files in the develop branch
# Change the 'develop' argument to your own branch if you need to run it on anything other than 'develop'
files = [file_str for file_str in git.ls_tree('-r', '--name-only', 'develop', repo.working_dir).split('\n')]

# Build a list of files to unique committer names, using git log
file_committer_map = {}
for file in files:
    if file not in file_committer_map:
        file_committer_map[file] = set()
    for name in git.log('--follow', '--pretty=format:%an', '--', file).split('\n'):
        file_committer_map[file].add(name)

# Run the reuse CLI to add copyright headers for all committers
for file in file_committer_map:
    for name in file_committer_map[file]:
        subprocess.run(['reuse', 'addheader', f'-c={name}', file])
