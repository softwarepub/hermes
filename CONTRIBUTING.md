# HERMES development workflow

## Preamble

> **Branching is cheap!**
>
> Work in small packets, put up small pull requests!
>
> Aim for quick turnaround times!

## Branching

We loosely follow a mixture of [GitHubFlow](https://docs.github.com/en/get-started/quickstart/github-flow) and [GitFlow](https://nvie.com/posts/a-successful-git-branching-model/):

`main`
    - Stable branch
    - Merges come only from `develop` or a hotfix branch (i.e., when something needs to be fixed in "production")

`develop`
    - Unstable development branch
    - Last "stable" is tagged: tag before attempting to break something

`feature/<describe-feature>` (including issue id when exists: `feature/62-fix-broken-thing`)
    - Branch from last tag on `develop`

### Pull requests

- As soon as you have made 1 commit in a feature branch, put up a *draft* pull request
- Keep pull requests small :skull: 
- :warning: No pre-emptive reviews on PR drafts, **unless** the PR author @-mentions with this specific request
- When you think you're done, mark PR ready for review, see below (Merge Process)

## Merge Process (into `develop`)

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
        - **CASE 4:** :warning: If you want a second pair of eyes on the PR, use "Comment" to finish review, request another reviewer and @-mention in comment.
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
- PR author
    - Close PR, or
    - Merge PR and delete remote branch

## Release/stabilization process

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
- :bulb: If something goes wrong in the release branch, you can always delete, fix things in a feature branch, merge into `develop` following workflow above, and start anew
