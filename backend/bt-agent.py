#!/usr/bin/python3

from gi.repository import GLib
import dbus
import dbus.service
import dbus.mainloop.glib

class BluetoothAgent(dbus.service.Object):
    def __init__(self, bus, path):
        super().__init__(bus, path)

    @dbus.service.method('org.bluez.Agent1', in_signature="", out_signature="")
    def Release(self):
        print("Agent released")
        return

    @dbus.service.method('org.bluez.Agent1', in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"Authorize service for device {device}, uuid {uuid}")
        return

    @dbus.service.method('org.bluez.Agent1', in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print(f"Passkey requested for device {device}")
        return None  # Aucun passkey

    @dbus.service.method('org.bluez.Agent1', in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print(f"Request confirmation for device {device}, passkey {passkey}")
        # Confirmez toujours la demande
        return

    @dbus.service.method('org.bluez.Agent1', in_signature="", out_signature="")
    def Cancel(self):
        print("Request cancelled")
        return

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    agent = BluetoothAgent(bus, '/org/bluez/agent')
    
    obj = bus.get_object('org.bluez', '/org/bluez')
    manager = dbus.Interface(obj, 'org.bluez.AgentManager1')
    
    print("Registering agent with NoInputNoOutput capability...")
    manager.RegisterAgent('/org/bluez/agent', 'NoInputNoOutput')
    
    print("Setting as default agent...")
    manager.RequestDefaultAgent('/org/bluez/agent')
    
    print("Agent is now running...")
    GLib.MainLoop().run()

if __name__ == '__main__':
    main()