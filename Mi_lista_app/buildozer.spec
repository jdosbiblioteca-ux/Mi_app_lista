[app]
title = Mi Lista de Compras
package.name = milistacompras
package.domain = org.milista
source.include_exts = py,png,jpg,kv,atlas,db
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,pillow,openssl,urllib3,idna,certifi,charset-normalizer,sqlite3
android.permissions = INTERNET
orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 1
