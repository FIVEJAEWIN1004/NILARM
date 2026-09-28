#!/usr/bin/env bash
# PINKY, one time: let `nilarm` start the laptop /harvest server without any
# prompt. Rerun until everything says OK.
#   ./scripts/setup_remote_harvest.sh <laptop_user>@<laptop_host>   # first time
#   ./scripts/setup_remote_harvest.sh                                # re-check
# Stores only the address in <repo>/.nilarm_remote_env (git-ignored) and a
# dedicated key in ~/.ssh/nilarm_laptop_ed25519. No password is stored.
repo="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cfg="${repo}/.nilarm_remote_env"
key="$HOME/.ssh/nilarm_laptop_ed25519"

if [[ "$1" == *@* ]]; then
    printf 'NILARM_LAPTOP_USER=%q\nNILARM_LAPTOP_HOST=%q\n' "${1%@*}" "${1#*@}" >"${cfg}"
    echo "saved ${cfg}"
fi
[[ -f "${cfg}" ]] && source "${cfg}"
if [[ -z "${NILARM_LAPTOP_HOST}" || -z "${NILARM_LAPTOP_USER}" ]]; then
    echo "usage: $0 <laptop_user>@<laptop_host>   (e.g. on the laptop: whoami; hostname -I)" >&2
    exit 2
fi
target="${NILARM_LAPTOP_USER}@${NILARM_LAPTOP_HOST}"
echo "laptop: ${target}"

if [[ ! -f "${key}" ]]; then
    mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
    # No passphrase: nilarm must start unattended. The key only unlocks this laptop.
    ssh-keygen -q -t ed25519 -N '' -C "nilarm-pinky@$(hostname)" -f "${key}"
    echo "created ${key}"
fi
echo "Pinky public key: $(cat "${key}.pub")"

manual_steps() {
    cat <<EOF

Do these once, then rerun $0:
  1) laptop: sudo apt install openssh-server        (SSH server; once)
  2) laptop: ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub   (note fingerprint)
  3) Pinky:  ssh-copy-id -i ${key}.pub ${target}
     - answer 'yes' only if the fingerprint matches step 2
     - enter the laptop password once (it is not saved anywhere)
EOF
}

if ! ssh-keygen -F "${NILARM_LAPTOP_HOST}" >/dev/null 2>&1; then
    echo "NOT OK: ${NILARM_LAPTOP_HOST} is not in ~/.ssh/known_hosts yet"
    manual_steps
    exit 1
fi
echo "OK: laptop host key is known"

ssh_opts=(-o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=5
          -i "${key}" -o IdentitiesOnly=yes)
if ! ssh "${ssh_opts[@]}" "${target}" true; then
    echo "NOT OK: passwordless SSH to ${target} failed"
    manual_steps
    exit 1
fi
echo "OK: passwordless SSH"

remote="\$HOME/${NILARM_LAPTOP_REPO:-NILARM}/scripts/run_harvest_server.sh"
if ! ssh "${ssh_opts[@]}" "${target}" "bash \"${remote}\" check"; then
    echo "NOT OK: laptop harvest environment check failed (see above)"
    exit 1
fi
echo
echo "All OK. \`nilarm\` will start the laptop /harvest server when it is not running."
