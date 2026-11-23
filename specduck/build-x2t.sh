#!/bin/bash
# Builds only the x2t executable (and the static format libraries it links) from this tree, against the shared
# libraries of the ONLYOFFICE Document Server release it is based on. specDuck replaces only x2t in that release's
# FileConverter/bin; every .so stays the release's. Runs in ubuntu:22.04 (glibc 2.35), from the repository root.
set -euo pipefail
RELEASE=10.0.0 DEB_SHA256=c841776e56f4987d38516f5718d7b87b89263436178a03a4bee29fd748a11c20 ICU=74_2
ROOT=$PWD; JOBS=$(nproc)

export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q build-essential qtbase5-dev-tools qt5-qmake libboost-regex-dev libboost-filesystem-dev \
  libboost-system-dev libboost-date-time-dev curl ca-certificates dpkg-dev python3 file

# The release's shared libraries, where qmake links them from.
curl -fsSL -o /tmp/oo.deb "https://github.com/ONLYOFFICE/DocumentServer/releases/download/v$RELEASE/onlyoffice-documentserver_amd64.deb"
echo "$DEB_SHA256  /tmp/oo.deb" | sha256sum -c
dpkg-deb -x /tmp/oo.deb /tmp/oo
BIN=/tmp/oo/var/www/onlyoffice/documentserver/server/FileConverter/bin
mkdir -p build/lib/linux_64 Common/3dParty/icu/linux_64/build/include
cp -a "$BIN"/*.so build/lib/linux_64/
cp -a "$BIN"/libicu*.so.74 Common/3dParty/icu/linux_64/build/

# ICU 74 headers (symbols carry the major version, so they must match the release's libicuuc.so.74).
curl -fsSL -o /tmp/icu.tgz "https://github.com/unicode-org/icu/releases/download/release-${ICU/_/-}/icu4c-${ICU}-src.tgz"
tar xzf /tmp/icu.tgz -C /tmp
mkdir -p Common/3dParty/icu/linux_64/build/include/unicode
cp /tmp/icu/source/common/unicode/*.h /tmp/icu/source/i18n/unicode/*.h Common/3dParty/icu/linux_64/build/include/unicode/

# Boost from the distribution, where boost.pri looks: static archives only, so x2t needs no boost .so at run time
# (the release's bin has none).
mkdir -p Common/3dParty/boost/build/linux_64/lib
ln -sfn /usr/include Common/3dParty/boost/build/linux_64/include
cp /usr/lib/x86_64-linux-gnu/libboost_{regex,system,filesystem,date_time}.a Common/3dParty/boost/build/linux_64/lib/

build() { mkdir -p "/tmp/qb/$1" && (cd "/tmp/qb/$1" && qmake -qt=qt5 "$ROOT/$2" CONFIG+=release && make -j"$JOBS"); }
build cryptopp Common/3dParty/cryptopp/project/cryptopp.pro
build x2t X2tConverter/build/Qt/X2tSLN.pro

X2T=$(find build/bin -name x2t -type f | head -1)
file "$X2T"
mkdir -p out && cp "$X2T" out/x2t
# Smoke test: every library it needs is in the release's bin.
mkdir -p /tmp/chk && cp -a "$BIN"/. /tmp/chk/ && cp out/x2t /tmp/chk/x2t
# Every library it needs is in the release's bin or the base system (libc, libm, libpthread, libdl, librt, ld-linux).
extra=$(LD_LIBRARY_PATH=/tmp/chk ldd /tmp/chk/x2t | grep -v -e "=> /tmp/chk/" -e vdso -e ld-linux \
  -e "lib\(c\|m\|pthread\|dl\|rt\)\.so" || true)
if [ -n "$extra" ]; then echo "x2t needs libraries the release does not ship:"; echo "$extra"; exit 1; fi
objdump -T out/x2t | grep -o 'GLIBC_2\.[0-9]*' | sort -Vu | tail -1
