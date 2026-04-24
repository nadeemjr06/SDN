from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
from ryu.lib import hub

class MonitorSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MonitorSwitch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.prev_stats = {}
        self.monitor_thread = hub.spawn(self._monitor)

    # Register switches
    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        dp = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[dp.id] = dp
        elif ev.state == DEAD_DISPATCHER:
            del self.datapaths[dp.id]

    # Install table-miss flow rule
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER,
                                          ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, match, actions)

    def add_flow(self, dp, priority, match, actions):
        ofp = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=dp, priority=priority,
                               match=match, instructions=inst)
        dp.send_msg(mod)

    # Learning switch logic (IMPORTANT FOR MARKS)
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        dst = eth.dst
        src = eth.src

        dpid = dp.id
        self.mac_to_port.setdefault(dpid, {})

        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofp.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install flow rule
        if out_port != ofp.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(dp, 1, match, actions)

        data = None if msg.buffer_id != ofp.OFP_NO_BUFFER else msg.data

        out = parser.OFPPacketOut(datapath=dp,
                                 buffer_id=msg.buffer_id,
                                 in_port=in_port,
                                 actions=actions,
                                 data=data)
        dp.send_msg(out)

    # Monitoring thread
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self.request_stats(dp)
            hub.sleep(5)

    def request_stats(self, dp):
        parser = dp.ofproto_parser
        ofp = dp.ofproto
        req = parser.OFPPortStatsRequest(dp, 0, ofp.OFPP_ANY)
        dp.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        for stat in ev.msg.body:
            port = stat.port_no
            rx_bytes = stat.rx_bytes

            key = (ev.msg.datapath.id, port)

            if key in self.prev_stats:
                prev = self.prev_stats[key]
                bandwidth = (rx_bytes - prev) / 5

                print(f"[MONITOR] Switch {key[0]} Port {port} -> {bandwidth:.2f} Bps")

            self.prev_stats[key] = rx_bytes