# Copyright 2019, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import find_packages, setup

setup(
    name="opencensus-ext-tornado",
    version="0.2.dev0",  # noqa
    author="OpenCensus Authors, Marc Peake",
    author_email="mpeake@gmail.com",
    classifiers=[
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="OpenCensus Tornado Integration",
    include_package_data=True,
    long_description=open("README.rst").read(),
    install_requires=[
        "opencensus >= 0.7.7",
        "tornado >= 6.0.3",
        "wrapt >= 1.11.1"
    ],
    extras_require={},
    license="Apache-2.0",
    packages=find_packages(exclude=("examples", "tests",)),
    namespace_packages=[],
    url="https://github.com/peakm0/opencensus-ext-tornado",  # noqa: E501
    zip_safe=False
)