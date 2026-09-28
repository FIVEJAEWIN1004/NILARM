from setuptools import find_packages, setup

package_name = "arm_control_pkg"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    package_data={
        "arm_control_pkg.pumpkin_harvest": ["*.json"],
    },
    include_package_data=True,
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="chaeyoung",
    maintainer_email="chaeyoung@todo.todo",
    description="OMX pumpkin harvesting control package",
    license="Apache-2.0",
    extras_require={
        "test": ["pytest"],
    },
    entry_points={
        "console_scripts": [
            "pumpkin_harvest = "
            "arm_control_pkg.pumpkin_harvest."
            "pumpkin_full_auto_orange_harvest_to_bin_v5:main",
        ],
    },
)
