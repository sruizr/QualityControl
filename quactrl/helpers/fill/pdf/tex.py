from .. import Filler as BaseFiller
import subprocess


class Filler(BaseFiller):
    def __init__(self , fs, template_path):
        "docstring"
        env_config = {
            'block_start_string': '\BLOCK{',
            'block_end_string': '}',
            'variable_start_string': '\VAR{',
            'variable_end_string': '}',
            'comment_start_string': '\#{',
            'comment_end_string': '}',
            'line_statement_prefix': '%%',
            'line_comment_prefix': '%#',
            'trim_blocks': True,
            'autoescape': False
        }

        super().__init__(fs, template_path=template_path,
                         env_config=env_config)

    def convert(self, filled_fn, run_many=1):
        """Converts filled tex file to pdf file
        """
        filled_syspath = self._temp_fs.getsyspath(filled_fn)
        output_directory = self._temp_fs.getsyspath('/')
        for _ in range(run_many):
            command = "pdflatex -output-directory {} {}".format(
                output_directory, filled_syspath
            )
            subprocess.check_call(command, shell=True)

        pdf_fn = filled_fn.replace('.tex', '.pdf')
        return super().convert(pdf_fn)
