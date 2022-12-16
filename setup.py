from pathlib import Path

from setuptools import setup

scripts = [
    str(filename)
    for filename in Path('./scripts').glob('**/*')
    if filename.is_file() and filename.name != '__pycache__'
]

setup(scripts=scripts)
