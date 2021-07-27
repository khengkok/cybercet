## Default route problem for Kali 2021 image

As we have a 2nd interface which is in the private network, when it was added to the instance, the default route change to private interface, that is eth1 (e.g. 10.2.1.X). 

The following is an *ugly* fix for this problem: 

add the following line in the /etc/network/interfaces file: 

```sh
auto eth1
iface eth1 inet dhcp
    post-up ip route replace default via 10.2.0.1
```
