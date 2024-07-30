from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo

class MyListener:
    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            self.log_service_info("added", name, info)

    def remove_service(self, zeroconf, service_type, name):
        print(f"Service {name} removed")

    def update_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            self.log_service_info("updated", name, info)

    def log_service_info(self, action, name, info):
        addresses = ["%s:%d" % (address, info.port) for address in info.parsed_addresses()]
        properties = info.properties
        print(f"Service {name} {action}:")
        print(f"  Addresses: {addresses}")
        print(f"  Server: {info.server}")
        print(f"  Properties:")
        for key, value in properties.items():
            if value is not None:
                print(f"    {key.decode('utf-8')}: {value.decode('utf-8')}")

zeroconf = Zeroconf()
listener = MyListener()
browser = ServiceBrowser(zeroconf, "_esphomelib._tcp.local.", listener)

try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()
