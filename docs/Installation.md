# 🥭 Mango Explorer


# 📦 Installation

`mango-explorer` is a [regular Python library](https://pypi.org/project/mango-explorer/), available to install however you usually install Python libraries. It also contains some useful command-line tools to make using [Mango](https://www.mango.markets/) easier.

This walkthrough shows one way of installing `mango-explorer`. If you're not familiar with some aspects of Python this guide aims to get you up and running quickly.

This is certainly not the only way, and there isn't a single 'right' way. Feel free to choose whatever works for you.


## 1. Create Python Virtual Environment

You don't have to create a Python 'venv' but it helps isolate dependencies to make sure you're running exactly the code you expect.

Here we'll create a directory - `NewMangoProject` - and create a Python virtual environment in the `.venv` subdirectory.

```
mkdir NewMangoProject
cd NewMangoProject
python3 -m venv .venv
```


## 2. Set Up `direnv`

[`direnv`](https://direnv.net/) is a useful tool that allows you to configure environment variables when you're within specific directories.

We'll use it here to update the `$PATH` variable used to locate commands - this will allow us to use the `.venv` Python commands and the `mango-explorer` commands without having to prefix them with path names.

Assuming you have `direnv` installed for your operating system, create a file called `.envrc` in the `NewMangoProject` directory with the following contents:
```
CURRENT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PATH=$CURRENT_DIRECTORY/.venv/bin:$PATH:$CURRENT_DIRECTORY/.venv/lib/python3.9/site-packages/bin
```

`direnv` will see the new file and require explicit authorisation to load it. (It only does this when the file is new or is changed.) To authorise `direnv` to use the new file, enter:
```
direnv allow
```


## 3. Add `mango-explorer` Dependency

Now we need to tell Python this project will use `mango-explorer`, and that it should be downloaded and installed. We'll use `pip` for installing packages, so create a `requirements.txt` file with the following contents:
```
mango-explorer
```

Then install the dependencies with the following command:
```
pip install -r requirements.txt
```


## 4. Verify Installation

The dependencies should all install without error. You can check everything is OK by running the following command:
```
mango-explorer-version
```

This runs the `mango-explorer-version` command that's in the `mango-explorer` package that was installed in the `.venv` and was found using the `$PATH` that was set by `direnv` from the `.envrc` file. If you see something like this (the version details may be different) then you have successfully installed `mango-explorer`:
```
« PackageVersion 3.3.0 - '1967a63 [Thu Jan 20 16:49:40 2022 +0000] - v3.3.0' »
```


## 5. Use `mango-explorer` From Python

Now let's write some Python code to load the `mango-explorer` library and use it. Create a file `showversion.py` with the following contents:
```
import mango

print("From Python code:", mango.version())
```

Now run it:
```
python showversion.py
```

You should see output like the following (again, the actual version details may be different):
```
From Python code: « PackageVersion 3.3.0 - '1967a63 [Thu Jan 20 16:49:40 2022 +0000] - v3.3.0' »
```

But that's not doing much with Mango. Let's try loading and displaying the Mango `Group`. Create a file `showgroup.py` with the following contents:
```
import mango

context = mango.ContextBuilder.build()
group = mango.Group.load(context)
print(group)
```

And run it:
```
python showgroup.py
```

You should see a lot of details about the current `Group`:
```
« Group Version.V3 [98pjRuQjK3qA6gXts96PqZT4Ze5QmnCmt3QYjhbUSPue]
    « Metadata Version.V1 - Group: Initialized »
    Name: mainnet.1
    Signer [Nonce: 0]: 9BVcYqEQxyccuwznvxXqDkSJFavvTyheiTYk231T1A8S
    Admin: 7Gm5zF6FNJpyhqdwKcEdMQw3r5YzitYUGVDKYMPT1cMy
    ...
```

Showing the full output would clutter things up here, but you should be able to see all the `Group` details on your screen.


## 6. Conclusion

That's it - that's `mango-explorer` installed with the command-line tools all available to you and the library ready for you to `import` into your own programs.

Happy coding!