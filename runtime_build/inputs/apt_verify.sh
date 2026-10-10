#!/bin/sh
# Candidate apt-install design, not target solver/install proof.
set -eu
trap 'for f in /tmp/apt-plan.txt /tmp/before-dpkg.tsv /reviewed-inputs/installed-dpkg.tsv; do if test -f "$f"; then printf "\nEVIDENCE %s\n" "$f"; cat "$f"; fi; done' EXIT
export LC_ALL=C DEBIAN_FRONTEND=noninteractive
cd /reviewed-inputs
# apt uses supplied hash-pinned signed-by keyring, no other configured sources.
apt-get update
# apt verifies signatures; additionally verify exact reviewed InRelease bytes.
check_release() {
  suite=$1 expected=$2
  set -- /var/lib/apt/lists/*_dists_${suite}_InRelease
  test "$#" -eq 1 && test -f "$1"
  echo "$expected  $1" | sha256sum -c -
}
check_release noble cdb2f31d809f589719a53c6ad15f255b27569c4059542ada282aaa21b8e164b0
check_release noble-updates 20c19c7b4265ac3fd6cfa3ef5b9a5bda93d0309655c87a42b23daa0c756bb570
check_release noble-security 802ae17a727fdaf3e561fe0d7620dd62ee6bd560299872a1a4b9a35199423294
dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' > /tmp/before-dpkg.tsv
set -- python3.12=3.12.3-1ubuntu0.17 python3.12-minimal=3.12.3-1ubuntu0.17 libpython3.12-minimal=3.12.3-1ubuntu0.17 libpython3.12-stdlib=3.12.3-1ubuntu0.17 python3.12-venv=3.12.3-1ubuntu0.17 gcc=4:13.2.0-7ubuntu1 libc6-dev=2.39-0ubuntu8.9 bubblewrap=0.9.0-1ubuntu0.3 ca-certificates=20260601~24.04.1 ubuntu-keyring=2023.11.28.1
apt-get --simulate --no-install-recommends install "$@" > /tmp/apt-plan.txt
if grep -q '^Remv ' /tmp/apt-plan.txt; then echo 'Removal refused' >&2;exit 1;fi
awk '/^Inst / { n=$2; sub(/:.*/,"",n); for(i=3;i<=NF;i++)if($i~/^\(/){v=$i;sub(/^\(/,"",v);print n "\t" v;break}}' /tmp/apt-plan.txt > /tmp/changes.tsv
while IFS="$(printf '\t')" read -r name version; do
  expected=$(awk -F '\t' -v n="$name" '$1==n {print $2}' deb-pins.tsv)
  test -n "$expected" || exit 1
  test "$version" = "$expected" || exit 1
  old=$(awk -F '\t' -v n="$name" '{sub(/:.*/,"",$1); if($1==n && $3=="installed") print $2}' /tmp/before-dpkg.tsv)
  if test -n "$old"; then dpkg --compare-versions "$version" ge "$old";fi
done < /tmp/changes.tsv
# Apt signed-index hash validation PLUS explicit artifact-control/version/hash check.
apt-get -y --download-only --no-install-recommends install "$@"
for deb in /var/cache/apt/archives/*.deb; do
  test -f "$deb" || continue
  name=$(dpkg-deb -f "$deb" Package); version=$(dpkg-deb -f "$deb" Version); arch=$(dpkg-deb -f "$deb" Architecture)
  pin=$(awk -F '\t' -v n="$name" '$1==n {print $0}' deb-pins.tsv);test -n "$pin"
  test "$version" = "$(printf '%s\n' "$pin" | cut -f2)" || exit 1
  test "$arch" = "$(printf '%s\n' "$pin" | cut -f3)" || exit 1
  test "$(wc -c < "$deb" | tr -d ' ')" = "$(printf '%s\n' "$pin" | cut -f4)"
  echo "$(printf '%s\n' "$pin" | cut -f5)  $deb" | sha256sum -c -
done
apt-get -y --no-download --no-install-recommends install "$@"
dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' > /reviewed-inputs/installed-dpkg.tsv
# Evidence emitted BEFORE strict gate, including failure cases.
cat /tmp/apt-plan.txt /tmp/before-dpkg.tsv installed-dpkg.tsv
# Strict entire installed-set gate, including preexisting base packages.
awk -F '\t' 'NR==FNR {v[$1]=$2;next} $3=="installed" {sub(/:.*/,"",$1);seen[$1]=1;if(!($1 in v)||v[$1]!=$2){print "outside exact ledger: " $1 > "/dev/stderr";bad=1}} END {for(n in v)if(!(n in seen)){print "missing post package: " n > "/dev/stderr";bad=1} exit bad}' post-install-pins.tsv installed-dpkg.tsv
dpkg-query -W
# Normal apt CA postinst has run. Switch apt TLS to generated system bundle.
test -s /etc/ssl/certs/ca-certificates.crt
printf 'Acquire::https::CaInfo "/etc/ssl/certs/ca-certificates.crt";\n' > /etc/apt/apt.conf.d/99runtime27b-ca
apt-get update
