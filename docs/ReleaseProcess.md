# 🥭 Mango Explorer


# 📦 Overview

This page documents the release process for `mango-explorer` - how to check, build and package the [Pypi library](https://pypi.org/project/mango-explorer/) and the [docker image](https://hub.docker.com/r/opinionatedgeek/mango-explorer-v3).

**If you don't have permissions on the [main mango-explorer repo](https://github.com/blockworks-foundation/mango-explorer) you won't be able to perform these actions.**


## 📦 Release Process

The release process is controlled by Github Actions.

* On every push to the repository, the unit tests and lint checks are performed.
* On every new version tag, the unit tests and lint checks are performed, then the Pypi package is built and pushed to Pypi, and the docker image is built and pushed to Docker Hub.

It's worth emphasising - **creating a new version will automatically build and package the release, making the new code available to everyone.** If you do not want to make a new release publicly available, do not create a new version tag!


## 🧪 Pre-Release Checks

Every time new code is pushed to the repo, the `.github/on-push.yaml` workflow triggers the `test-and-lint.yaml` workflow. This will run the unit tests and lint checks, equivalent to running `make test && make lint` during development.

All tests should pass (`pyserum` causes 1 warning).

Do not proceed with the release if this step fails.


## 🏭 Releasing a New Version

All releases must have a distinct version number of the form X.Y.Z where X, Y, and Z are all numbers. Typically a new release will just increment the previous version number.


### 1. Update Version Number
So the first step is to update the file `pyproject.toml` with the new version number. It's right at the start of the file:
```
[tool.poetry]
version = "0.1.8"
...
```
For the example here, the next version would then be 0.1.9, so the updated file would then look like:
```
[tool.poetry]
version = "0.1.9"
...
```


### 2. Check In Version Number Change

Next that version number needs to be checked in to git. Commit the change using the version number as the comment, with a leading 'v', so 'v0.1.9' in this case.


### 3. Push Changes To Github

Push the changes to Github.


### 4. Create a New Release on Github

To create a new release of the version, go to the [Tags page](https://github.com/blockworks-foundation/mango-explorer/tags), choose 'Releases', and click the 'Draft a new release' button.

On the form that appears, click the 'Choose a tag' dropdown, and in the 'Find or create a new tag' input box, type in your version number with a preceding 'v', so in our example type in v0.1.9.

Please do not get creative here. The tag is matched using a regular expression so additional comments will just prevent the release mechanism from starting. The format **must** be the letter 'v', a decimal number, a period, a decimal number, a period, and a decimal number. Nothing else, and no trailing spaces.

When you've entered the tag, confirm it by pressing the '+ Create a new tag: v0.1.9 on publish' action that appears.

Then enter v0.1.9 as the 'Release title' and you can let your full creativity flow in the 'Describe this release' field if you so choose.

Then press the 'Publish release' button, and you're done!

The Pypi and Docker workflows should kick in automatically now the new version is created and tagged, and you can check the progress of these steps in the [Github Actions](https://github.com/blockworks-foundation/mango-explorer/actions) page for the repo.

These actions can take quite a few minutes to run but once they complete successfully it means the packaged code is available on both [Pypi](https://pypi.org/project/mango-explorer/) and [Docker Hub](https://hub.docker.com/r/opinionatedgeek/mango-explorer-v3).


## Troubleshooting

It is possible to run (or re-run) the different workflow actions manually if they failed for transient reasons.

To re-run the Docker Image publishing:
* Go to [Github Actions](https://github.com/blockworks-foundation/mango-explorer/actions)
* Click on the 'Publish to Docker' workflow on the left of the page
* It says 'This workflow has a workflow_dispatch event trigger.' Click the 'Run workflow' dropdown to the right of this line.
* Click 'Run workflow'

To re-run the Pypi package publishing:

(Note that publishing to Pypi is not going to succeed if a previous release with the same version number has already been published to Pypi.)

* Go to [Github Actions](https://github.com/blockworks-foundation/mango-explorer/actions)
* Click on the 'Publish to Pypi' workflow on the left of the page
* It says 'This workflow has a workflow_dispatch event trigger.' Click the 'Run workflow' dropdown to the right of this line.
* Click 'Run workflow'
