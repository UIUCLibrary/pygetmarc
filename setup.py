from setuptools import setup


setup(
    packages=['uiucprescon.pygetmarc'],
    test_suite="tests",
    namespace_packages=["uiucprescon"],
    setup_requires=['pytest-runner'],
    install_requires=['aiohttp'],
    tests_require=['pytest'],
    zip_safe=False,
)
