from setuptools import setup, find_packages

setup(
    name="pbi-tools",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    license="MIT",
    description="Power BI REST API wrapper and other tools",
    long_description=open("README.md").read(),
    use_scm_version={
        "version_scheme": "python-simplified-semver",
        "local_scheme": "no-local-version"
    },
    setup_requires=['setuptools_scm'],
    install_requires=["gitpython", "requests"],
    url="https://github.com/thomas-daughters/pbi-tools",
    author="Sam Thomas",
    author_email="sam.thomas@redkite.com",
)
