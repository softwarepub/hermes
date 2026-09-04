# Release Process

## Regular Releases

To release a new version of HERMES when a new set of features and/or fixes have been merged, execute the following steps:
> Please create a branch `release/v<version>` 
1. Create a pull request from `release/v<version>` to `develop` containing:
   1. Update the `CHANGELOG.md` with Added, Fixed and Changed.
   2. Adjust the version number in `pyproject.toml` and `CITATION.cff` as necessary (major, minor or patch release).
      To edit the version in `pyproject.toml`, there are two ways:
      - Manually edit the file with an editor.
      - Use `poetry version <rule>`. See also [Poetry Docs](https://python-poetry.org/docs/cli/#version)
2. Merge and delete the release `release/v<version>` branch.
2. Create a pull request from `develop` to `main`.
3. Check if all the CI pipelines for that PR succeed.
3. Let the named maintainer (see GOVERNANCE.md) merge the PR into `main`.
4. Create a new release [by using the Github UI](https://github.com/softwarepub/hermes/releases/new).
   - Choose to create a new tag with the format `v<version number>`.
   - Target branch is `main`.
   - The release title will be set to the tag name, keep as is.
   - A description should be added, giving a very brief summary of the contained changes.
   - Publish the release.
   
   Note: this will also ensure usage of *annotated* tags, making Software Heritage archive the release.
5. On `develop`, update the version in `pyproject.toml` to `<major>.<minor+1>.0.dev0` in another pull request.
   To edit the version, you can use two ways:
   - Manually edit the file with an editor.
   - Use `poetry version "<major>.<minor+1>.0.dev0"`
