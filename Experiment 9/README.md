# Experiment 9: IPsec VPN in Tunnel Mode with strongSwan

## Aim
To configure an IPsec VPN in tunnel mode between two Kali Linux gateways using strongSwan IKEv2 and analyze the protected traffic in Wireshark.

## Theory
IPsec provides confidentiality and integrity between network gateways. In tunnel mode, the complete original IP packet is encapsulated in a new IP header. IKEv2 establishes an IKE Security Association (SA) and authenticates the gateways. The resulting CHILD_SA uses ESP to encrypt and protect the actual data traffic.

In this experiment:
- Gateway A used outer address `192.168.188.129` and inner address `10.10.1.1/32`.
- Gateway B used outer address `192.168.188.135` and inner address `10.20.1.1/32`.
- The protected traffic was carried between `10.10.1.1/32` and `10.20.1.1/32`.
- strongSwan used IKEv2 with a shared pre-shared key (PSK).
- ESP with AES-GCM-256 was used for the CHILD_SA.

## Tools Used
- Two Kali Linux virtual machines
- strongSwan / charon-systemd / swanctl
- Linux XFRM networking tools
- tcpdump
- Wireshark
- VMware virtual networking

## Methodology

### 1. Address and connectivity verification
The outer interface and IP address were identified on both gateways. Gateway A and Gateway B were checked for direct reachability with `ping` and `ip route get` before configuring the tunnel.

### 2. strongSwan installation and service verification
strongSwan and supporting tools were installed on both gateways:

```bash
sudo apt update
sudo apt install -y charon-systemd strongswan-swanctl tcpdump
sudo systemctl enable --now strongswan
```

The service and daemon were verified with:

```bash
sudo systemctl status strongswan --no-pager
sudo swanctl --version
sudo swanctl --version --daemon
```

The evidence showed strongSwan `6.1.0` running with the charon-systemd daemon.

### 3. Protected network configuration
A loopback address was assigned on each gateway:

```bash
# Gateway A
sudo ip address add 10.10.1.1/32 dev lo

# Gateway B
sudo ip address add 10.20.1.1/32 dev lo
```

The firewall rules were checked with `sudo nft list ruleset` to ensure IKE and ESP traffic were not blocked.

### 4. strongSwan IKEv2 configuration
The gateways were configured with mirrored traffic selectors:

| Field | Gateway A | Gateway B |
|---|---|---|
| Local address | `192.168.188.129` | `192.168.188.135` |
| Remote address | `192.168.188.135` | `192.168.188.129` |
| IKE identity | `gw-a` | `gw-b` |
| Local traffic selector | `10.10.1.1/32` | `10.20.1.1/32` |
| Remote traffic selector | `10.20.1.1/32` | `10.10.1.1/32` |

The IKE proposals used AES-GCM-256, SHA-256 PRF, and MODP3072. The CHILD_SA used ESP with AES-GCM-256. The PSK was kept secret and was not included in the repository or screenshots.

The configuration was loaded on both gateways:

```bash
sudo swanctl --load-all
sudo swanctl --list-conns 2>/dev/null
```

### 5. Tunnel initiation
A packet capture was started on Gateway A before initiating the tunnel:

```bash
sudo tcpdump -ni eth0 -w exp9-ipsec.pcap \
  'udp port 500 or udp port 4500 or proto 50 or proto 51'
```

The tunnel was initiated from Gateway A:

```bash
sudo swanctl --initiate --child lab-net 2>/dev/null
```

The IKE SA and CHILD SA were established successfully.

### 6. Security Association and XFRM verification
Both gateways were inspected with:

```bash
sudo swanctl --list-sas 2>/dev/null
sudo ip xfrm state
sudo ip xfrm policy
```

The Security Associations showed IKEv2 established and an installed tunnel-mode CHILD_SA using ESP/AES-GCM-256.

### 7. Protected traffic test
Gateway A and Gateway B were used to send ping traffic with their loopback addresses as the source:

```bash
# Gateway A
ping -I 10.10.1.1 -c 4 10.20.1.1

# Gateway B
ping -I 10.20.1.1 -c 4 10.10.1.1
```

The counters in `swanctl --list-sas` were checked again to confirm that traffic increased the XFRM packet and byte counters.

### 8. Packet analysis
The capture was stopped and opened in Wireshark. The following display filter was used:

```text
isakmp || esp || ah || udp.port == 4500
```

The capture showed IKE_SA_INIT, IKE_AUTH, and ESP traffic between the two gateway addresses. NAT-T/UDP 4500 was used when the environment detected NAT. ESP protected the inner ICMP payload, while only outer gateway addresses and ESP metadata remained visible to the observer.

## Improvements Made During the Experiment

The following improvements were applied while completing the experiment to make the configuration reliable and easier to verify:

- Added loopback `/32` addresses (`10.10.1.1` on Gateway A and `10.20.1.1` on Gateway B) so that protected traffic had fixed source and destination addresses.
- Used mirrored traffic selectors and matching identities on both gateways to ensure that inbound and outbound policies were consistent.
- Verified direct Gateway A-to-Gateway B connectivity and inspected the firewall rules before tunnel initiation.
- Enabled and checked the `strongswan` service with `charon-systemd`, and confirmed the strongSwan/charon version before configuration.
- Used `2>/dev/null` for `swanctl` verification commands to hide harmless local CLI plugin warnings while retaining the daemon's real status output.
- Reloaded all connections with `sudo swanctl --load-all` after configuration changes and checked the loaded connection on both gateways.
- Captured UDP ports 500 and 4500 plus ESP/AH protocols so IKEv2 negotiation and NAT-T traffic were recorded along with the protected ESP packets.
- Bound ping traffic to the loopback source addresses and rechecked Security Association counters, XFRM states, and XFRM policies to prove that traffic passed through the tunnel.
- Added cleanup steps to terminate the CHILD_SA and remove the temporary loopback addresses after the experiment.

