#!/usr/bin/env python

from setuptools import setup

import os
import shutil
from hashlib import sha512

def file_hash(path):
    with open(path, 'rb') as f:
        return sha512(f.read()).digest()

def make_launcher():

    if not os.path.exists('launcher'):
        os.makedirs('launcher')

    launcher_path = os.path.join('launcher', 'cursewords')

    if not os.path.exists(launcher_path) or (file_hash('cursewords.py') != file_hash(launcher_path)):
        shutil.copy('cursewords.py', launcher_path)

    return [launcher_path]

def main():
    setup(
        name='cursewords',
        version='420.69',
        packages=(
            'cursewords',
            'cursewords.core',
            'cursewords.container',
            'cursewords.gui',
            'cursewords.etc'
        ),
        scripts=make_launcher()
    )

if __name__ == '__main__':
    main()