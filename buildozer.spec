[app]
title = ZSSK Zmeny
package.name = zsskzmeny
package.domain = org.zssk

source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json

version = 0.2
requirements = python3,kivy==2.3.0,kivymd==1.1,pillow

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[android]
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.sdk = 34
android.ndk = 25b
android.accept_sdk_license = True
android.permissions = INTERNET

p4a.branch = develop
android.gradle_dependencies = 
android.add_src = 
android.meta_data = 
android.add_activites = 
