import json
from pathlib import Path

import build


def print_header(message: str) -> None:
    print("\033[95m" + message + "\033[0m", flush=True)


def print_error(message: str) -> None:
    print("\033[91m" + message + "\033[0m", flush=True)


if __name__ == "__main__":
    print_header("Starting Ubuntu tests")

    testing_dict = {
        "distro_name": "ubuntu",
        "distro_version": "",
        "de_name": "",
        "username": "localuser",
        "password": "test",
        "device": "image",
        "kernel_type": "mainline"
    }
    # deepin currently results in a cli boot in 22.10
    available_des = ["gnome", "kde", "xfce", "lxqt", "budgie", "deepin", "cli"]
    failed_distros = []
    size_dict = {}

    # Start testing
    for version in ["22.04", "22.10"]:
        testing_dict["distro_version"] = version
        for de_name in available_des:
            retry = True
            testing_dict["de_name"] = de_name
            print_header(f"Testing Ubuntu + {de_name}")
            try:
                build.start_build(verbose=True, local_path=None, dev_release=False, build_options=testing_dict,
                                  no_download_progress=True)
                # calculate shrunk image size in gb and round it to 2 decimal places
                size_dict[de_name] = round(Path("./depthboot.img").stat().st_size / 1073741824, 1)
            except Exception as e:
                print_error(str(e))
                print_error(f"Failed to build Ubuntu + {de_name}")
                failed_distros.append(de_name)
                size_dict[de_name] = 0
            except SystemExit:
                if retry:
                    print_error(f"Failed to build Ubuntu + {de_name}, retrying")
                    retry = False
                    build.start_build(verbose=True, local_path=None, dev_release=False, build_options=testing_dict,
                                      no_download_progress=True)
                    # calculate shrunk image size in gb and round it to 2 decimal places
                    size_dict[de_name] = round(Path("./depthboot.img").stat().st_size / 1073741824, 1)
                else:
                    print_error(f"Failed twice to build Ubuntu + {de_name}")
                    failed_distros.append(de_name)
                    size_dict[de_name] = 0

        with open(f"results_ubuntu_{version}.txt", "w") as f:
            f.write(str(failed_distros))

        with open(f"sizes_ubuntu_{version}.json", "w") as file:
            json.dump(size_dict, file)
