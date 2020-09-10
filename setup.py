# -*- coding: utf-8 -*-
""""""


from setuptools import setup, find_packages


setup(
    name="stylegan-encoder",
    version="0.0.0",
    description="StyleGAN encoder",
    # packages=find_packages(),
    py_modules=["encoder"],
    python_requires='>=3.6',
    install_requires=[],
    # entry_points={
    #     "console_scripts": [
    #         # "deliverable-run=deliverable.__main__:main"
    #     ]
    # },
)
