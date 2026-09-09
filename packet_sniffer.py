from scapy.all import sniff, wrpcap

from scapy.all import sniff, wrpcap


class PacketSniffer:

    def __init__(self, interface="wlan0",
                 output_file="capture.pcap"):
        self.interface = interface
        self.output_file = output_file
        self.packets = []

    def start(self):
        print("Starting packet capture...")

        self.packets = sniff(
            iface=self.interface,
            filter="tcp port 80 or tcp port 9000"
        )

    def save(self):
        wrpcap(self.output_file, self.packets)

        print(
            f"Saved {len(self.packets)} packets "
            f"to {self.output_file}"
        )


if __name__ == "__main__":

    sniffer = PacketSniffer()

    try:
        sniffer.start()

    except KeyboardInterrupt:
        print("\nStopping capture...")
        sniffer.save()
