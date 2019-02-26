import quactrl.models.core as core
import quactrl.models.operations as op
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Directory(core.Node):
    def __init__(self, key, name=None, description=None, parent=None):
        self.key = key
        self.name = name if name else key
        self.directories = []
        self.parent = parent

    @property
    def path(self):
        prefix = self.parent.path if self.parent else ''
        return '{}/{}'.format(prefix, self.name)


class Form(core.Resource):
    def __init__(self, key, template_name, description=None):
        self.key = key
        self.description = description
        name, type = template_name.split('.')
        self.name = name
        self.pars = {'type': type}

    @property
    def type(self):
        return self.pars.get('type', '')

    @property
    def template_name(self):
        return '{}.{}'.format(self.name, self.type)


class Document(core.Item):
    def __init__(self, form, tracking, content, type='pdf'):
        self.form = form
        self.tracking = tracking
        self.pars = {}
        self.pars['content'] = content
        self.pars['type'] = type

    @property
    def content(self):
        return self.pars['content']

    @property
    def type(self):
        return self.pars['type']

    @property
    def filename(self):
        value = '{}_{}.{}'.format(self.form.name, self.tracking, self.type)
        logger.info('filename is : {}'.format(value))
        return value

    @property
    def file_path(self):
        for token in reversed(self.tokens):
            if type(token.flow) is Fill:
                path =  '{}/{}'.format(token.node.path, self.filename)
                logger.debug('Path for document is {}'.format(path))
                return path

    # def print_sheet(self, printer_name, pdf_file_path=None):
    #     """Prints to local printer using CUPS service, if there is no pdf_file, it creates a new one and returns it
    #     """
    #     if not pdf_file_path:
    #         pdf_file_path = self.export2pdf()

    #     command = 'lp -D {} {}'.format(printer_name, pdf_file_path)
    #     subprocess.check_call(command)

    #     return pdf_file_path

    # def export2pdf(self, path=None, tex_file_path=None):
    #     """Exports to pdf and returns the file_path
    #     """
    #     if not tex_file_path:
    #         tex_file_path = self.export2tex(path)

    #     pdf_file_path = '{}.pdf'.format(tex_file_path[:-3])

    #     command = 'pdflatex {}'.format(tex_file_path)
    #     subprocess.check_call(command)

    #     return pdf_file_path

    # def export2tex(self, path=None):
    #     return self.form.writer.fill(self.content, file_name=self.tracking,
    #                                  path=path)

class DocFlow(op.Action):
    def __init__(self, operation, step, update):
        self.update = update
        self.operation = operation
        self.step = step

    @property
    def docs(self):
        if not hasattr(self, '_docs'):
            self._docs = []

        return self._docs

    @property
    def destination(self):
        value = self.step.to_node if self.step.to_node else self.step.parent.to_node
        return value


class Fill(DocFlow):
    def add_document(self, form, tracking, content, type='pdf'):
        self.docs.append(
            Document(form, tracking, content, type)
        )

    def close(self):
        """Create the documents and upload to file_system
        """
        doc_service = self.operation.toolbox.doc_service()
        for doc in self.docs:
            destination = self.step.destination
            doc.update_qty(1, destination, self)
            doc_path = '{}/{}'.format(destination.path, doc.filename)
            doc_service.fill(doc.content, doc.form.template_name, doc_path)

        self.operation.docs.extend(self.docs)
        super().close()


class Print(DocFlow):
    """Print all documents inside its docs
    """
    def close(self):
        doc_service = self.operation.toolbox.doc_service()
        printer_name = self.step.method_pars['printer_name']
        for doc in self.docs:
                doc_service.print_to_cups_printer(
                    printer_name, doc.file_path
                )
                doc.update_qty(1, self.destination, self)
        super().close()


class FillStep(op.Step):
    def implement(self, operation):
        return Fill(operation, self, operation.update)


class PrintStep(op.Step):
    def implement(self, operation):
        return Print(operation, self, operation.update)


class SignStep(op.Step):
    def implement(self, operation):
        return Sign(operation, self, operation.update)
