from girder.models.user import User
from girder.models.assetstore import Assetstore
from getpass import getpass
import os


def init_girder(username=None, password=None):
    api_root = os.environ.get('API_ROOT')
    user = User().findOne({'admin': True})
    assetstore = Assetstore().findOne()

    if user is None:
        if username is None:
            username = input('Admin username: ')
        if password is None:
            password = getpass('Admin password: ')
        user = User().createUser(
            username,
            password,
            'Admin',
            'User',
            'admin@noemail.nil',
            admin=True,
        )
    if assetstore is None:
        assetstore = Assetstore().createFilesystemAssetstore(
            'files', '/data',
        )
    if user is not None and assetstore is not None:
        print('Success. Initialization complete.')


if __name__ == '__main__':
    init_girder()
