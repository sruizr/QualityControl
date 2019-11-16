import os.path
from smb.SMBConnection import SMBConnection
import logging


logger = logging.get_logger(__name__)


class Handler:
    def __init__(self, system_name, user, domain, password,
                 service_name, path=None):
        self.conn = SMBConnection(user, password, 'raspberry', system_name,
                                  domain)
        assert self.conn.connect(system_name)
        self.service_name = service_name
        self.path = path if path else '/'

    def upload_file(self, local_path, samba_path=''):
        file_name = os.path.basename(samba_path)
        if not file_name:  # if no filename it copies the local filename
            file_name = os.path.basename(local_path)
            samba_path = os.path.join(samba_path, file_name)

        samba_path = os.path.join(self.path, samba_path)
        with open(local_path, 'rb') as f:
            print(samba_path)
            self.conn.storeFile(self.service_name, samba_path, f)

    def download_file(self, samba_path, local_path=None):
        raise NotImplementedError

    def get_shared_link(self, samba_path):
        raise NotImplementedError
