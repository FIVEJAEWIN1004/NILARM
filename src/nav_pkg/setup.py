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
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='junghyo',
    maintainer_email='junghyo@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'drive_test = nav_pkg.drive_test:main',
            'obstacle_detector = nav_pkg.obstacle_detector:main',
            'odom_reader = nav_pkg.odom_reader:main',
            'odom_drive_test = nav_pkg.odom_drive_test:main',
            'odom_rotate_test = nav_pkg.odom_rotate_test:main',
            'path_test = nav_pkg.path_test:main',
            'goal_point_test = nav_pkg.goal_point_test:main',
        ],
    },
)
