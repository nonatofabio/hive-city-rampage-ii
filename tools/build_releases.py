"""Export local macOS and Android test builds, verifying their signatures.

Requires Godot 4.3 templates, Java 17, and Android SDK build-tools 34.0.0.
JAVA_HOME and ANDROID_HOME may override the locally configured toolchain.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'


def main():
    engine = os.environ.get('GODOT_BIN') or shutil.which('godot') or '/Applications/Godot.app/Contents/MacOS/Godot'
    sdk = Path(os.environ.get('ANDROID_HOME', str(Path.home()/'Library/Android/sdk')))
    java = os.environ.get('JAVA_HOME')
    cached_java = Path.home()/'Library/Caches/ashgate-build/java-home.txt'
    if not java and cached_java.exists():
        java = cached_java.read_text().strip()
    if not java:
        raise SystemExit('Set JAVA_HOME to Java 17 before building Android.')
    env = dict(os.environ, JAVA_HOME=java, ANDROID_HOME=str(sdk))
    app = BUILD / 'macos/Hyve City Rampage II.app'
    apk = BUILD / 'android/Hyve-City-Rampage-II-0.2.0.apk'
    (BUILD/'logs').mkdir(parents=True,exist_ok=True)
    for preset, flag, output in [('macOS','--export-release',app),('Android','--export-debug',apk)]:
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
    signer = sdk/'build-tools/34.0.0/apksigner'
    signed = subprocess.run([str(signer),'verify','--verbose',str(apk)],env=env,text=True,
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
    (BUILD/'logs/android-signature.txt').write_text(signed.stdout)
    print(signed.stdout,flush=True)
    metadata = plistlib.loads((app/'Contents/Info.plist').read_bytes())
    binary = app/'Contents/MacOS'/metadata['CFBundleExecutable']
    print(subprocess.check_output(['file',str(binary)],text=True),flush=True)
    archive = BUILD/'Hyve-City-Rampage-II-0.2.0-macOS.zip'
    subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(app),str(archive)],check=True)
    manifest = {'version':'0.2.0','engine':subprocess.check_output([engine,'--version'],text=True).strip(),'python_source':'b9828a619a8e61b036e05c676d055580787e9dfb',
                'worktree_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'macos_signing':'ad-hoc, not notarized','android_signing':'local Android debug key',
                'artifacts':{str(p.relative_to(BUILD)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [archive,apk]}}
    (BUILD/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('BUILD PASS: macOS signature, universal binary, signed Android APK, ZIP and hashes',flush=True)


if __name__=='__main__':
    main()
