import contextlib
from functions import *
from urllib.request import urlretrieve


def config(de_name: str, distro_version: str, verbose: bool) -> None:
    set_verbose(verbose)
    print_status("Configuring Debian")

    print_status("Installing dependencies")
    # install apt-add-repository
    chroot("apt-get update -y")
    chroot("apt-get install -y software-properties-common")
    # add non-free repos
    chroot("add-apt-repository -y non-free")
    # Add eupnea repo
    mkdir("/mnt/depthboot/usr/local/share/keyrings", create_parents=True)
    # download public key
    urlretrieve("https://eupnea-linux.github.io/apt-repo/public.key",
                filename="/mnt/depthboot/usr/local/share/keyrings/eupnea.key")
    with open("/mnt/depthboot/etc/apt/sources.list.d/eupnea.list", "w") as file:
        file.write("deb [signed-by=/usr/local/share/keyrings/eupnea.key] https://eupnea-linux.github.io/"
                   "apt-repo/debian_ubuntu kinetic main")
    # update apt
    chroot("apt-get update -y")
    chroot("apt-get upgrade -y")
    # Install general dependencies + eupnea packages
    chroot("apt-get install -y network-manager sudo firmware-linux-free firmware-linux-nonfree "
           "firmware-iwlwifi iw")
    chroot("apt-get install -y eupnea-utils eupnea-system")

    print_status("Downloading and installing de, might take a while")
    # DEBIAN_FRONTEND=noninteractive skips locale setup questions
    match de_name:
        case "gnome":
            print_status("Installing GNOME")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y gnome/stable gnome-initial-setup")
        case "kde":
            print_status("Installing KDE")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y task-kde-desktop")
        case "xfce":
            print_status("Installing Xfce")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y task-xfce-desktop xfce4-pulseaudio-plugin "
                   "gnome-software epiphany-browser")
        case "lxqt":
            print_status("Installing LXQt")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y task-lxqt-desktop plasma-discover")
        case "deepin":
            print_error("Deepin is not available for Debian")
            exit(1)
        case "budgie":
            print_status("Installing Budgie")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y budgie-desktop budgie-indicator-applet "
                   "budgie-core lightdm lightdm-gtk-greeter gnome-terminal epiphany-browser gnome-software")
            chroot("systemctl enable lightdm.service")
        case "cli":
            print_status("Skipping desktop environment install")
        case _:
            print_error("Invalid desktop environment! Please create an issue")
            exit(1)

    if de_name != "cli":
        # Set system to boot to gui
        chroot("systemctl set-default graphical.target")

    # GDM3 auto installs gnome-minimal. Remove it if user didn't choose gnome
    if de_name != "gnome":
        rmfile("/mnt/depthboot/usr/share/xsessions/ubuntu.desktop")
        chroot("apt-get remove -y gnome-shell")
        chroot("apt-get autoremove -y")

    # Fix gdm3, https://askubuntu.com/questions/1239503/ubuntu-20-04-and-20-10-etc-securetty-no-such-file-or-directory
    with contextlib.suppress(FileNotFoundError):
        cpfile("/mnt/depthboot/usr/share/doc/util-linux/examples/securetty", "/mnt/depthboot/etc/securetty")
    print_status("Desktop environment setup complete")

    # Replace input-synaptics with newer input-libinput, for better touchpad support
    print_status("Upgrading touchpad drivers")
    chroot("apt-get remove -y xserver-xorg-input-synaptics")
    chroot("apt-get install -y xserver-xorg-input-libinput")

    # TODO: Pre-update python3 to 3.10 on stable
    # Pre-updating to python3.10 breaks the gnome first time installer...
    '''
    # Pre-update python to 3.10 as some postinstall scripts require it
    print_status("Upgrading python to 3.10")
    # switch to unstable channel
    with open("/mnt/depthboot/etc/apt/sources.list", "r") as file:
        original_sources = file.readlines()
    sources = original_sources
    sources[0] = sources[0].replace("stable", "unstable")
    with open("/mnt/depthboot/etc/apt/sources.list", "w") as file:
        file.writelines(sources)
    # update and install python
    print_status("Installing python 3.10")
    chroot("apt-get update -y")
    chroot("apt-get install -y python3")
    print_status("Python 3.10 installed")
    # revert to stable channel
    with open("/mnt/depthboot/etc/apt/sources.list", "w") as file:
        file.writelines(original_sources)
    chroot("apt-get update -y")
    '''
    print_status("Debian setup complete")


def chroot(command: str) -> None:
    if verbose:
        bash(f'chroot /mnt/depthboot /bin/bash -c "{command}"')
    else:
        bash(f'chroot /mnt/depthboot /bin/bash -c "{command}" 2>/dev/null 1>/dev/null')  # supress all output
