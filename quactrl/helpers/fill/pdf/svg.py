import subprocess
from .. import BaseFiller


class SvgFiller(BaseFiller):
    def convert(self, filled_fn):
        svg_sys_path = self.temp_fs.getsyspath(filled_fn)
        pdf_sys_path = svg_sys_path.replace('.svg', '.pdf')

        base = ['inkscape']
        svg_input = ['-f', svg_sys_path]
        pdf_output = ['-A', pdf_sys_path]
        command = base + svg_input + pdf_output
        subprocess.check_call(command)

        return super().convert(pdf_sys_path)
