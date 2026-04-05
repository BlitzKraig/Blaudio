from invoke import task
import os
import re
import shutil

@task
def start(c):
    c.run("python blaudio.py")

@task
def bump(c, version):
    """Bump the version number across all project files.

    Usage: invoke bump --version 0.1.0
    """
    parts = version.split('.')
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise SystemExit(f"Version must be X.Y.Z format, got: {version!r}")

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    v_str     = f'v{version}'                          # v0.1.0
    tuple_str = f'(0, {major}, {minor}, {patch})'     # (0, 0, 1, 0)

    def sub(path, pattern, replacement, flags=0):
        text = open(path, encoding='utf-8').read()
        new_text, n = re.subn(pattern, replacement, text, flags=flags)
        if n == 0:
            print(f"  WARNING: no match in {path!r} — pattern may need updating")
        else:
            open(path, 'w', encoding='utf-8').write(new_text)
            print(f"  {path}")

    print(f"Bumping to {version} ({v_str}, {tuple_str})")

    sub('api.py',
        r"(self\._version\s*=\s*')v[\d.]+(')",
        rf'\g<1>{v_str}\g<2>')

    sub('ui/web/js/state.js',
        r"(  version:\s*')v[\d.]+(')",
        rf'\g<1>{v_str}\g<2>')

    sub('version.txt',
        r'(filevers=)\([\d,\s]+\)',
        rf'\g<1>{tuple_str}')

    sub('version.txt',
        r'(prodvers=)\([\d,\s]+\)',
        rf'\g<1>{tuple_str}')

    sub('README.md',
        r'(\(currently )v[\d.]+(\))',
        rf'\g<1>{v_str}\g<2>')

    sub('README.md',
        r"(  version:\s*')v[\d.]+(')",
        rf'\g<1>{v_str}\g<2>')

    sub('README.md',
        r'(\*\*Version:\*\* )[\d.]+( \(early development\))',
        rf'\g<1>{version}\g<2>')

    print("Done.")


@task
def buildEXE(c):
    # Force full rebuild
    if os.path.exists("dist/"):
        shutil.rmtree("dist/")

    os.makedirs("dist/Arduino")
    c.run("pyinstaller blaudio.spec --clean")
    c.run("cp blaudio_config.json dist/")
    c.run("cp Arduino/Nano/BlaudioNano/* dist/Arduino/")
