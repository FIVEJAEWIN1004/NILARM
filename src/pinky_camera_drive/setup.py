import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'pinky_camera_drive'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
         glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pinky',
    maintainer_email='pinky@example.com',
    description='Safe camera-gated straight-drive test for Pinky Pro',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'camera_straight_drive = '
            'pinky_camera_drive.camera_straight_drive:main',
        ],
    },
)
