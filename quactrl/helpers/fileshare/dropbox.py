import os.path
import dropbox
import logging


logger = logging.get_logger(__name__)


class Handler:
    def __init__(self, token, path=None):
        "docstring"
        self.token = token
        self.path = path if path else '/'
        self.dbx = dropbox.Dropbox(token)

    def upload_file(self, local_filename, dropbox_path=None, overwrite=False):
        """Uploads a file on dropbox returning its path on dropbox
        """
        dropbox_path = dropbox_path if dropbox_path else ''
        filename = os.path.basename(dropbox_path)
        if not filename:
            filename = os.path.basename(local_filename)
            dropbox_path = os.path.join(dropbox_path, filename)

        dropbox_path = os.path.join(self.path, dropbox_path)

        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        with open(local_filename, 'rb') as f:
            data = f.read()

        try:
            self.dbx.files_upload(
                data, dropbox_path, mode)
        except dropbox.exceptions.ApiError as err:
            logging.exception(err)

        return dropbox_path

    def download_file(self, dropbox_path, local_path=None):
        raise NotImplementedError()

    def get_shared_link(self, dropbox_path):
        return self.dbx.sharing_create_shared_link(dropbox_path).url
