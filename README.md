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

# Usage
```bash
nbg-code -h
usage: nbg-code [-h] [-d] [--submission SUBMISSION] [--submission_zip SUBMISSION_ZIP] --source
                SOURCE [--outputPython OUTPUTPYTHON] [--output_folder OUTPUT_FOLDER]
                [--template TEMPLATE]

nbg-code - extract code cells from the submission and merge the cells with the test cells from
the source

options:
  -h, --help            show this help message and exit
  -d, --debug           show debug info
  --submission SUBMISSION
                        location of the submission notebook
  --submission_zip SUBMISSION_ZIP
                        location of the zip file containing multiple submission notebooks
  --source SOURCE       location of the source notebook for the submission
  --outputPython OUTPUTPYTHON
                        target file to store the result
  --output_folder OUTPUT_FOLDER
                        target directory to store the result
  --template TEMPLATE   template to use for the python code generation
 ```
# Example

## single submission
```bash
nbg-code --source tests/resources/python_addition/python_addition_source.ipynb --submission tests/resources/python_addition/python_addition_correct_submission.ipynb --template nbgExtract/resources/default_python_template.tpy -d
tail -3 /tmp/submission.py
### BEGIN HIDDEN TESTS
assert z == 10
### END HIDDEN TESTS%                    
```
