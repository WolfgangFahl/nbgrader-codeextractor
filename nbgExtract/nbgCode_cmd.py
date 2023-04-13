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
        parser = argparse.ArgumentParser(description='nbg-code - extract code cells from the submission and merge the cells with the test cells from the source')
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="show debug info")
        parser.add_argument("--submission", help="location of the submission notebook")
        parser.add_argument("--submission_zip", help="location of the zip file containing multiple submission notebooks")
        parser.add_argument("--source", required=True, help="location of the source notebook for the submission")
        parser.add_argument("--outputPython", default="/tmp/submission.py", help="target file to store the result")
        parser.add_argument("--output_folder", default="/tmp/submissions", help="target directory to store the result")
        parser.add_argument("--template", help="template to use for the python code generation")

        args = parser.parse_args(argv[1:])
        debug = args.debug
        if debug:
            logger.setLevel(level=logging.DEBUG)

        source = GraderNotebook(args.source)
        if args.submission:
            submission = Submission(args.submission)
            merged_submission = submission.merge_code(source)
            python_code = merged_submission.as_python_code(args.template)
            with open(args.outputPython, mode="w") as fp:
                fp.write(python_code)
        elif args.submission_zip:
            submissions = Submissions.from_zip(args.submission_zip)
            submissions.source_notebook = source
            submissions.generate_python_files(target_dir=args.output_folder, template_filepath=args.template )
        else:
            logger.info("No submissions were provided. Please use --submission or --submission_zip")

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if debug:
            print(traceback.format_exc())
        return 2

if __name__ == '__main__':
    sys.exit(main())