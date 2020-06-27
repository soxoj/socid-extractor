from setuptools import (
    setup,
    find_packages,
)


with open('README.md') as fh:
    long_description = fh.read()

setup(name='socid_extractor',
      version='0.0.1',
      description='Extract accounts\' identifiers from personal pages on various platforms',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/soxoj/socid_extractor',
      packages=find_packages(),
      author='Soxoj',
      author_email='soxoj@protonmail.com',
      license='GPL-3.0',
      zip_safe=False)
