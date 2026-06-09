from setuptools import setup, find_namespace_packages
import os

REQ_FILE = 'requirements.txt'
VERSION = '0.3.2'

def get_requires():
    thisdir = os.path.dirname(__file__)
    reqpath = os.path.join(thisdir, REQ_FILE)
    return [line.rstrip('\n') for line in open(reqpath)]

setup(name='korean_bank_tx_crawler',
      version=VERSION,
      url='https://github.com/promet99/simple_bank_korea',
      license='MIT',
      author='Junbum Lee',
      author_email='jun@beomi.net',
      description='Crawling Korea bank transactions',
      packages=find_namespace_packages(include=['simple_bank_korea', 'simple_bank_korea.*'], exclude=['*.assets', 'simple_bank_korea.kb.assets', 'simple_bank_korea.woori.assets']),
      package_data={
          'simple_bank_korea.kb': ['assets/*.png'],
          'simple_bank_korea.woori': ['assets/*.png'],
      },
      long_description=open('README.md', 'r', encoding="utf-8").read(),
      long_description_content_type="text/markdown",
      zip_safe=False,
      install_requires=get_requires(),
      include_package_data=True,
      classifiers=[
            "Programming Language :: Python :: 3",
      ],
)
