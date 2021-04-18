from setuptools import (
    setup,
    find_packages,
)


with open('README.md') as fh:
    long_description = fh.read()

setup(name='socid-extractor',
      version='0.0.17',
      description='Extract accounts\' identifiers from personal pages on various platforms',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/soxoj/socid-extractor',
      entry_points={'console_scripts': ['socid_extractor = socid_extractor.cli:run']},
      packages=find_packages(),
      install_requires=open('requirements.txt').readlines(),
      author='Soxoj',
      author_email='soxoj@protonmail.com',
      license='GPL-3.0',
      zip_safe=False)
