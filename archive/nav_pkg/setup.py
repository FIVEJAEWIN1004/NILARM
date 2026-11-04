import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'nav_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml') + glob('config/*.md')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='junghyo',
    maintainer_email='junghyo@todo.todo',
    description='NILARM navigation package',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'line_detector = nav_pkg.line_detector:main',
            'line_follower = nav_pkg.line_follower:main',
            'road_perception = nav_pkg.road_perception:main',
            'ir_align_node = nav_pkg.ir_align_node:main',
        ],
    },
)