## Improvements

The lab can be extended beyond the completed test in the following ways:

- Replace the shared PSK with certificate-based authentication to avoid distributing one shared secret to both gateways.
- Use separate private LAN subnets behind each gateway instead of loopback `/32` addresses to model a site-to-site VPN more realistically.
- Apply explicit firewall rules that allow only the required IKE and ESP traffic, including UDP 4500 when NAT-T is in use.
- Test tunnel recovery by restarting the strongSwan service or briefly interrupting connectivity, then verify that the SAs are re-established.
- Record packet and byte counters before and after larger test transfers, and compare the results with the Wireshark capture to document tunnel behavior.
- Save the final connection configuration securely and verify service startup and tunnel behavior after reboot; keep secrets out of the repository and screenshots.

## Screenshots

The screenshots below are arranged in the order of the experiment. Each image is included once.

### 1. strongSwan installation and service status

This shows strongSwan and tcpdump being installed, with the strongSwan service active and running.

![strongSwan installation and service status](Screenshots/Screenshot%202026-11-18%20101605.png)

### 2. Addressing and reachability test

The Gateway B outer interface is assigned `192.168.188.135/24`, and the loopback address `10.20.1.1/32` is configured as the protected network behind it. Gateway A reaches Gateway B successfully, confirming basic connectivity before tunnel configuration.

![Addressing and gateway reachability](Screenshots/Screenshot%202026-11-18%20103143.png)

### 3. Configuration loaded successfully

The swanctl configuration is loaded, and the `lab-vpn` IKEv2 connection is reported as successfully loaded.

![strongSwan configuration loaded](Screenshots/Screenshot%202026-11-18%20103919.png)

### 4. Gateway A connection definition

The Gateway A connection shows `gw-a` as the local identity, `gw-b` as the remote identity, and traffic selectors `10.10.1.1/32` to `10.20.1.1/32`.

![Gateway A connection definition](Screenshots/Screenshot%202026-11-18%20104049.png)

### 5. Gateway B connection definition

The mirrored Gateway B connection shows the reverse local and remote identities and traffic selectors.

![Gateway B connection definition](Screenshots/Screenshot%202026-11-18%20104722.png)

### 6. IKEv2 and CHILD_SA establishment

This output confirms IKE_SA_INIT, IKE_AUTH, PSK authentication, the established IKE SA, and the installed CHILD_SA with ESP and AES-GCM-256.

![Tunnel initiation and SA establishment](Screenshots/Screenshot%202026-11-18%20104107.png)

### 7. XFRM states and tunnel policies

The XFRM state and policy output shows inbound and outbound ESP states, tunnel selectors, and the `10.10.1.1/32` to `10.20.1.1/32` traffic path.

![XFRM states and policies](Screenshots/Screenshot%202026-11-18%20104418.png)

### 8. Protected traffic in Wireshark

The packet capture shows IKEv2, NAT-T/UDP 4500, and ESP traffic between the gateway addresses. The Encapsulating Security Payload content does not reveal the inner ICMP payload.

![Wireshark IPsec packet analysis](Screenshots/Screenshot%202026-11-18%20105043.png)

## Result
The two Kali Linux gateways were configured as IPsec tunnel endpoints. The IKEv2 exchange established an IKE SA and CHILD_SA, and ping traffic between `10.10.1.1` and `10.20.1.1` crossed the tunnel using ESP. XFRM states and policies were installed on the gateways, and Wireshark captured the IKE and ESP packets.

## Observations
- strongSwan 6.1.0 and its charon-systemd daemon were running successfully.
- Gateway A used `192.168.188.129`, and Gateway B used `192.168.188.135`.
- The tunnel protected traffic between `10.10.1.1/32` and `10.20.1.1/32`.
- The capture displayed IKEv2 negotiation messages and ESP packets.
- ESP encrypted the inner ICMP payload while the outer gateway addresses remained visible.
- NAT-T may be detected and carried ESP inside UDP 4500.

## Conclusion
This experiment successfully demonstrated a strongSwan IPsec tunnel in tunnel mode. IKEv2 authenticated and negotiated the gateways, while ESP protected traffic between their private loopback networks. Verification with `swanctl`, `ip xfrm state`, `ip xfrm policy`, ping, tcpdump, and Wireshark confirmed that the tunnel was active and carrying protected traffic.

## Cleanup
After saving the packet capture and screenshots, the tunnel and temporary loopback addresses can be removed:

```bash
sudo swanctl --terminate --child lab-net 2>/dev/null
sudo ip address del 10.10.1.1/32 dev lo  # Gateway A
sudo ip address del 10.20.1.1/32 dev lo  # Gateway B
```

## Security Note
The pre-shared key must remain secret and must not be committed or shown in screenshots. The test should only be performed on authorized lab networks. Production deployments should use stronger certificate or enterprise authentication instead of a lab-only PSK.

## Reference
- [Experiment 9 procedure PDF](Experiment_9_IPsec_VPN_strongSwan_Kali_Procedure.pdf)
