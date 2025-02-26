# Release Process

## Regular Releases

To release a new version of HERMES when a new set of features and/or fixes have been merged, execute the following steps:

1. Adjust the version number in `pyproject.toml` as necessary (major, minor or patch release).
   Please create and merge a PR for this. Don't just push to `develop`.
   To edit the version, you can use two ways:
   - Manually edit the file with an editor.
   - Use `poetry version <rule>`. See also [Poetry Docs](https://python-poetry.org/docs/cli/#version)
2. Create a pull request from `develop` to `main`.
3. Check if all the CI pipelines for that PR succeed.
3. Let the named maintainer (see GOVERNANCE.md) merge the PR into `main`.
4. Create a new release [by using the Github UI](https://github.com/softwarepub/hermes/releases/new).
   This also ensures usage of *annotated* tags to include releases in Software Heritage Archive.
   - Choose to create a new tag with the format `v<version number>`.
   - Target branch is `main`.
   - The release title will be set to the tag name, keep as is.
   - A description should be added, giving a very brief summary of the contained changes.
   - Publish the release.
5. On `develop`, update the version in `pyproject.toml` to `<major>.<minor+1>.0.dev0` in another pull request.
   To edit the version, you can use two ways:
   - Manually edit the file with an editor.
   - Use `poetry version "<major>.<minor+1>.0.dev0"`
