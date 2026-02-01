Rename ProxierHealthServer to ProxyHealthServer across all proxier implementations

Rename type, constructor, and all references across iptables, ipvs, and nftables proxy code



Search hints:
- Look in pkg/proxy/healthcheck/ for type definition
- Find NewProxierHealthServer constructor
- Search pkg/proxy/iptables, pkg/proxy/ipvs, pkg/proxy/nftables for usages
- Update struct field names and method receivers
