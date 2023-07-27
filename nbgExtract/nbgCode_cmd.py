import argparse
import logging
import sys
import os
import traceback

from nbgExtract import logger
from nbgExtract.notebook import GraderNotebook, Submission, Submissions


def main(argv=None):
    """
    main routine
    """

    if argv is None:
        argv = sys.argv
    program_name = os.path.basename(sys.argv[0])
    debug = False
    try:
        parser = argparse.ArgumentParser(description='nbg-code - extract code cells from the submission and merge the '
                                                     'cells with the test cells from the source')
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="show debug info")
        parser.add_argument("-wcc", "--with_cell_comments",
                            action="store_true", help="add cell metadata as python comment")
        parser.add_argument("--submission", help="location of the submission notebook")
        parser.add_argument("--submission_zip",
                            help="location of the zip file containing multiple submission notebooks")
        parser.add_argument("--source", required=True, help="location of the source notebook for the submission")
        parser.add_argument("--outputPython", default="/tmp/submission.py", help="target file to store the result")
        parser.add_argument("--output_folder", default="/tmp/submissions", help="target directory to store the result")
        parser.add_argument("--template", help="template to use for the python code generation")
        parser.add_argument("--only_merge_answers", action="store_true",
                            help="Only merge the answers to the source notebook. "
                                 "If not set merge only the test cells to the submission notebook")

        args = parser.parse_args(argv[1:])
        debug = args.debug
        if debug:
            logger.setLevel(level=logging.DEBUG)

        source = GraderNotebook(args.source)
        if args.submission:
            submission = Submission(args.submission)
            merged_submission = submission.merge_code(source, args.only_merge_answers)
            python_code = merged_submission.as_python_code(args.template)
            with open(args.outputPython, mode="w") as fp:
                fp.write(python_code)
        elif args.submission_zip:
            submissions = Submissions.from_zip(args.submission_zip, debug=debug)
            submissions.source_notebook = source
            submissions.generate_python_files(
                    target_dir=args.output_folder,
                    template_filepath=args.template,
                    with_cell_comments=args.with_cell_comments,
                    only_merge_answers=args.only_merge_answers
            )
        else:
            logger.info("No submissions were provided. Please use --submission or --submission_zip")

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        indent = len(program_name) * " "
        err_msg=f"""{program_name}:{repr(e)}\n{indent}for help use --help"""
        print(err_msg, file=sys.stderr, flush=True)
        if debug:
            print(traceback.format_exc())
        return 2


if __name__ == '__main__':
    args = None
    sys.exit(main(args))
