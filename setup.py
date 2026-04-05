from setuptools import setup

setup(
    name="my-tracker",
    version="0.1.0",
    py_modules=["tracker"],
    entry_points={
        "console_scripts": [
            "tracker = tracker:main",
        ],
    },
)
