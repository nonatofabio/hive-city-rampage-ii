"""Export local macOS and Android test builds, verifying their signatures.

Requires Godot 4.3 templates, Java 17, and Android SDK build-tools 34.0.0.
JAVA_HOME and ANDROID_HOME may override the locally configured toolchain.
"""
import configparser
import hashlib
import json
import os
from pathlib import Path
import plistlib
import sys
import tarfile
from toolchain import godot_binary
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'


def main():
    if sys.platform != 'darwin':
        raise SystemExit('make build requires macOS for app signing and packaging.')
    engine = godot_binary()
    sdk = Path(os.environ.get('ANDROID_HOME') or str(Path.home()/'Library/Android/sdk'))
    java = os.environ.get('JAVA_HOME')
    if not java or not (Path(java)/'bin/java').is_file():
        raise SystemExit('Set JAVA_HOME to Java 17 in Makefile.local before building.')
    signer = sdk/'build-tools/34.0.0/apksigner'
    if not signer.is_file():
        raise SystemExit('Install Android build-tools 34.0.0 and set ANDROID_HOME in Makefile.local.')
    env = dict(os.environ, JAVA_HOME=java, ANDROID_HOME=str(sdk))
    presets = configparser.ConfigParser(interpolation=None)
    presets.read(ROOT/'godot/export_presets.cfg')
    version = json.loads(presets['preset.0.options']['application/version'])
    if json.loads(presets['preset.1.options']['version/name']) != version:
        raise SystemExit('macOS and Android versions must match in export_presets.cfg.')
    app = BUILD / 'macos/Hive City Rampage II.app'
    apk = BUILD / f'android/Hive-City-Rampage-II-{version}.apk'
    linux = BUILD / 'linux/Hive-City-Rampage-II.x86_64'
    (BUILD/'logs').mkdir(parents=True,exist_ok=True)
    # Import new assets and register script classes on a fresh checkout before exporting.
    import_log = BUILD/'logs/import.log'
    with import_log.open('w') as stream:
        imported = subprocess.run([engine,'--headless','--editor','--path',str(ROOT/'godot'),'--import'],
                                  stdout=stream,stderr=subprocess.STDOUT,env=env,timeout=180)
    if imported.returncode or 'ERROR:' in import_log.read_text():
        raise SystemExit(f'Godot import failed; see {import_log}')
    for preset, flag, output in [('macOS','--export-release',app),('Android','--export-debug',apk),('Linux','--export-release',linux)]:
        output.parent.mkdir(parents=True,exist_ok=True)
        log = BUILD/'logs'/f'export-{preset}.log'
        with log.open('w') as stream:
            result = subprocess.run([engine,'--headless','--path',str(ROOT/'godot'),flag,preset,str(output)],
                                    stdout=stream,stderr=subprocess.STDOUT,env=env,timeout=180)
        text = log.read_text()
        if result.returncode or 'ERROR:' in text or 'APK is unsigned' in text or not output.exists():
            print(text[-5000:])
            raise SystemExit(f'{preset} export failed; see {log}')
        print(f'Exported {output}',flush=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
    signed = subprocess.run([str(signer),'verify','--verbose',str(apk)],env=env,text=True,
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
    (BUILD/'logs/android-signature.txt').write_text(signed.stdout)
    print(signed.stdout,flush=True)
    metadata = plistlib.loads((app/'Contents/Info.plist').read_bytes())
    binary = app/'Contents/MacOS'/metadata['CFBundleExecutable']
    print(subprocess.check_output(['file',str(binary)],text=True),flush=True)
    archive = BUILD/f'Hive-City-Rampage-II-{version}-macOS.zip'
    subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(app),str(archive)],check=True)
    linux.chmod(0o755)
    if linux.read_bytes()[:4] != b'\x7fELF':
        raise SystemExit('Linux export is not an ELF executable.')
    linux_notes = linux.parent/'README-Steam-Deck.txt'
    linux_notes.write_text((ROOT/'STEAM-DECK.md').read_text())
    linux_archive = BUILD/f'Hive-City-Rampage-II-{version}-Linux-SteamDeck.tar.gz'
    with tarfile.open(linux_archive,'w:gz') as bundle:
        bundle.add(linux,arcname='Hive-City-Rampage-II/Hive-City-Rampage-II.x86_64')
        bundle.add(linux_notes,arcname='Hive-City-Rampage-II/README-Steam-Deck.txt')
    manifest = {'version' :version,'engine':subprocess.check_output([engine,'--version'],text=True).strip(),'art_source_commit':'b9828a619a8e61b036e05c676d055580787e9dfb',
                'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'macos_signing':'ad-hoc, not notarized','android_signing':'local Android debug key',
                'artifacts':{str(p.relative_to(BUILD)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [archive,apk,linux_archive]}}
    (BUILD/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('BUILD PASS: macOS signature, universal binary, signed Android APK, Linux x86-64 ELF, archives and hashes',flush=True)


if __name__=='__main__':
    main()
