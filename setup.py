from setuptools import setup


setup(
    packages=['uiucprescon.pygetmarc', 'uiucprescon.pygetmarc.data'],
    test_suite="tests",
    namespace_packages=["uiucprescon"],
    setup_requires=['pytest-runner'],
    install_requires=['aiohttp', 'importlib_resources;python_version<"3.7"'],
    tests_require=['pytest'],
    package_data={'uiucprescon.pygetmarc.data': ['template.xml']},
    zip_safe=False,
)
