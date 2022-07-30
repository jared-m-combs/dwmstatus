dwmstatus
=========
Simple status bar for DWM written in Python.

Statuses are generated from async generators. The main thread awaits these generators
and pushes updates to the status bar whenever they are received. This approach has a
number of benefits.

* The python application uses a single thread.
* No polling. Updates are only generated as they occur.
* Subprocesses are kept to a minimum. (No blocks that create their own processes.)

Installation
------------
This is a Python package and can be installed in the typical manner:
```
pip3 install --user git+https://github.com/jared-m-combs/dwmstatus.git
```

Alternatively, this has no external python dependencies. You can simplly clone the repository
and copy the script onto the path.
```
git clone git+https://github.com/jared-m-combs/dwmstatus.git
sudo cp dwmstatus/dwmstatus.py /usr/local/bin/dwmstatus
sudo chmod +x /usr/local/bin/dwmstatus
```

If you don't have permission or would prefer not to use `sudo`, `~/.local/bin` is a good
installation location if it is on your `PATH`.

This project has a number of dependencies on system packages. Ensure the following are installed:
* `xorg-xsetroot`
* `playerctl`
* `pactl`
* `vmstat`

For example, in Arch Linux:
```
sudo pacman -Syu xorg-xsetroot playerctl pactl vmstat
```

Generators
----------
* Currently Playing Media - Uses `playerctl` to display media. Uses `dbus-monitor` to detect track changes.
* Master Volume Level - Uses `pactl --subscribe` to detect volume changes.
* CPU and Memory Usage - Uses `vmstat` to periodically update cpu and memory statistics.
* Current Date and Time - Generates date/time updates using the `datetime` Python package.

Contributing
------------
Open a pull request and I'll take a look. The implementation is currently very minimal. I'll probably:
* Add the ability to select generators via command line arguments.
* Add the ability to use i3 blocks.

Alternatively, this project uses the [Unlicense](https://unlicense.org/) and you are free
to fork it and do as you please.
