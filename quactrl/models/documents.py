import quactrl.models.core as core
import quactrl.models.operations as op
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Directory(core.Node):
    def __init__(self, key, name, description=None, parent=None):
        self.key = key
        self.name = name if name else key
        self.directories = []
        self.parent = parent
        if parent:
            parent.directories.append(self)

        self._fs = None

    def set_root_fs(self, fs):
        parent = self
        while parent.parent:
            parent = parent.parent

        parent.fs = fs.opendir('/{}'.format(parent.name))

    @property
    def fs(self):
        if self._fs is None:
            if self.parent is None:
                return
            parent_fs = self.parent.fs
            if self.parent.fs is None:
                return
            self._fs = parent_fs.opendir('/{}'.format(self.name))
        return self._fs

    @fs.setter
    def fs(self, value):
        self._fs = value

    @property
    def get_sys_path(self):
        return self._fs.getsyspath('/')

    def save(self, doc, task):
        logger.debug('Saving document on directory')
        if not doc._bin:
            Exception('There is no content on doc to store')
        with self.fs.openbin(doc.filename, 'w') as f:
            f.write(doc._bin)
        doc.clear()
        doc.update_qty(1, self, task)

    def load(self, doc):
        if self not in doc.stocks:
            raise FileNotFoundError
        with self.fs.openbin(self.filename, 'r') as f:
            doc.write(f.read())

    def rename(self, old_filename, new_filename):
        self.fs.move(old_filename, new_filename)

    def trash(self, doc, task):
        self.fs.remove(doc.filename)
        doc.clear(self, task)


class Form(core.Resource):
    def __init__(self, key, name, description=None, pars=None):
        self.key = key
        self.description = description
        self.name = name
        self.pars = {}
        if pars:
            self.pars.update(pars)

    @property
    def template_name(self):
        return '{}.{}'.format(self.key, self.pars['in_type'])

    def fill(self, filler, tracking, content):
        document = Document(self, tracking, content)
        document.write(
            filler.fill(document.content, self.template_name)
        )
        return document


class Document(core.Item):
    def __init__(self, form, tracking, content, type='pdf'):
        super().__init__()
        self.form = form
        self.tracking = tracking
        self.pars = {}
        self.pars['content'] = content
        self._bin = b''

    @property
    def content(self):
        return self.pars['content']

    @property
    def type(self):
        return self.form.pars['type']

    @property
    def filename(self):
        if 'filename' not in self.pars:
            self.pars['filename'] = '{}.{}'.format(
                self.tracking, self.form.pars['out_type']
            )
        return self.pars['filename']

    @filename.setter
    def filename(self, value):
        old_filename = self.pars.get('filename')
        self.pars['filename'] = value
        if old_filename:
            for directory in self.stocks.keys():
                directory.rename(old_filename, value)

    def get_sys_path(self):
        paths = []
        for directory in self.stocks.keys():
            paths.append(directory.fs.getsyspath(self.filename))
        return paths

    def read(self):
        if self._bin is None:
            for directory in self.stocks:
                directory.load(self)
        return self._bin

    def write(self, binary):
        self._bin = binary

    def clear(self):
        self._bin = None


class AdminTask(op.Action):
    """ Flow of documents. It can be:
    1. Document creation, it includes copy
    2. Document printing
    3. Document removing
    """

    @property
    def docs(self):
        if not hasattr(self, '_docs'):
            self._docs = []

        return self._docs

    def close(self):
        for doc in self.docs:
            logger.debug('Hay documentos a enviar a {}'.format(self.destination))
            if type(self.destination) is Directory:
                logger.debug('intentado salvar')
                if self.destination.fs is None:
                    self.destination.set_root_fs(self.toolbox.fs)

                self.destination.save(doc, self)
            self.operation.docs.append(doc)
        super().close()

    @property
    def destination(self):
        return self.step.destination


class AdminStep(op.Step):
    def implement(self, operation):
        return AdminTask(operation, self, operation.update)
