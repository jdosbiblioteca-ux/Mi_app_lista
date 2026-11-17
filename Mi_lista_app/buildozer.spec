[app]

# (str) Title of your application
title = Mi Lista de Compras

# (str) Package name
package.name = milistacompras

# (str) Package domain (needed for android packaging)
package.domain = org.milista

# (str) Source files where the main file lives
source.dir = .

# (list) Source files to include (let it include python files and assets)
source.include_exts = py,png,jpg,kv,atlas,db

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,pillow,openssl,urllib3,idna,certifi,charset-normalizer,sqlite3

# (list) Permissions
android.permissions = INTERNET

# (str) Supported orientations
orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 1
