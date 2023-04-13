# nbgrader-codeextractor
[![Github Actions Build](https://github.com/WolfgangFahl/nbgrader-codeextractor/workflows/Build/badge.svg?branch=main)](https://github.com/WolfgangFahl/nbgrader-codeextractor/actions?query=workflow%3ABuild+branch%3Amain)
[![GitHub issues](https://img.shields.io/github/issues/WolfgangFahl/nbgrader-codeextractor.svg)](https://github.com/WolfgangFahl/nbgrader-codeextractor/issues)
[![GitHub issues](https://img.shields.io/github/issues-closed/WolfgangFahl/nbgrader-codeextractor.svg)](https://github.com/WolfgangFahl/nbgrader-codeextractor/issues/?q=is%3Aissue+is%3Aclosed)
[![GitHub](https://img.shields.io/github/license/WolfgangFahl/nbgrader-codeextractor.svg)](https://www.apache.org/licenses/LICENSE-2.0)

Extracts code cells from nbgrader notebooks for  executability outside jupyter environment

# What is it?
[nbgrader](https://github.com/jupyter/nbgrader) is a tool for automatically
grading jupyter-notebook that are used in education for exercises

The nbgrader-codeextractor is compatible to nbrader and allows to extract
the python code from the nbgrader cells and "wrap" the code with given templates.

This approach may e.g. be used to execute the code as python unittests and
have an additional capability to analyze the submissions of students.