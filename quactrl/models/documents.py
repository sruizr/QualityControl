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


class Fill(Flow):
    def __init__(self, operation, step, update):
        self.update = update
        self.operation = operation
        self.step = step
        self.docs = []


    def execute(self):
        if (self.status != 'started'):
            raise Exception('step should be started before executing')

        self.step.method(self, **self.step.method_pars)  # method loads doc_tracking and doc_content
        form = self.step.out_resources[0]
        self.doc = form.create(self.doc_tracking, self.doc_content)
        dir_path = self.destination.path

        doc_path = '{}/{}.pdf'.format(self.step.destination.path,
                                         self.doc.filename)
        self.doc_service.fill(doc.content, form.template, doc_path)

        self.status = 'done'

    def close(self):
        self.doc.add(1, self.step.destination, self)
        if not hasattr('docs', self.operation):
            self.operation.docs = []

        self.operation.docs.append(self.doc)

        super().close()


class Print(Flow):
    def __init__(self, operation, step, update=None):
        self.update = update
        self.operation = operation
        self.step =step
        self.docs = []

    def execute(self):
        super().execute()
        printer_name = self.method_pars['printer_name']
        pattern = self.method_pars.get('pattern', '')
        self.docs = []
        if hasattr(self.operation, 'docs'):
            for doc in self.operation.docs:
                if pattern in doc.tracking:
                    self.docu_service.print_to_cups_printer(
                        printer_name, doc.file_path
                    )
                self.docs.append(doc)

    def close(self):
        for doc in self.docs:
            doc.add(1, self.operation.destination, self)
        super().close()


class Sign(Flow):
    def close(self):
        pass


class Export(Flow):
    pass


class Copy(Flow):
    pass


class FillStep(core.Path):
    def implement(self, operation):
        return Fill(operation, self, operation.update)


class PrintStep(core.Path):
    def implement(self, operation):
        return Print(operation, self, operation.update)


class SignStep(core.Path):
    def implement(self, operation):
        return Sign(operation, self, operation.update)
