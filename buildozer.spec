requirements = python3,kivy
title = ZSSK Zmeny
package.name = zsskzmeny
package.domain = org.zssk
source.dir =.
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.8
requirements = hostpython3==3.11.9,python3==3.11.9,kivy

orientation = portrait

[buildozer]
log_level = 2

[android]
android.archs = arm64-v8a
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.build_tools = 33.0.2
android.accept_sdk_license = True
p4a.branch = develop
p4a.source_dir =
android.permissions = INTERNET
