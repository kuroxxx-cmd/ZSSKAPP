[app]
title = ZSSK Zmeny
package.name = zsskzmeny
package.domain = org.zssk

source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json,ttf
source.main = main.py

version = 0.6
requirements = python3,kivy,pyjnius,android

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0

[android]
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.build_tools = 33.0.2
android.accept_sdk_license = True
p4a.branch = master
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
