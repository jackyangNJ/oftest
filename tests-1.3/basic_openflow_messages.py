import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp
import FuncUtils
from oftest.testutils import *


@group('standard')
class FeaturesRequest(base_tests.SimpleProtocol):
    """
    Test features_request to make sure we get a response

    Derived from Test case 20.10 --> Verify Features Request / Reply is implemented
    """

    def runTest(self):
        request = ofp.message.features_request()
        response, _ = self.controller.transact(request)
        self.assertTrue(response is not None,
                        'Did not get features reply')


@group('standard')
class ConfigGet(base_tests.SimpleProtocol):
    """
    Verify that a basic Get Config Request does not generate an error.

    Derived from Test case 20.20: Verify basic Config Request is implemented
    """

    def runTest(self):
        request = ofp.message.get_config_request()
        response, _ = self.controller.transact(request)
        logging.info(response.show())
        self.assertTrue(response is not None,
                        "No response to get config request")


@group('standard')
class FlowAddRequest(base_tests.SimpleProtocol):
    """
    Verify that a basic Flow ADD request does not generate an error.

    Derived from Test case 20.30: Verify basic Modify state Add message is implemented
    """

    def runTest(self):
        request = ofp.message.flow_add()
        self.controller.message_send(request)
        # send Barrier Message to check errors
        do_barrier(self.controller)

        response, _ = self.controller.poll(ofp.OFPT_ERROR)
        self.assertTrue(response is None,
                        "Error message was received")


@group('standard')
class FlowDeleteRequest(base_tests.SimpleProtocol):
    """
    Verify that a basic Flow Delete request does not generate an error.

    Derived from Test case 20.40: Verify basic Modify state Delete message is implemented
    """

    def runTest(self):
        request = ofp.message.flow_delete()
        self.controller.message_send(request)
        # send Barrier Message to check errors
        do_barrier(self.controller)

        response, _ = self.controller.poll(ofp.OFPT_ERROR)
        self.assertTrue(response is None,
                        "Error message was received")


@group('standard')
class FlowModifyRequest(base_tests.SimpleProtocol):
    """
    Verify that a basic Modify State Modify request does not generate an error.

    Derived from Test case 20.50: Verify basic Modify Flow Modify message is implemented
    """

    def runTest(self):
        request = ofp.message.flow_modify()
        self.controller.message_send(request)
        # send Barrier Message to check errors
        do_barrier(self.controller)

        response, _ = self.controller.poll(ofp.OFPT_ERROR)
        self.assertTrue(response is None,
                        "Error message was received")


@group('standard')
class StatsRequest(base_tests.SimpleProtocol):
    """
    Verify that a basic Read state request does not generate an error.

    Derived from Test case 20.60: Verify basic Read state is implemented
    """

    def runTest(self):
        request = ofp.message.stats_request()
        logging.info("Sending desc stats request")
        response, _ = self.controller.transact(request)
        self.assertTrue(response != None, "No response to desc stats request")
        self.assertEquals(response.flags, 0, "Unexpected bit set in desc stats reply flags")


@group('standard')
class PacketOut(base_tests.SimpleDataPlane):
    """
    Verify that a basic send packet request does not generate an error

    Derived from Test case 20.70: Verify basic send packet is implemented

    Send packet out message to controller for each dataplane port and
    verify the packet appears on the appropriate dataplane port
    """

    def runTest(self):
        pkt = str(simple_tcp_packet())

        for of_port in config["port_map"].keys():
            msg = ofp.message.packet_out(
                in_port=ofp.OFPP_CONTROLLER,
                actions=[ofp.action.output(port=of_port)],
                buffer_id=ofp.OFP_NO_BUFFER,
                data=pkt)

            self.controller.message_send(msg)
            verify_packets(self, pkt, [of_port])


@group('standard')
class BarrierRequest(base_tests.SimpleProtocol):
    """
    Verify that a basic barrier request does not generate an error.

    Test case 20.80: Verify basic barrier request-reply is implemented
    """

    def runTest(self):
        request = ofp.message.barrier_request()
        response, _ = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "No response to Barrier Request")


@group('standard')
class PacketInMiss(base_tests.SimpleDataPlane):
    """
    Test case 20.90: Packet_in generation

    Test packet in function for a table-miss flow
    Send a packet to each dataplane port and verify that a packet
    in message is received from the controller for each
    """

    def runTest(self):
        delete_all_flows(self.controller)

        parsed_pkt = simple_tcp_packet()
        pkt = str(parsed_pkt)

        FuncUtils.flow_entry_install(
            self.controller,
            "flow_add",
            instructions=[
                ofp.instruction.apply_actions(
                    actions=[
                        ofp.action.output(
                            port=ofp.OFPP_CONTROLLER,
                            max_len=ofp.OFPCML_NO_BUFFER)])],
            prio=0)

        for of_port in config["port_map"].keys():
            logging.info("PacketInMiss test, port %d", of_port)
            self.dataplane.send(of_port, pkt)
            verify_packet_in(self, pkt, of_port, ofp.OFPR_NO_MATCH)
            # verify_packets(self, pkt, []) ensures no packets are received from other ports
            verify_packets(self, pkt, [])


