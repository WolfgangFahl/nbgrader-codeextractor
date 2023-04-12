import unittest
from pathlib import Path

from nbgExtract.notebook import GraderNotebook, Submission


class TestGraderNotebook(unittest.TestCase):
    """
    test GraderNotebook
    """

    def setUp(self) -> None:
        """
        setup test env
        """
        self.resource_dir = f"{Path(__file__).parent.absolute()}/resources"

    def test_extraction(self):
        """
        tests extraction of code cells
        """
        assignment_dir = f"{self.resource_dir}/python_addition"
        test_params = [ # file path of assignment, strings that should be extracted
            (f"{assignment_dir}/python_addition_source.ipynb",
             ["cell-9fb6fe3588ec4909", "### BEGIN SOLUTION", "cell-744e5dbe470759ae", "### BEGIN HIDDEN TESTS"]),
            (f"{assignment_dir}/python_addition_release.ipynb",
             ["cell-9fb6fe3588ec4909", "# YOUR CODE HERE", "raise NotImplementedError()", "cell-744e5dbe470759ae"]),
            (f"{assignment_dir}/python_addition_correct_submission.ipynb",
             ["cell-9fb6fe3588ec4909", "# YOUR CODE HERE", "z = x + y", "cell-744e5dbe470759ae"]),
        ]
        for test_param in test_params:
            with self.subTest(test_param=test_param):
                assignment_filepath, expected_extractions = test_param
                grader_notebook = GraderNotebook(notebook=assignment_filepath)
                grader_notebook.load()
                code = grader_notebook.as_python_code()
                print(code)
                for expected in expected_extractions:
                    self.assertIn(expected, code)


class TestSubmission(unittest.TestCase):
    """
    test Submission
    """

    def setUp(self) -> None:
        """
        setup test env
        """
        self.resource_dir = f"{Path(__file__).parent.absolute()}/resources"

    def test_merging_code(self):
        """
        tests merging code cells of a submission with its source
        """
        source_file = f"{self.resource_dir}/python_addition/python_addition_source.ipynb"
        submission_file = f"{self.resource_dir}/python_addition/python_addition_correct_submission.ipynb"
        grader_notebook = GraderNotebook(notebook=source_file)
        submission = Submission(notebook=submission_file)
        merged_submission = submission.merge_code(grader_notebook)
        code = merged_submission.as_python_code()
        expected_lines = ["cell-9fb6fe3588ec4909", "# YOUR CODE HERE", "### BEGIN HIDDEN TESTS"]
        for expected_line in expected_lines:
            self.assertIn(expected_line, code)



if __name__ == '__main__':
    unittest.main()
