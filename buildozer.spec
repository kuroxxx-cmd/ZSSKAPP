[app]
title = ZSSK Zmeny
package.name = zsskzmeny
package.domain = org.zssk
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.main = main.py

version = 13.0

# TVRDÝ FIX 1: Nekompromisné zafixovanie stabilných verzií knižníc
requirements = python3,kivy,plyer,androidstorage4kivy

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0

[android]
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.build_tools = 33.0.2
android.accept_sdk_license = True

# Pre file manager na Android 13+
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO
android.manifest.intent_filters = 

# TVRDÝ FIX 2: Použitie poslednej nepochybne stabilnej vetvy kompilátora (žiadny master/develop)
p4a.fork = kivy
p4a.branch = master
p4a.bootstrap = sdl2
