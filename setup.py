import setuptools

#with open("README.md", "r") as fh:
    #long_description = fh.read()
long_description = ''

setuptools.setup(
    name="camdict-dio",
    version="0.1",
    author="Darkclainer",
    author_email="darkclainer@gmail.com",
    description="Parser for html page of web dictionary",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",

    packages=setuptools.find_packages('src/'),
    package_dir={
        '': 'src'
    },

    include_package_data=True,

    install_requires=[
        'bs4',
        'requests'
    ],

    setup_requires=[
        'pytest-runner'
    ],

    tests_require=[
        'pytest'
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
