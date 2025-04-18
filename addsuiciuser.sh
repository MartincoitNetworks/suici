# add a user to a SuiCI performance node

USER=$1

if [ -z $USER ]; then
  echo "usage: $0 <username>"
  exit -1
fi

adduser $USER
mkdir ~$USER/.ssh
touch ~$USER/.ssh/authorized_keys
chown $USER:$USER ~$USER/.ssh/
chown $USER:$USER ~$USER/.ssh/authorized_keys
chmod 700 ~$USER/.ssh/
chmod 600 ~$USER/.ssh/authorized_keys
cat > /etc/sudoers.d/90-$USER <<EOF
$USER ALL=NOPASSWD: /usr/sbin/iftop
EOF
echo "enter the authorized keys ending with ctrl-d"
cat - > ~$USER/.ssh/authorized_keys