@group('standard')
class HelloRequest(base_tests.SimpleProtocol):
    """
    Verify basic Hello message generation with correct version field

    Test case 20.100: Verify basic Hello messages are implemented
    """

    def runTest(self):
        request = ofp.message.hello()
        self.controller.message_send(request)


@group('standard')
class Echo(base_tests.SimpleProtocol):
    """
    Verify basic Echo Reply generation

    Test case 20.110: Verify Echo Reply messages are implemented
    """

    def runTest(self):
        request = ofp.message.echo_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get echo reply")
        self.assertEqual(response.type, ofp.OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')
        self.assertEqual(len(response.data), 0, 'response data non-empty')


@group('Optional')
class EchoWithData(base_tests.SimpleProtocol):
    """
    Test echo response with short string data
    """

    def runTest(self):
        data = 'OpenFlow Will Rule The World'
        request = ofp.message.echo_request(data=data)
        response, _ = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get echo reply")
        self.assertEqual(response.type, ofp.OFPT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')
        self.assertEqual(request.data, response.data,
                         'response data != request data')


@group('Optional')
class DefaultDrop(base_tests.SimpleDataPlane):
    """
    Check that an empty flowtable results in drops
    """

    def runTest(self):
        in_port, = openflow_ports(1)
        delete_all_flows(self.controller)

        pkt = str(simple_tcp_packet())
        self.dataplane.send(in_port, pkt)
        verify_no_packet_in(self, pkt, None)
        verify_packets(self, pkt, [])


@group('Optional')
class OutputExact(base_tests.SimpleDataPlane):
    """
    Test output function for an exact-match flow

    For each port A, adds a flow directing matching packets to that port.
    Then, for all other ports B != A, verifies that sending a matching packet
    to B results in an output to A.
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        delete_all_flows(self.controller)

        parsed_pkt = simple_tcp_packet()
        pkt = str(parsed_pkt)
        match = packet_to_flow_match(self, parsed_pkt)

        for out_port in ports:
            request = ofp.message.flow_add(
                table_id=test_param_get("table", 0),
                cookie=42,
                match=match,
                instructions=[
                    ofp.instruction.apply_actions(
                        actions=[
                            ofp.action.output(
                                port=out_port,
                                max_len=ofp.OFPCML_NO_BUFFER)])],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=1000)

            logging.info("Inserting flow sending matching packets to port %d", out_port)
            self.controller.message_send(request)
            do_barrier(self.controller)

            for in_port in ports:
                if in_port == out_port:
                    continue
                logging.info("OutputExact test, ports %d to %d", in_port, out_port)
                self.dataplane.send(in_port, pkt)
                verify_packets(self, pkt, [out_port])


@group('Optional')
class OutputWildcard(base_tests.SimpleDataPlane):
    """
    Test output function for a match-all (but not table-miss) flow

    For each port A, adds a flow directing all packets to that port.
    Then, for all other ports B != A, verifies that sending a packet
    to B results in an output to A.
    """

    def runTest(self):
        ports = sorted(config["port_map"].keys())

        delete_all_flows(self.controller)

        pkt = str(simple_tcp_packet())

        for out_port in ports:
            request = ofp.message.flow_add(
                table_id=test_param_get("table", 0),
                cookie=42,
                instructions=[
                    ofp.instruction.apply_actions(
                        actions=[
                            ofp.action.output(
                                port=out_port,
                                max_len=ofp.OFPCML_NO_BUFFER)])],
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=1000)

            logging.info("Inserting flow sending all packets to port %d", out_port)
            self.controller.message_send(request)
            do_barrier(self.controller)

            for in_port in ports:
                if in_port == out_port:
                    continue
                logging.info("OutputWildcard test, ports %d to %d", in_port, out_port)
                self.dataplane.send(in_port, pkt)
                verify_packets(self, pkt, [out_port])


@group('Optional')
class PacketInExact(base_tests.SimpleDataPlane):
    """
    Test packet in function for an exact-match flow

    Send a packet to each dataplane port and verify that a packet
    in message is received from the controller for each
    """

    def runTest(self):
        delete_all_flows(self.controller)

        parsed_pkt = simple_tcp_packet()
        pkt = str(parsed_pkt)
        match = packet_to_flow_match(self, parsed_pkt)

        request = ofp.message.flow_add(
            table_id=test_param_get("table", 0),
            cookie=42,
            match=match,
            instructions=[
                ofp.instruction.apply_actions(
                    actions=[
                        ofp.action.output(
                            port=ofp.OFPP_CONTROLLER,
                            max_len=ofp.OFPCML_NO_BUFFER)])],
            buffer_id=ofp.OFP_NO_BUFFER,
            priority=1000)

        logging.info("Inserting flow sending matching packets to controller")
        self.controller.message_send(request)
        do_barrier(self.controller)

        for of_port in config["port_map"].keys():
            logging.info("PacketInExact test, port %d", of_port)
            self.dataplane.send(of_port, pkt)
            verify_packet_in(self, pkt, of_port, ofp.OFPR_ACTION)
            verify_packets(self, pkt, [])


@group('Optional')
class PacketInWildcard(base_tests.SimpleDataPlane):
    """
    Test packet in function for a match-all flow

    Send a packet to each dataplane port and verify that a packet
    in message is received from the controller for each
    """

    def runTest(self):
        delete_all_flows(self.controller)

        pkt = str(simple_tcp_packet())

        request = ofp.message.flow_add(
            table_id=test_param_get("table", 0),
            cookie=42,
            instructions=[
                ofp.instruction.apply_actions(
                    actions=[
                        ofp.action.output(
                            port=ofp.OFPP_CONTROLLER,
                            max_len=ofp.OFPCML_NO_BUFFER)])],
            buffer_id=ofp.OFP_NO_BUFFER,
            priority=1000)

        logging.info("Inserting flow sending all packets to controller")
        self.controller.message_send(request)
        do_barrier(self.controller)

        for of_port in config["port_map"].keys():
            logging.info("PacketInWildcard test, port %d", of_port)
            self.dataplane.send(of_port, pkt)
            verify_packet_in(self, pkt, of_port, ofp.OFPR_ACTION)
            verify_packets(self, pkt, [])


@group('Optional')
class FlowRemoveAll(base_tests.SimpleProtocol):
    """
    Remove all flows; required for almost all tests

    Add a bunch of flows, remove them, and then make sure there are no flows left
    This is an intentionally naive test to see if the baseline functionality works
    and should be a precondition to any more complicated deletion test (e.g.,
    delete_strict vs. delete)
    """

    def runTest(self):
        for i in range(1, 5):
            logging.debug("Adding flow %d", i)
            request = ofp.message.flow_add(
                buffer_id=ofp.OFP_NO_BUFFER,
                priority=i * 1000)
            self.controller.message_send(request)
        do_barrier(self.controller)

        delete_all_flows(self.controller)

        logging.info("Sending flow stats request")
        stats = get_flow_stats(self, ofp.match())
        self.assertEqual(len(stats), 0, "Expected empty flow stats reply")


## Multipart messages



@group('Optional')
class FlowStats(base_tests.SimpleProtocol):
    """
    Flow stats multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        logging.info("Sending flow stats request")
        stats = get_flow_stats(self, ofp.match())
        logging.info("Received %d flow stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class AggregateStats(base_tests.SimpleProtocol):
    """
    Aggregate flow stats multipart transaction

    Only verifies we get a single reply.
    """

    def runTest(self):
        request = ofp.message.aggregate_stats_request(
            table_id=ofp.OFPTT_ALL,
            out_port=ofp.OFPP_ANY,
            out_group=ofp.OFPG_ANY,
            cookie=0,
            cookie_mask=0)
        logging.info("Sending aggregate flow stats request")
        response, _ = self.controller.transact(request)
        self.assertTrue(response != None, "No response to aggregate stats request")
        logging.info(response.show())
        self.assertEquals(response.flags, 0, "Unexpected bit set in aggregate stats reply flags")


@group('Optional')
class TableStats(base_tests.SimpleProtocol):
    """
    Table stats multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        logging.info("Sending table stats request")
        stats = get_stats(self, ofp.message.table_stats_request())
        logging.info("Received %d table stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class PortStats(base_tests.SimpleProtocol):
    """
    Port stats multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        request = ofp.message.port_stats_request(port_no=ofp.OFPP_ANY)
        logging.info("Sending port stats request")
        stats = get_stats(self, request)
        logging.info("Received %d port stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class QueueStats(base_tests.SimpleProtocol):
    """
    Queue stats multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        request = ofp.message.queue_stats_request(port_no=ofp.OFPP_ANY,
                                                  queue_id=ofp.OFPQ_ALL)
        logging.info("Sending queue stats request")
        stats = get_stats(self, request)
        logging.info("Received %d queue stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class GroupStats(base_tests.SimpleProtocol):
    """
    Group stats multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        request = ofp.message.group_stats_request(group_id=ofp.OFPG_ALL)
        logging.info("Sending group stats request")
        stats = get_stats(self, request)
        logging.info("Received %d group stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class GroupDescStats(base_tests.SimpleProtocol):
    """
    Group description multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        request = ofp.message.group_desc_stats_request()
        logging.info("Sending group desc stats request")
        stats = get_stats(self, request)
        logging.info("Received %d group desc stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class GroupFeaturesStats(base_tests.SimpleProtocol):
    """
    Group features multipart transaction

    Only verifies we get a single reply.
    """

    def runTest(self):
        request = ofp.message.group_features_stats_request()
        logging.info("Sending group features stats request")
        response, _ = self.controller.transact(request)
        self.assertTrue(response != None, "No response to group features stats request")
        logging.info(response.show())
        self.assertEquals(response.flags, 0, "Unexpected bit set in group features stats reply flags")


@group('Optional')
class MeterStats(base_tests.SimpleProtocol):
    """
    Meter stats multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        request = ofp.message.meter_stats_request(meter_id=ofp.OFPM_ALL)
        logging.info("Sending meter stats request")
        stats = get_stats(self, request)
        logging.info("Received %d meter stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class MeterConfigStats(base_tests.SimpleProtocol):
    """
    Meter config multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        request = ofp.message.meter_config_stats_request(meter_id=ofp.OFPM_ALL)
        logging.info("Sending meter config stats request")
        stats = get_stats(self, request)
        logging.info("Received %d meter config stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class MeterFeaturesStats(base_tests.SimpleProtocol):
    """
    Meter features multipart transaction

    Only verifies we get a single reply.
    """

    def runTest(self):
        request = ofp.message.meter_features_stats_request()
        logging.info("Sending meter features stats request")
        response, _ = self.controller.transact(request)
        self.assertTrue(response != None, "No response to meter features stats request")
        logging.info(response.show())
        self.assertEquals(response.flags, 0, "Unexpected bit set in meter features stats reply flags")


@disabled  # pyloxi does not yet support table features
class TableFeaturesStats(base_tests.SimpleProtocol):
    """
    Table features multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        logging.info("Sending table features stats request")
        stats = get_stats(self, ofp.message.table_features_stats_request())
        logging.info("Received %d table features stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class PortDescStats(base_tests.SimpleProtocol):
    """
    Port description multipart transaction

    Only verifies we get a reply.
    """

    def runTest(self):
        logging.info("Sending port desc stats request")
        stats = get_stats(self, ofp.message.port_desc_stats_request())
        logging.info("Received %d port desc stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())


@group('Optional')
class PortConfigMod(base_tests.SimpleProtocol):
    """
    Modify a bit in port config and verify changed

    Get the switch configuration, modify the port configuration
    and write it back; get the config again and verify changed.
    Then set it back to the way it was.
    """

    def runTest(self):
        logging.info("Running " + str(self))
        for of_port, _ in config["port_map"].items():  # Grab first port
            break

        (_, config1, _) = \
            port_config_get(self.controller, of_port)
        self.assertTrue(config is not None, "Did not get port config")

        logging.debug("OFPPC_NO_PACKET_IN bit port " + str(of_port) + " is now " +
                      str(config1 & ofp.OFPPC_NO_PACKET_IN))

        rv = port_config_set(self.controller, of_port,
                             ofp.OFPPC_NO_PACKET_IN,
                             ofp.OFPPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")

        # Verify change took place with same feature request
        (_, config2, _) = port_config_get(self.controller, of_port)
        self.assertTrue(config2 is not None, "Did not get port config2")
        logging.debug("OFPPC_NO_PACKET_IN bit port " + str(of_port) + " is now " +
                      str(config2 & ofp.OFPPC_NO_PACKET_IN))
        self.assertTrue(config2 & ofp.OFPPC_NO_PACKET_IN !=
                        config1 & ofp.OFPPC_NO_PACKET_IN,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_port, config1,
                             ofp.OFPPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")


@group('Optional')
class AsyncConfigGet(base_tests.SimpleProtocol):
    """
    Verify initial async config

    Other tests rely on connections starting with these values.
    """

    def runTest(self):
        logging.info("Sending get async config request")
        response, _ = self.controller.transact(ofp.message.async_get_request())
        self.assertTrue(response != None, "No response to get async config request")
        logging.info(response.show())
        self.assertEquals(response.packet_in_mask_equal_master & 0x07, 0x07)
        self.assertEquals(response.port_status_mask_equal_master & 0x07, 0x07)
        self.assertEquals(response.flow_removed_mask_equal_master & 0x0f, 0x0f)
