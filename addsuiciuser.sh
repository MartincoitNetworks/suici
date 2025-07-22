#/usr/bin/bash
# add a user to a SuiCI performance node
# gives user access to iftop via sudo
# will prompt for ssh keys if necessary

STUDARUS_KEYS="`cat <<'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIUMSlP1az/bgDKTJQgdf/QERUOC3sjVO8GjRbbK9m7q studarus-scionsui
EOF
`"

# Mysten Production Engineering
PE_KEYS="`cat <<'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILAVYnKYofNULBzpMk8jnxLExvJZXWcs8lQGlIzAJFin chris.gorham@mystenlabs.com
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINd+Ss33L4TDDiLseBVw7t+Ofy3FyaeLyCHWGzXgbV1p pe@mystenlabs.com
EOF
`"

NODEINFRA_KEYS="`cat <<'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICpwkfjKl225Da/01eZOqbv4AbiAHjEC6xQlBt02fEYi dawoon.han@mirny.io
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPCKFmYt6BMoIN9zPYUzlcesAltQywn1VCaxvIYBRPjV ys@mirny.io
EOF
`"

ARTIFACT_KEYS="`cat <<'EOF'
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCQezIyoQ/3OvILBD4HZg5SVlyEmmHc+Vu7HjTcHFXus95nwvs2Ng7quRPGM85gCsZ506i4OOJQifPV/hOTtmwdNsbCVe/MiYEByyx5NFzIZR6QBfMyYJVqKafqbVc8mDup14kdUnyMNuEPAaOpp5Bx0H46VUa2CZ/O5ZL/Sv
ufIAtleFW4hKM6oeax3lcniD0wDsnXF1z10HwtTONpd04zPiBhQaOgRS+H4YOAxNNfnQd72ryoFwgVW0RY8oYbGJ8PSdEve5wlXua+HG4G7dkGbi3KRP3HFT5yvMe8JbZvF1u3/M34PulkWrJ1InvHqGuNR6zGDTlkZFH9E0+IfUT2pEQog0SnthruegyM1ZJQ65Aki4AFfKpt
qVLxRVeps3wy3ych6Ax0/eKjBErnevLLBIm0pRiNBoYqiJ24u+i0nnDJhr7CjtweAW+v/vPhJMKmLxkCKQZJg6W4K+O+d8CtI+LZJzmF158KVG9Ln+RnOUcUdzaGG75bVK57UGOrmVc= dlee
EOF
`"

RUBYNODES_KEYS="`cat <<'EOF'
ecdsa-sha2-nistp521 AAAAE2VjZHNhLXNoYTItbmlzdHA1MjEAAAAIbmlzdHA1MjEAAACFBAE7K01SbmoWYK4ffK6beNjQ9alqjVPk5ppeCtpkEz0vH69j7cwnUKi864S4yvYvq3louADJQ5supWMu/fE+GLxkXAExIA5RAEgh5Ge/v/1Hy0Qk2MXaya8wKL8947PVobWW0Nb/2XbNdJNIcr4kbSty73+E2izRY/9hKpTQrXvDtkBacQ==
EOF
`"

USER=$1

if [ -z $USER ]; then
  echo "usage: $0 <username>"
  exit -1
fi

adduser $USER

HOME="$(getent passwd $USER | awk -F ':' '{print $6}')"
mkdir $HOME/.ssh
touch $HOME/.ssh/authorized_keys
chown $USER:$USER $HOME/.ssh/
chown $USER:$USER $HOME/.ssh/authorized_keys
chmod 700 $HOME/.ssh/
chmod 600 $HOME/.ssh/authorized_keys

apt install iftop -y

cat > /etc/sudoers.d/90-$USER <<EOF
$USER ALL=NOPASSWD: /usr/sbin/iftop
EOF

superuser=false

case $USER in
  studarus)
    echo $STUDARUS_KEYS >> $HOME/.ssh/authorized_keys
    superuser=true
    ;;
  pe)
    echo $PE_KEYS >> $HOME/.ssh/authorized_keys
    superuser=true
    ;;
  nodeinfra)
    echo $NODEINFRA_KEYS >> $HOME/.ssh/authorized_keys
    superuser=false
    ;;
  artifact)
    echo $ARTIFACT_KEYS >> $HOME/.ssh/authorized_keys
    superuser=false
    ;;
  rubynodes)
    superuser=false
    echo $RUBYNODES_KEYS >> $HOME/.ssh/authorized_keys
    ;;
  *)
    echo -n "enter the authorized keys ending with ctrl-d:"
    superuser=0
    cat - > $HOME/.ssh/authorized_keys
esac

if [ "$superuser" = true ] ; then
  cat > /etc/sudoers.d/90-$USER <<EOF
$USER ALL=(ALL) NOPASSWD:ALL
  EOF
fi

