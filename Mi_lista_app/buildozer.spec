[app]

# (str) Title of your application
title = Mi Lista de Compras

# (str) Package name
package.name = listadecompras

# (str) Package domain (needed for android packaging)
package.domain = org.compras

# (list) Source files to include (let it default to your project files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
# Omitimos versiones experimentales y fijamos Kivy/KivyMD estables con Python 3.10
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,urllib3,idna,certifi,charset-normalizer

# (str) Supported orientations
orientation = portrait

# (list) The orientation can be 'landscape', 'sensor' or 'portrait'
#fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support
android.min_api = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK version to use (Optional, leave blank to auto-download)
# android.sdk = 30

# (str) python-for-android branch
# Forzamos una rama estable compatible con Python 3.10
p4a.branch = master
