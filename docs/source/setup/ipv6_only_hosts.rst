***************
IPv6 only hosts
***************

TLDR;
=====

Technically, this is feasible for many applications. However, some dependencies are not ready for IPv6-only networks.
To provide a full experience, we "built" an IPv4 reverse proxy on another host that handles all IPv4 traffic and forwards it to the IPv6-only host. 
The IPv6 addresses are enforced through the `/etc/hosts` file on the IPv4 reverse proxy so that it can reach the IPv6 host. 
We need this for Matrix federation (and Matrix OIDC) because Synapse servers currently cannot reach IPv6-only hosts.

Since Docker heavily relies on IPv4, we need to tunnel IPv4 traffic through IPv4 to an IPv4 'exit node'.
WireGuard is a good solution for this because plain IPv4 tunneling through IPv6 is not well-supported. 
(We can force Docker to use IPv6 only, but many containers are not ready for IPv6-only networks, so this approach is currently not feasible.)

Overall, after two days of research and retries, we are sticking with this hybrid solution. 
The Libre Workspace Software itself is well-prepared for full IPv6 hosts, but it turns out that some other dependencies are not.

Challenges
==========

- Some sites and APIs are not reachable via IPv6 only. For such cases we can use a DNS64/NAT64 gateway to translate between IPv4 and IPv6 addresses.
- Docker does heavily rely on IPv4. But with the latest docker version and daemon settings we get the ability to integrate a container in a ipv6 only network.
- However some specific docker containers like e.g. the synaptic (matrix) container are not ready for IPv6 only networks. This is a problem for federation.


What works
==========

- The webserver (Caddy) supports IPv6 only hosts out of the box.
- The Libre Workspace Portal also has no problems with IPv6 only hosts.
- Nextcloud works with IPv6 only hosts, but the installation of Nextcloud Apps (which require the github API) is not possible without a DNS64/NAT64 gateway.
- Collabora works flawlessly with IPv6 only hosts.
- Also with Jitsi Meet no problems were discovered.
- Matrix federation currently does NOT work at IPv6 only hosts. Our solution: Configure a ipv4 reverseproxy at another host to provide a ipv4 for others in federation. And for ipv4 traffic from the 

Adaptions
=========

- Make sure the latest official docker version is installed.

.. code-block:: shell

    # Activate IPv6 in the docker daemon
    echo "{
    \"ipv6\": true,
    \"fixed-cidr-v6\": \"fd00:abcd:1::/64\",
    \"dns\": [\"2001:67c:2b0::4\", \"2001:67c:2b0::6\"]
    }" > /etc/docker/daemon.json

    systemctl restart docker


    # Adjust all upstream nameservers to a DNS64/NAT64 services. In this example we use the google public DNS64 addresses 2001:67c:2b0::4, 2001:67c:2b0::6
    chattr -i /etc/resolv.conf

    GLOBAL_IPV6_ADDRESS=$(ip -6 a | grep global | awk '{print $2}' | head -n 1)
    # Remove the /64 in the end
    GLOBAL_IPV6_ADDRESS=${GLOBAL_IPV6_ADDRESS%/*}

    echo "nameserver $GLOBAL_IPV6_ADDRESS" > /etc/resolv.conf
    echo "nameserver 2001:67c:2b0::4" >> /etc/resolv.conf
    echo "nameserver 2001:67c:2b0::6" >> /etc/resolv.conf
    chattr +i /etc/resolv.conf

    # Adjust in your netplan or /etc/network/interfaces the dns servers as well.
    # For example in /etc/netplan/01-netcfg.yaml
    # network:
    #   version: 2
    #   renderer: networkd
    #   ethernets:
    #     ens3:
    #       dhcp4: no
    #       dhcp6: no
    #       addresses:
    #         - 2001:18d::/64
    #  # We need this very local ipv4 for ldaps connection from synapse
    #         - 10.10.10.10/24
    #       routes:
    #         - to: default
    #         via: 2001:18d::1
    #       nameservers:
    #         addresses: [2001:67c:2b0::4, 2001:67c:2b0::6]


    # That matrix works:
    # We need to install matrix with ldap support, not with oidc support. As ldaps:// connection we are using: ldaps://10.10.10.10:636
    # This 10.10.10.10 address we assign to our host network interface as you see above in the netplan configuration.
    # Federation still doesnt work because other matrix servers are not able to reach us because of ipv6 only :(
