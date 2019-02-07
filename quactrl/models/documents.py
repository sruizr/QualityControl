import subprocess
import core
from quactrl.helpers.docs import TexWriter


class Directory(core.Node):
    def __init__(self, key, name=None, description=None, parent=None):
        self.key = key
        self.name = name if name else key
        self.directories = []
        self.parent = parent

    def path(self):
        prefix = self.parent.path if self.parent else ''
        return '{}/{}'.format(prefix, self.name)


class Form(core.Resource):
    def __init__(self, key, name, description=None, pars=None):
        self.key = key
        self.name = name
        self.description = description
        self.pars = pars if pars else {}

    @property
    def type(self):
        return self.pars.get('type', '')

    @property
    def template_name(self):
        return '{}.{}'.format(self.name, self.type)


class Document(core.Item):
    def __init__(self, form, tracking, content):
        self.form = form
        self.tracking = tracking
        self.pars['content'] = content

    @property
    def content(self):
        return self.pars['content']

    @property
    def filename(self):
        return '{}_{}.{}'.format(self.form.name, self.tracking, self.form.type)

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
    def close(self):
        if hasattr(self, 'docs'):
            for doc in self.docs:
                self.fill_doc(doc)
        if hasattr(self, 'doc'):
            self.fill_doc
        super().close()

    def fill_doc(self, doc):
        doc_path = '{}/{}'.format(
            self.administration.destination.path, doc.filename
        )
        doc.add(1, self, self.administration.destination)
        self.documngr.fill(doc.content, doc.form.template_path,
                         doc_path)


class Print(Flow):
    def close(self):
        if hasattr(self, 'docs'):
            for doc in self.docs:
                self.print_doc(doc)
        if hasattr(self, 'doc'):
            self.print_doc
        super().close()

    def print_doc(self, doc):
        doc.add(1, self.administration.destination, self)

class Sign(Flow):
    def close(self):
        pass


class Export(Flow):
    pass


class Copy(Flow):
    pass
