================================================
Welcome to Geospatial Analysis Pipelines (GAPs)!
================================================

|Docs| |Tests| |Linter| |Codecov|
|PyPi| |PythonV| |Ruff| |Pixi|
|License| |SWR|

.. |Docs| image:: https://github.com/NatLabRockies/gaps/workflows/Documentation/badge.svg
    :target: https://natlabrockies.github.io/gaps/

.. |Tests| image:: https://github.com/NatLabRockies/gaps/workflows/Pytests/badge.svg
    :target: https://github.com/NatLabRockies/gaps/actions?query=workflow%3A%22Pytests%22

.. |Linter| image:: https://github.com/NatLabRockies/gaps/workflows/Lint%20Code%20Base/badge.svg
    :target: https://github.com/NatLabRockies/gaps/actions?query=workflow%3A%22Lint+Code+Base%22

.. |PyPi| image:: https://img.shields.io/pypi/pyversions/NLR-GAPs.svg
    :target: https://pypi.org/project/NLR-GAPs/

.. |PythonV| image:: https://badge.fury.io/py/NLR-GAPs.svg
    :target: https://badge.fury.io/py/NLR-GAPs

.. |Codecov| image:: https://codecov.io/gh/NatLabRockies/gaps/branch/main/graph/badge.svg?token=6VZK0Q2QNQ
    :target: https://codecov.io/gh/NatLabRockies/gaps

.. |Ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff

.. |License| image:: https://img.shields.io/badge/License-BSD_3--Clause-blue.svg
    :target: https://opensource.org/licenses/BSD-3-Clause

.. |Pixi| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json
    :target: https://pixi.sh

.. |SWR| image:: https://img.shields.io/badge/SWR--23--28_-blue?label=NLR
    :alt: Static Badge

.. inclusion-intro

Geospatial Analysis Pipelines (GAPs) is a framework designed
to assist researchers and software developers add execution
tools to their geospatial python models. Born from the
open-source `reV <https://github.com/NatLabRockies/reV>`_ model, GAPs is a
robust and easy-to-use engine that provides a rich set of features
such as command-line interface (CLI) generation and documentation,
basic High-Performance Computing (HPC) scaling capabilities,
configuration file generation, job status monitoring, and more.


Who should use GAPs
===================
GAPs is intended to be used by researchers and/or software developers
who have implemented a working python model but have not yet added any
external model execution tools. Within minimal effort, developers can
use GAPs to add a variety of utility for end-users, including a complete
set of CLI commands and documentation pulled from the model run function
docstrings. In addition, GAPs provides basic HPC execution capabilities,
particularly catered towards embarrassingly parallel geospatial models
(e.g. single-location models such as the `System Advisor Model <https://sam.nlr.gov>`_).
GAPs can automatically distribute the execution of such models over a large
geospatial extent (e.g. CONUS) across many parallel HPC nodes.

GAPs is **NOT** a workflow management system (WMS), and therefore does not
provide any of the in-depth tools/capabilities expected from a proper WMS.
However, GAPs-supported models can sometimes be included as part of the workflow in
WMS tools like `Torc <https://pages.github.natlabrockies.gov/viz/wms/index.html#/>`_.

To get started, take a look at the examples for
`analysts <https://natlabrockies.github.io/gaps/misc/examples.users.html>`_ or
`model developers <https://natlabrockies.github.io/gaps/misc/examples.developers.html>`_
or dive straight into the full `documentation <https://natlabrockies.github.io/gaps/>`_.


Installing GAPs
===============

The quickest way to install GAPs for users is from PyPi:

.. code-block:: shell

    pip install nlr-gaps

If you are a developer contributing to GAPs, we recommend using `pixi <https://pixi.sh/latest/>`_:

.. code-block:: shell

    pixi shell

For detailed instructions, see the `installation documentation <https://natlabrockies.github.io/gaps/misc/installation.html>`_.

Development
===========
Please see the `Development Guidelines <https://natlabrockies.github.io/gaps/dev/index.html>`_
if you wish to contribute code to this repository.


Acknowledgments
===============
.. inclusion-ack

Paul Pinchuk and Grant Buster. Geospatial Analysis Pipelines. 2023. https://doi.org/10.11578/dc.20230426.7

The authors of this code would like to thank ExxonMobil Corporation for their contributions to this effort.
