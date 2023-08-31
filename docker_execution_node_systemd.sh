#!/bin/bash

# Check if the nodename argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <nodename>"
    exit 1
fi

nodename="$1"

url="http://sbf:sbf@localhost:30080/api/v2/instances/$nodename/install_bundle/"

curl -k "$url" -o "/home/sbf/Downloads/$nodename.tar.gz"

tar xfz "/home/sbf/Downloads/$nodename.tar.gz" -C /home/sbf/Downloads/

docker run --rm --network kind --user root --privileged --name "$nodename" -d quay.io/fosterseth/public:execution_node_systemd

cd "/home/sbf/Downloads/${nodename}_install_bundle"

sed -i 's/<username>/awx/g' inventory.yml

ansible-playbook -c community.docker.docker -i inventory.yml install_receptor.yml

