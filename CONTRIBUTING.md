<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Stephan Druskat
SPDX-FileContributor: Oliver Bertuch
-->

# Contribution Guidelines

## Feedback

This is an open repository, and we are very happy to receive contributions to the HERMES workflow from the community, 
for example as feedback, bug reports, feature requests, etc.

We see our project as part of a global and interdisciplinary effort to improve the state of the art in 
research software engineering, maintenance and scholarly communications around research software. We therefore
appreciate any feedback you may have on the HERMES project itself and any of its outputs.

Either [create an issue](https://github.com/hermes-hmc/workflow/issues/new/choose) in our project repository or 
[send us an email](mailto:team@software-metadata.pub?subject=HERMES%20WOrkflow%20Reachout).

## HERMES development workflow

The following describes the workflow for contributions.

### Preamble

> **Branching is cheap!**
>
> Work in small packets, put up small pull requests!
>
> Aim for quick turnaround times!

### Branching

We loosely follow a mixture of [GitHubFlow](https://docs.github.com/en/get-started/quickstart/github-flow) and [GitFlow](https://nvie.com/posts/a-successful-git-branching-model/) with the following branches.

#### `main`

- This is the stable branch.
- Merges into `main` come only from `develop` or a hotfix branch (i.e., when something needs to be fixed in "production").

#### `develop`

- This is the unstable development branch.
- Before you attempt to break something or add experimental changes, `git tag` the current state.

#### `feature/<describe-feature>`

- Naming convention: include an issue id if one exists, e.g., `feature/62-improve-broken-thing` or `feature/42-add-new-thing`.
- Branch from last tag on `develop`.

#### `hotfix/<describe-hotfix>`

- Naming convention: include an issue id if one exists, e.g., `hotfix/62-fix-broken-thing-in-release`.
- Branch from `main`.

### Pull requests (PRs)

Project members may create pull requests from branches in the main repository, while external contributors need to follow
a [forking pattern](https://docs.github.com/en/get-started/quickstart/fork-a-repo). In both cases, please follow these rules:


- As soon as you have made 1 commit in a feature branch, put up a *draft* pull request.
- Keep pull requests small.
- ⚠️ Do not review *draft* pull requests, unless the PR author @-mentions you with this specific request.
- When you think you're done, mark the PR ready for review to start the [merge process](#merging-changes-into-develop).

### Merging changes into `develop`

- Create PR from `feature/...` against `develop` (PR author)
- Describe work in initial comment (PR author)
    - Reference any related issues (use, e.g., `Fixes #n` or `- Related: #n`)
    - What does the new code do?
    - Optional: What should reviewers look at specifically
    - Information on how to review:
        - E.g.
          ```bash
          pip install ./
          pytest test/
          ```
- Request review (PR author)
    - Eligible reviewers:
        - Python code: @led02, @sdruskat, @jkelling
        - Documentation:
            - Workflow: @all
            - Project: @all
- Review (at least 1 reviewer)
    - Follow instructions in PR
    - Review thoroughly beyond instructions
    - Comments / change suggestions inline in files
    - Submit review:
        - **CASE 1:** Non-blocking change requests (typos, documentation wording, etc.) -> Document and Accept
        - **CASE 2:** Blocking change requests (something doesn't work, bad quality code, docs not understandable):
            - Ideally, fix things yourself in the branch -> Request Changes (or do them on your own)
        - **CASE 3:** "Just a comment"s, pointers to potential future changes -> Document and Accept
        - **CASE 4:** :warning: If you want a second pair of eyes on the PR, use "Comment" to finish review, request
                      another reviewer and @-mention in comment.
    - Optional: If you find something blocking after initial review, add review with "Request changes" outcome
- Act on review (PR author)
    - React to comments
    - Fix issues
    - Discuss options
- Then:
    - CASE 1: PR author to fix non-blocking issues and merge
    - CASE 2: PR author to re-request review from original reviewer(s)
    - CASE 3: PR author to react to comments and merge
    - CASE 4: (PR author's reaction depends on outcome of second review)
- Re-review:
    - See Review above
- Any maintainer
    - Close PR if PR is not suitable for merge, and no further changes to improve it come from the PR author,
      after having communicated sensible requests with a deadline for further work in the PR comments.
    - Merge PR and delete remote branch if at least half of the invited reviewers have approved the PR, and no changes
      have been requested after review. This implements lazy consensus to avoid bottlenecks, where a PR has been
      approved by some reviewers but cannot be closed due to missing reviews.

### Release/stabilization process

- Create release branch `release/v<version-id>` from `develop`
- Check if everything looks good
    - Audit source (using linters and stuff)
    - Ensure test coverage of at least 72.3%
    - Check if documentation aligns with code (also run tutorial to check completeness)
    - Check if metadata is correct
- Put up PR from release branch against `main`
- Request review (workflow as above)
- Merge into `main`
- Tag `main` HEAD as `v<version-id>`
- Push `main`
- Push tag
- Merge `main` into `develop`
- Delete release branch
- :bulb: If something goes wrong in the release branch, you can always delete, fix things in a feature branch, merge
  into `develop` following workflow above, and start anew
