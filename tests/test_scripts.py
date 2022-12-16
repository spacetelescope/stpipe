import shutil

SCRIPTS = ['strun']


def test_scripts_in_path():
    for script in SCRIPTS:
        assert shutil.which(script) is not None, f'`{script}` not installed'
