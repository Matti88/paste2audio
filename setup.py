from setuptools import setup, find_packages

setup(
    name='paste2audio',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pyperclip',
        'ffmpeg-python',
        'numpy',
        'gtts',
        'PyQt6',
        'soundfile',
    ],
    entry_points={
        'console_scripts': [
            'paste2audio=paste2audio.main:main',
        ],
    },
)
