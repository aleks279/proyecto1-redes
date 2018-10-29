# This file is part of Scapy
# See http://www.secdev.org/projects/scapy for more information
# Copyright (C) Philippe Biondi <phil@secdev.org>
# This program is published under a GPLv2 license

"""
Routing and handling of network interfaces.
"""


from __future__ import absolute_import


import scapy.consts
from scapy.config import conf
from scapy.error import Scapy_Exception, warning
from scapy.modules import six
from scapy.utils import atol, ltoa, itom, plain_str, pretty_list


##############################
#  Routing/Interfaces stuff  #
##############################

class Route:
    def __init__(self):
        self.resync()
        self.invalidate_cache()

    def invalidate_cache(self):
        self.cache = {}

    def resync(self):
        from scapy.arch import read_routes
        self.invalidate_cache()
        self.routes = read_routes()

    def __repr__(self):
        rtlst = []
        for net, msk, gw, iface, addr, metric in self.routes:
            rtlst.append((ltoa(net),
                          ltoa(msk),
                          gw,
                          (iface.name if not isinstance(iface, six.string_types) else iface),  # noqa: E501
                          addr,
                          str(metric)))

        return pretty_list(rtlst,
                           [("Network", "Netmask", "Gateway", "Iface", "Output IP", "Metric")])  # noqa: E501

    def make_route(self, host=None, net=None, gw=None, dev=None, metric=1):
        from scapy.arch import get_if_addr
        if host is not None:
            thenet, msk = host, 32
        elif net is not None:
            thenet, msk = net.split("/")
            msk = int(msk)
        else:
            raise Scapy_Exception("make_route: Incorrect parameters. You should specify a host or a net")  # noqa: E501
        if gw is None:
            gw = "0.0.0.0"
        if dev is None:
            if gw:
                nhop = gw
            else:
                nhop = thenet
            dev, ifaddr, _ = self.route(nhop)
        else:
            ifaddr = get_if_addr(dev)
        return (atol(thenet), itom(msk), gw, dev, ifaddr, metric)

    def add(self, *args, **kargs):
        """Ex:
        add(net="192.168.1.0/24",gw="1.2.3.4")
        """
        self.invalidate_cache()
        self.routes.append(self.make_route(*args, **kargs))

    def delt(self, *args, **kargs):
        """delt(host|net, gw|dev)"""
        self.invalidate_cache()
        route = self.make_route(*args, **kargs)
        try:
            i = self.routes.index(route)
            del(self.routes[i])
        except ValueError:
            warning("no matching route found")

    def ifchange(self, iff, addr):
        self.invalidate_cache()
        the_addr, the_msk = (addr.split("/") + ["32"])[:2]
        the_msk = itom(int(the_msk))
        the_rawaddr = atol(the_addr)
        the_net = the_rawaddr & the_msk

        for i, route in enumerate(self.routes):
            net, msk, gw, iface, addr, metric = route
            if scapy.consts.WINDOWS:
                if iff.guid != iface.guid:
                    continue
            elif iff != iface:
                continue
            if gw == '0.0.0.0':
                self.routes[i] = (the_net, the_msk, gw, iface, the_addr, metric)  # noqa: E501
            else:
                self.routes[i] = (net, msk, gw, iface, the_addr, metric)
        conf.netcache.flush()

    def ifdel(self, iff):
        self.invalidate_cache()
        new_routes = []
        for rt in self.routes:
            if scapy.consts.WINDOWS:
                if iff.guid == rt[3].guid:
                    continue
            elif iff == rt[3]:
                continue
            new_routes.append(rt)
        self.routes = new_routes

    def ifadd(self, iff, addr):
        self.invalidate_cache()
        the_addr, the_msk = (addr.split("/") + ["32"])[:2]
        the_msk = itom(int(the_msk))
        the_rawaddr = atol(the_addr)
        the_net = the_rawaddr & the_msk
        self.routes.append((the_net, the_msk, '0.0.0.0', iff, the_addr, 1))

    def route(self, dest, verbose=None):
        if dest is None:
            dest = "0.0.0.0"
        elif isinstance(dest, bytes):
            try:
                dest = plain_str(dest)
            except UnicodeDecodeError:
                dest = "0.0.0.0"
        if dest in self.cache:
            return self.cache[dest]
        if verbose is None:
            verbose = conf.verb
        # Transform "192.168.*.1-5" to one IP of the set
        dst = dest.split("/")[0]
        dst = dst.replace("*", "0")
        while True:
            idx = dst.find("-")
            if idx < 0:
                break
            m = (dst[idx:] + ".").find(".")
            dst = dst[:idx] + dst[idx + m:]

        dst = atol(dst)
        paths = []
        for d, m, gw, i, a, me in self.routes:
            if not a:  # some interfaces may not currently be connected
                continue
            aa = atol(a)
            if aa == dst:
                paths.append(
                    (0xffffffff, 1, (scapy.consts.LOOPBACK_INTERFACE, a, "0.0.0.0"))  # noqa: E501
                )
            if (dst & m) == (d & m):
                paths.append((m, me, (i, a, gw)))
        if not paths:
            if verbose:
                warning("No route found (no default route?)")
            return scapy.consts.LOOPBACK_INTERFACE, "0.0.0.0", "0.0.0.0"
        # Choose the more specific route
        # Sort by greatest netmask
        paths.sort(key=lambda x: x[0], reverse=True)
        # Get all paths having the (same) greatest mask
        paths = [i for i in paths if i[0] == paths[0][0]]
        # Tie-breaker: Metrics
        paths.sort(key=lambda x: x[1])
        # Return interface
        ret = paths[0][2]
        self.cache[dest] = ret
        return ret

    def get_if_bcast(self, iff):
        for net, msk, gw, iface, addr, metric in self.routes:
            if net == 0:
                continue
            if scapy.consts.WINDOWS:
                if iff.guid != iface.guid:
                    continue
            elif iff != iface:
                continue
            bcast = atol(addr) | (~msk & 0xffffffff)  # FIXME: check error in atol()  # noqa: E501
            return ltoa(bcast)
        warning("No broadcast address found for iface %s\n", iff)


conf.route = Route()

iface = conf.route.route("0.0.0.0", verbose=0)[0]

# Warning: scapy.consts.LOOPBACK_INTERFACE must always be used statically, because it  # noqa: E501
# may be changed by scapy/arch/windows during execution

if getattr(iface, "name", iface) == scapy.consts.LOOPBACK_INTERFACE:
    from scapy.arch import get_working_if
    conf.iface = get_working_if()
else:
    conf.iface = iface

del iface
