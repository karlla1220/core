#!/bin/bash
# Builds only the x2t executable (and the static format libraries it links) from this tree, against the shared
# libraries of the ONLYOFFICE Document Server release it is based on. specDuck replaces only x2t in that release's
# FileConverter/bin; every .so stays the release's. Runs in ubuntu:22.04 (glibc 2.35), from the repository root.
set -euo pipefail
# Env: CXX_EXTRA (see build()), WORK (downloads and object files, kept between runs: a rerun rebuilds only what changed), JOBS, SKIP_APT=1.
# CI uses the defaults in ubuntu:22.04; on a developer machine it is the same script with WORK kept.
RELEASE=10.0.0 ICU=74_2
ARCH=$(dpkg --print-architecture)
case $ARCH in
  amd64) DEB_SHA256=c841776e56f4987d38516f5718d7b87b89263436178a03a4bee29fd748a11c20 ;;
  arm64) DEB_SHA256=ea27422f3f4749cead8dce7a738eb1f6950b0c42d441ba930f338eeb40f34a9f ;;
  *) echo "unsupported architecture $ARCH"; exit 1 ;;
esac
ROOT=$PWD; WORK=${WORK:-/tmp/x2t-build}; JOBS=${JOBS:-$(nproc)}
SUDO=; [ "$(id -u)" = 0 ] || SUDO=sudo
mkdir -p "$WORK"

if [ "${SKIP_APT:-0}" != 1 ]; then
  export DEBIAN_FRONTEND=noninteractive
  $SUDO apt-get update -q
  $SUDO apt-get install -y -q build-essential qtbase5-dev-tools qt5-qmake libboost-regex-dev libboost-filesystem-dev \
    libboost-date-time-dev curl ca-certificates dpkg-dev python3 file
fi

# The release's shared libraries, where qmake links them from.
BIN=$WORK/oo/var/www/onlyoffice/documentserver/server/FileConverter/bin
if [ ! -d "$BIN" ]; then
  curl -fsSL -o "$WORK/oo.deb" "https://github.com/ONLYOFFICE/DocumentServer/releases/download/v$RELEASE/onlyoffice-documentserver_$ARCH.deb"
  echo "$DEB_SHA256  $WORK/oo.deb" | sha256sum -c
  dpkg-deb -x "$WORK/oo.deb" "$WORK/oo" && rm "$WORK/oo.deb"
fi
mkdir -p build/lib/linux_64 Common/3dParty/icu/linux_64/build/include/unicode
cp -a "$BIN"/*.so build/lib/linux_64/
cp -a "$BIN"/libicu*.so.74 Common/3dParty/icu/linux_64/build/

# ICU 74 headers (symbols carry the major version, so they must match the release's libicuuc.so.74).
if [ ! -d "$WORK/icu" ]; then
  curl -fsSL "https://github.com/unicode-org/icu/releases/download/release-${ICU/_/-}/icu4c-${ICU}-src.tgz" | tar xz -C "$WORK"
fi
cp "$WORK"/icu/source/common/unicode/*.h "$WORK"/icu/source/i18n/unicode/*.h Common/3dParty/icu/linux_64/build/include/unicode/

# Boost from the distribution, where boost.pri looks: static archives only, so x2t needs no boost .so at run time
# (the release's bin has none).
LIBDIR=/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)
mkdir -p Common/3dParty/boost/build/linux_64/lib
ln -sfn /usr/include Common/3dParty/boost/build/linux_64/include
for l in regex system filesystem date_time; do  # boost_system is header-only from 1.69 and gone from newer distributions
  if [ -f "$LIBDIR/libboost_$l.a" ]; then cp "$LIBDIR/libboost_$l.a" Common/3dParty/boost/build/linux_64/lib/
  else ar rcs "Common/3dParty/boost/build/linux_64/lib/libboost_$l.a"; fi
done

# CXX_EXTRA: flags for every compile, through a compiler wrapper (qmake arguments with spaces do not reach the
# subprojects), e.g. on a newer gcc that no longer pulls in headers the tree forgets:
#   CXX_EXTRA="-include cfloat -include cstdint -include climits"
QARGS=(CONFIG+=release)
if [ -n "${CXX_EXTRA:-}" ]; then
  printf '#!/bin/sh\nexec g++ %s "$@"\n' "$CXX_EXTRA" > "$WORK/cxx" && chmod +x "$WORK/cxx"
  # precompiled headers off: their -include rule and the wrapper's do not mix (a PCH that is never built)
  # (-after: the projects set it themselves, after the command line's assignments)
  QARGS+=("QMAKE_CXX=$WORK/cxx" "QMAKE_LINK=$WORK/cxx" -after "CONFIG-=precompile_header")
fi
# Three levels below WORK: subprojects build at ../../../<their path>, which stays inside WORK.
build() { local d="$WORK/qb/$1/b/q"; mkdir -p "$d" && (cd "$d" && qmake -qt=qt5 "$ROOT/$2" "${QARGS[@]}" && make -j"$JOBS"); }
build cryptopp Common/3dParty/cryptopp/project/cryptopp.pro
# x2t's Makefile does not depend on the static libraries: drop it so a rebuilt library is linked in.
rm -f build/bin/linux_64/x2t
build x2t X2tConverter/build/Qt/X2tSLN.pro

X2T=$(find build/bin -name x2t -type f | head -1)
file "$X2T"
mkdir -p out && cp "$X2T" out/x2t
# Smoke test: every library it needs is in the release's bin.
rm -rf "$WORK/chk" && mkdir -p "$WORK/chk" && cp -a "$BIN"/. "$WORK/chk/" && cp out/x2t "$WORK/chk/x2t"
# Every library it needs is in the release's bin or the base system (libc, libm, libpthread, libdl, librt, ld-linux).
extra=$(LD_LIBRARY_PATH="$WORK/chk" ldd "$WORK/chk/x2t" | grep -v -e "=> $WORK/chk/" -e vdso -e ld-linux \
  -e "lib\(c\|m\|pthread\|dl\|rt\)\.so" || true)
if [ -n "$extra" ]; then echo "x2t needs libraries the release does not ship:"; echo "$extra"; exit 1; fi
objdump -T out/x2t | grep -o 'GLIBC_2\.[0-9]*' | sort -Vu | tail -1
