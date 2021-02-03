from setuptools import (
    setup,
    find_packages,
)


with open('README.md') as fh:
    long_description = fh.read()

setup(name='socid-extractor',
      version='0.0.8',
      description='Extract accounts\' identifiers from personal pages on various platforms',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/soxoj/socid-extractor',
      entry_points={'console_scripts': ['socid_extractor = socid_extractor.cli:run']},
      packages=find_packages(),
      author='Soxoj',
      author_email='soxoj@protonmail.com',
      license='GPL-3.0',
      zip_safe=False)
