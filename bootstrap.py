"""Generate native runners using your installed stable Flutter SDK."""
import pathlib, subprocess, tempfile, shutil
root=pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as folder:
    seed=pathlib.Path(folder)/'runner'
    subprocess.run(['flutter','create','--platforms=android,ios','--org','com.rafad','--project-name','rafad_trend',str(seed)],check=True)
    for name in ('android','ios','.metadata'):
        dest=root/name
        if not dest.exists():
            if (seed/name).is_dir(): shutil.copytree(seed/name,dest)
            else: shutil.copy2(seed/name,dest)
manifest=root/'android/app/src/main/AndroidManifest.xml'
source=manifest.read_text()
if 'android.permission.INTERNET' not in source:
    source=source.replace('<application','<uses-permission android:name="android.permission.INTERNET"/>\n    <application',1)
source=source.replace('android:label="rafad_trend"','android:label="رفد ترند"')
manifest.write_text(source)
plist=root/'ios/Runner/Info.plist'
plist.write_text(plist.read_text().replace('<string>Rafad Trend</string>','<string>رفد ترند</string>'))
subprocess.run(['flutter','pub','get'],cwd=root,check=True)
print('Native runners prepared. Run flutter analyze, then flutter build apk --debug.')
