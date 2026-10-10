#!/bin/sh
# Plan acquisition only. No package install, postinst, Python or application execution.
printf '%s\n' 'STAGE start'
set -eu
export LC_ALL=C DEBIAN_FRONTEND=noninteractive
cd /reviewed
sha256sum -c inputs.sha256
printf '%s\n' 'STAGE inputs-ok'
aptver=$(dpkg-query -W -f='${Version}' apt)
printf 'TOOL\tapt\t%s\n' "$aptver"
test "$aptver" = 2.8.3
dpkg-query -W -f='BASE\t${Package}\t${Version}\t${Architecture}\t${db:Status-Status}\n'
printf '%s\n' 'STAGE dpkg-ok'
# Extraction does not run package maintainer scripts.
dpkg-deb -x ca-certificates-bootstrap.deb /bootstrap-ca
LC_ALL=C find /bootstrap-ca/usr/share/ca-certificates/mozilla -type f -name '*.crt' | LC_ALL=C sort > /tmp/ca-list
test "$(wc -l < /tmp/ca-list)" -eq 121
while IFS= read -r p; do cat "$p"; done < /tmp/ca-list > /tmp/bootstrap-ca.pem
echo '9481fcd95f41b221f02f14d896535fe500bec539bc563c4cdca1acee483a8bdd  /tmp/bootstrap-ca.pem' | sha256sum -c -
printf '%s\n' 'STAGE ca-ok'
rm -f /etc/apt/sources.list
rm -rf /etc/apt/sources.list.d/*
mkdir -p /etc/apt/sources.list.d
cp apt.sources /etc/apt/sources.list.d/reviewed.sources
cp ubuntu-archive-keyring.gpg /usr/share/keyrings/runtime27b-ubuntu.gpg
mkdir -p /etc/apt/apt.conf.d
printf 'Acquire::https::CaInfo "/tmp/bootstrap-ca.pem";\nAcquire::Retries "0";\nAcquire::https::Timeout "30";\nAPT::Sandbox::User "root";\nDir::Cache::pkgcache "";\nDir::Cache::srcpkgcache "";\n' > /etc/apt/apt.conf.d/99reviewed
printf '%s\n' 'STAGE conf-ok'
apt-get update || { rc=$?; df -P /var/lib/apt/lists /var/cache/apt /tmp >&2; exit "$rc"; }
printf '%s\n' 'STAGE apt-update-ok'
check_release() {
 suite=$1 hash=$2
 set -- /var/lib/apt/lists/*_dists_${suite}_InRelease
 test "$#" -eq 1 && test -f "$1"
 echo "$hash  $1" | sha256sum -c -
 date=$(sed -n 's/^Date: //p' "$1")
 printf 'POCKET\t%s\t%s\n' "$suite" "$date"
}
check_release noble cdb2f31d809f589719a53c6ad15f255b27569c4059542ada282aaa21b8e164b0
check_release noble-updates 20c19c7b4265ac3fd6cfa3ef5b9a5bda93d0309655c87a42b23daa0c756bb570
check_release noble-security 802ae17a727fdaf3e561fe0d7620dd62ee6bd560299872a1a4b9a35199423294
set -- python3.12=3.12.3-1ubuntu0.17 python3.12-minimal=3.12.3-1ubuntu0.17 libpython3.12-minimal=3.12.3-1ubuntu0.17 libpython3.12-stdlib=3.12.3-1ubuntu0.17 python3.12-venv=3.12.3-1ubuntu0.17 gcc=4:13.2.0-7ubuntu1 libc6-dev=2.39-0ubuntu8.9 bubblewrap=0.9.0-1ubuntu0.3 ca-certificates=20260601~24.04.1 ubuntu-keyring=2023.11.28.1
printf '%s\n' 'STAGE plan-begin'
printf 'PLAN_BEGIN\n'
apt-get --simulate --no-install-recommends install "$@"
printf 'PLAN_END\n'
