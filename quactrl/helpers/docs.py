import os.path
import shutil
import tempfile
import jinja2


class TexWriter:
    def __init__(self, templates_dir, out_dir=None):
        self._temp_dir = tempfile.mkstemp()
        self.out_dir = out_dir

    def set_template(self, template_name):
        template_name = '{}.tex'.format(template_name)
        self.template = self.jinja.get_template(template_name)

    def fill(self, content, file_name=None):
        tex_content = self.template.render(content)

        if not file_name:
            return tex_content

        directory = self.out_dir if out_dir else self._temp_dir
        file_name = os.join(directory, file_name)
        with open(file_name, 'w') as f:
            f.write(tex_content)

        return file_name

    def __del__(self):
        shutil.rmtree(self.temporary_dir)


class DocSigner:
    pass


class DocPrinter:
    pass
