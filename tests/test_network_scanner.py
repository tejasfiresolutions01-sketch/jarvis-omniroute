"""
Unit tests for J.A.R.V.I.S. Local LAN Perimeter & IoT Device Scanner.
"""

import unittest
from unittest.mock import patch, MagicMock
from tools.network_scanner import NetworkScanner

class TestNetworkScanner(unittest.TestCase):

    def setUp(self):
        self.scanner = NetworkScanner()

    @patch("socket.gethostname", return_value="StarkTower-Mainframe")
    @patch("socket.gethostbyname", return_value="192.168.1.100")
    @patch.object(NetworkScanner, "_detect_default_gateway", return_value="192.168.1.1")
    def test_get_local_identity(self, mock_gw, mock_ip, mock_host):
        identity = self.scanner.get_local_identity()
        self.assertEqual(identity["hostname"], "StarkTower-Mainframe")
        self.assertEqual(identity["local_ip"], "192.168.1.100")
        self.assertEqual(identity["gateway"], "192.168.1.1")

    @patch("subprocess.run")
    def test_scan_arp_table(self, mock_run):
        mock_output = (
            "Interface: 192.168.1.100 --- 0x3\n"
            "  Internet Address      Physical Address      Type\n"
            "  192.168.1.1           00-14-22-01-23-45     dynamic\n"
            "  192.168.1.50          aa-bb-cc-dd-ee-ff     dynamic\n"
            "  224.0.0.22            01-00-5e-00-00-16     static\n"
            "  255.255.255.255       ff-ff-ff-ff-ff-ff     static\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)

        devices = self.scanner.scan_arp_table()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["ip"], "192.168.1.1")
        self.assertEqual(devices[0]["mac"], "00-14-22-01-23-45")
        self.assertEqual(devices[1]["ip"], "192.168.1.50")

    @patch("subprocess.run")
    def test_ping_host_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Reply from 192.168.1.1: bytes=32 time=4ms TTL=64")
        latency = self.scanner.ping_host("192.168.1.1")
        self.assertEqual(latency, 4)

    @patch("subprocess.run")
    def test_ping_host_timeout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="Request timed out.")
        latency = self.scanner.ping_host("192.168.1.99")
        self.assertIsNone(latency)

    @patch("socket.socket")
    def test_check_open_port(self, mock_socket_class):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket_class.return_value.__enter__.return_value = mock_sock

        self.assertTrue(self.scanner.check_open_port("127.0.0.1", 80))

    def test_format_butler_perimeter_report(self):
        sample_results = {
            "host_identity": {
                "hostname": "Mark85-Core",
                "local_ip": "192.168.1.100",
                "gateway": "192.168.1.1"
            },
            "gateway_latency_ms": 3,
            "discovered_nodes": [
                {
                    "ip": "192.168.1.1",
                    "mac": "00-14-22-01-23-45",
                    "type": "dynamic",
                    "latency_ms": 3,
                    "open_ports": [80, 443],
                    "is_gateway": True
                }
            ],
            "node_count": 2
        }

        report = self.scanner.format_butler_perimeter_report(sample_results)
        self.assertIn("Perimeter reconnaissance complete, sir", report)
        self.assertIn("Mark85-Core", report)
        self.assertIn("192.168.1.1", report)
        self.assertIn("Default Gateway", report)
        self.assertIn("All perimeter telemetry is nominal", report)


if __name__ == "__main__":
    unittest.main()
