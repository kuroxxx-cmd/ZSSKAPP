[app]
title = ZSSK Zmeny
package.name = zsskzmeny
package.domain = org.zssk

source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json

version = 0.2
requirements = python3,kivy==2.3.0

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
p4a.branch = develop
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE
