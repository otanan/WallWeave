from setuptools import setup
APP = ['wallweave/wallweave.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleShortVersionString': '0.0.1',
        'LSUIElement': True,
    },
    'packages': ['rumps'],
}
setup(
    app=APP,
    name='WallWeave',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'], install_requires=['rumps']
)