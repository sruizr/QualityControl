import uuid
import fs.copy
import fs.path
from fs.tempfs import TempFS
from jinja2.loaders import BaseLoader, TemplateNotFound
from jinja2 import Environment


class FSLoader(BaseLoader):
    """Loader for FileSystem object (PyFileSystem interface)
    """
    def __init__(self, fs):
        "docstring"
        self.fs = fs

    def get_source(self, environment, template_path):
        if not self.fs.exists(template_path):
            raise TemplateNotFound(template_path)

        with self.fs.open(template_path, 'r') as f:
            source = f.read()

        return source, template_path, lambda: True


class Filler:
    """Filler helper to inherits depending of text outut
    """
    def __init__(self, fs,  env_config=None, template_path=None):
        env_config = env_config if env_config else {}
        template_fs = (fs if template_path is None
                       else fs.opendir(template_path))
        self.engine = Environment(loader=FSLoader(template_fs),
                                  **env_config)

        self._temp_fs = TempFS()

    def fill(self, data, template_path):
        """Fill data on template and return a temporary file path
        """
        template = self.engine.get_template(template_path)
        text_content = template.render(**data)

        template_ext = fs.path.basename(template_path).split('.')[-1]
        filled_fn = '{}.{}'.format(str(uuid.uuid4()), template_ext)

        with self._temp_fs.open(filled_fn, 'w') as f:
            f.write(text_content)

        return self.convert(filled_fn)

    def convert(self, filled_fn):
        # Default is to return
        with self._temp_fs.openbin(filled_fn, 'r') as f:
            binary = f.read()
        return binary

    def __del__(self):
        self._temp_fs.close()
