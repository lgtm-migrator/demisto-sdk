from __future__ import print_function

import os
import re
from demisto_sdk.common.tools import run_command

from demisto_sdk.common.tools import print_error, get_latest_release_notes_text, \
    get_release_notes_file_path

release_notes_standard = 'https://github.com/demisto/content/blob/master/docs/release_notes/README.md'


class ReleaseNotesValidator:
    """Release notes validator is designed to ensure the existence and correctness of the release notes in content repo.

    Attributes:
        file_path (str): the path to the file we are examining at the moment.

    """

    def __init__(self, file_path):
        # type: (str) -> None
        self.file_path = file_path
        self.release_notes_path = get_release_notes_file_path(self.file_path)
        self.release_notes = get_latest_release_notes_text(self.release_notes_path)
        self.master_diff = self.get_master_diff()

    def get_master_diff(self):
        # type: () -> str
        """Gets difference between current branch and origin/master

        git diff with the --unified=10000 option means that if there exists a
        difference between origin/master and current branch, the output will have at most 10000
        lines of context.

        Returns:
            str. empty string if no changes made or no origin/master branch, otherwise full difference context.

        """
        try:
            return run_command(F'git diff --unified=10000 '
                               F'origin/master {self.release_notes_path}')  # type: str

        finally:
            return ''

    def is_release_notes_changed(self):
        # type: () -> bool
        """Validates that a new comment was added to release notes.

        Returns:
            bool. True if comment was added, False otherwise.

        """
        # there exists a difference between origin/master and current branch
        if self.master_diff:
            diff_releases = self.master_diff.split('##')
            unreleased_section = diff_releases[1]
            unreleased_section_lines = unreleased_section.split('\n')

            adds_in_diff = 0
            removes_in_diff = 0

            for line in unreleased_section_lines:
                if line.startswith('+'):
                    adds_in_diff += 1
                elif line.startswith('-'):
                    removes_in_diff += 1

            # means that at least one new line was added
            if adds_in_diff - removes_in_diff > 0:
                return True

        print_error(F'File {self.release_notes_path} is not formatted according to '
                    F'release notes standards.\nFix according to {release_notes_standard}')
        return False

    def is_valid_release_notes_structure(self):
        # type: () -> bool
        """Validates that the release notes written in the correct manner.

        one_line_release_notes_regex meaning:
            dont start with any of the characters in the first []
            starts with a letter or number
            ends with '.'

        multi_line_release_notes_regex meaning:
            starts with tab, then '-' ,then space
            ends with '.'

        Returns:
            bool. True if release notes structure valid, False otherwise

        """
        hyphen_release_notes_regex = r'- ?'
        one_line_release_notes_regex = r'[a-zA-Z0-9].*\.$'
        multi_line_release_notes_regex = r'(\t+| {2,4})- .*\.$|- ?$'

        release_notes_comments = self.release_notes.split('\n')
        print(release_notes_comments)

        if len(release_notes_comments) == 1:
            if not (re.match(hyphen_release_notes_regex, self.release_notes) or
                    re.match(one_line_release_notes_regex, self.release_notes)):
                print_error(F'File {self.release_notes_path} is not formatted according to '
                            F'release notes standards.\nFix according to {release_notes_standard}')
                return False

        elif len(release_notes_comments) == 2:
            if re.match(multi_line_release_notes_regex, release_notes_comments[0]) and \
                    release_notes_comments[1] == '':
                print_error(F'File {self.release_notes_path} is not formatted according to '
                            F'release notes standards.\nFix according to {release_notes_standard}')
                return False

        else:
            release_notes_comments = release_notes_comments[:-1]

            # if it's one line comment with list
            if re.match(one_line_release_notes_regex, release_notes_comments[0]):
                release_notes_comments = release_notes_comments[1:]

            for comment in release_notes_comments:
                if not re.match(multi_line_release_notes_regex, comment):
                    print_error(F'File {self.release_notes_path} is not formatted according to '
                                F'release notes standards.\nFix according to {release_notes_standard}')
                    return False

        return True

    def validate_file_release_notes(self):
        # type: () -> bool
        """Validate that the file has proper release notes when modified.

        Returns:
            bool. True if release notes file exists, False otherwise.
        """
        # checks that release notes file exists and contains text
        if not os.path.isfile(self.release_notes_path):
            print_error(F'File {self.file_path} is missing release notes, '
                        F'Please add it under {self.release_notes_path}')
            return False

        if self.release_notes is None:
            print_error(F'File {self.file_path} is missing release notes, '
                        F'Please add it under {self.release_notes_path}')
            return False

        return True

    def is_file_valid(self):
        # type: () -> bool
        """Checks if given file is valid.

        Return:
            bool. True if file's release notes are valid, False otherwise.
        """
        validations = [
            self.validate_file_release_notes(),
            self.is_valid_release_notes_structure(),
            self.is_release_notes_changed()
        ]

        return all(validations)
