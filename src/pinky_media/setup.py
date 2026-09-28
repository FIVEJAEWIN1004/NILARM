from glob import glob

from setuptools import find_packages, setup

package_name = 'pinky_media'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/assets', glob('assets/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pinky',
    maintainer_email='pinky@example.com',
    description='Pinky LCD image and looping match music',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'music_player = pinky_media.music_player:main',
            'buzzer_player = pinky_media.buzzer_player:main',
            'pinky_status_display = pinky_media.pinky_status_display:main',
        ],
    },
)
