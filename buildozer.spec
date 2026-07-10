[app]
title = ZSSK Zmeny
package.name = zsskzmeny
package.domain = org.zssk
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.main = main.py

version = 8.0
requirements = python3,kivy

# Podpora mobil + tablet, obe orientácie, ale default portrait
orientation = sensor
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0

[android]
# Kompatibilita max. zariadení
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.build_tools = 33.0.2
android.accept_sdk_license = True

p4a.fork = kivy
p4a.branch = master
p4a.bootstrap = sdl2

# Android 13+ bez WRITE_EXTERNAL_STORAGE, všetko ide do user_data_dir
android.permissions = INTERNET
android.allow_backup = True
# Pre tablety - povoliť veľké obrazovky
android.features = android.hardware.touchscreen
android.manifest.intent_filters = 
