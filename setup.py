from setuptools import setup, find_packages
import versioneer

setup(
    name='pbi-tools',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='Power BI REST API wrapper and other tools',
    long_description=open('README.md').read(),
    install_requires=['requests'],
    url='https://github.com/thomas-daughters/pbi-tools',
    author='Sam Thomas',
    author_email='sam.thomas@redkite.com'
)