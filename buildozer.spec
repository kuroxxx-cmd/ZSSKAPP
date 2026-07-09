name: Build APK v8
on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4

      - name: Set up Java 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          sudo apt update
          sudo apt install -y git zip unzip autoconf libtool pkg-config zlib1g-dev libncurses5-dev cmake libffi-dev libssl-dev libltdl-dev
          pip install --upgrade pip
          pip install buildozer==1.5.0 cython==0.29.36 virtualenv

      - name: Build APK
        run: yes | buildozer -v android debug
        env:
          P4A_PYTHON_VERSION: "3.11"

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: ZSSK-APK-v8
          path: bin/*.apk
          retention-days: 14
