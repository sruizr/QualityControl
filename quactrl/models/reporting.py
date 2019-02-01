import subprocess
from .core import Resource, Item
from quactrl.helpers.docs import TexWriter


class Form(Resource):
    def __init__(self, key, template, description=None, pars=None):
        self.key = key
        self.template = template
        self.description = description
        self.pars = pars if pars else {}

    def fill(self, tracking,  content):
        return Report(self, tracking, content)

    @property
    def writer(self):
        if not hasattr(self, '_writer'):
            self._writer = TexWriter(
                templates_dir=self.pars['templates_dir']
            )
            self._writer.set_template('{}.tex'.format(self.name))
        return self._writer


class Report(Item):
    def __init__(self, form, tracking, content):
        self.form = form
        self.tracking = tracking
        self.pars['content'] = content

    @property
    def content(self):
        return self.pars['content']

    def print_sheet(self, printer_name, pdf_file_path=None):
        """Prints to local printer using CUPS service, if there is no pdf_file, it creates a new one and returns it
        """
        if not pdf_file_path:
            pdf_file_path = self.export2pdf()

        command = 'lp -D {} {}'.format(printer_name, pdf_file_path)
        subprocess.check_call(command)

        return pdf_file_path

    def export2pdf(self, path=None, tex_file_path=None):
        """Exports to pdf and returns the file_path
        """
        if not tex_file_path:
            tex_file_path = self.export2tex(path)

        pdf_file_path = '{}.pdf'.format(tex_file_path[:-3])

        command = 'pdflatex {}'.format(tex_file_path)
        subprocess.check_call(command)

        return pdf_file_path

    def export2tex(self, path=None):
        return self.form.writer.fill(self.content, file_name=self.tracking,
                                     path=path)


class Administration(core.Path):
    pass


class Fill(Flow):
    pass


class Print(Flow):
    pass


class Sign(Flow):
    pass


class Export(Flow):
    pass


class Copy(Flow):
    pass
