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

- *Create draft PR:* The **contributor** [creates a draft pull request (PR)](#pull-requests-prs) from `feature/...` against `develop` (and becomes the **PR author**).
- *Describe changes:* The **PR author** describes the changes in the PR in the initial comment:
    - Reference any related issues (use, e.g., `Fixes #n` or `- Related: #n`)
    - Describe what new code does
    - Optional: Describe what reviewers should look at specifically
    - Include information on how to review:
        - E.g.:
          ```bash
          poetry install
          poetry run pytest test/
          ```
- *Request review:* The **PR author** requests one or more reviews.
    - Eligible reviewers are:
        - For Python code: @led02, @sdruskat, @jkelling
        - For Documentation:
            - Workflow: @all
            - Project: @all
- *Review:* At least 1 **reviewer** reviews the changes:
    - Follow the instructions in the PR
    - Review thoroughly beyond instructions
    - Add comments or change suggestions inline in the respective file using GitHub's * changed* tab
    - Submit the review with the correct review outcome:
        - **CASE 1:** Non-blocking change requests (typos, documentation wording, etc.) -> *Document and Accept*
        - **CASE 2:** Blocking change requests (something doesn't work, bad quality code, docs are not understandable):
            - Ideally, fix things yourself in the branch -> *Request Changes* (or do them on your own)
        - **CASE 3:** "Just a comment"s, pointers to potential future changes -> *Document and Accept*
        - **CASE 4:** ⚠️ If you want a second pair of eyes on the PR, use *Comment* to finish the review, then request
                      another reviewer and @-mention them in a comment on the PR.
    - Optional: If you find something blocking after your initial review, add another review with *Request changes* outcome.
- *Act on review:* The **PR author** acts on the review
    - React to comments
    - Fix issues (including non-blocking issues)
    - Discuss options
    - Then:
        - **CASE 1:** The **PR author** merges the PR.
        - **CASE 2:** The **PR author** re-requests a review from the original reviewer(s).
        - **CASE 3:** The **PR author** reacts to any comments. If all comments are resolved, the **PR author** merges the PR.
        - **CASE 4:** The correct next step depends on the outcome of the second review.
- *Re-review:*
    - *See Review* above
- **Any maintainer** can:
    - Close a PR if the PR is not suitable for merging, and no further changes to improve it come from the PR author.
      ⚠️ Only do this after after having communicated sensible requests with a deadline for further work in the PR comments.
    - Merge a PR and delete the remote branch if at least half of the invited reviewers have approved the PR, and no changes
      have been requested after review. This implements lazy consensus to avoid bottlenecks, where a PR has been
      approved by some reviewers but cannot be closed due to missing reviews.

### Stabilizing the codebase and making releases

⚠️ The following steps can only be taken by maintainers.

1. Create a release branch `release/v<version-id>` from `develop`.
1. Check if everything looks good:
    1. Audit the source code (using linters and other tooling).
    1. Ensure test coverage is at least 65%, and that all tests pass.
    1. Check if the documentation aligns with the code (also run tutorial to check completeness).
    1. Check if the metadata is correct in all relevant places.
1. Put up a PR from the release branch against `main`.
1. Request a review (using the same workflow as above).
1. Merge the PR into `main`.
1. Tag `main`'s `HEAD` as `v<version-id>`.
1. Push `main`.
1. Push tag.
1. Merge `main` into `develop`.
1. Delete the release branch.
1. 💡 If something goes wrong in the release branch, you can always delete it, fix things in a feature branch, merge
  into `develop` following the workflow above, and start anew.
