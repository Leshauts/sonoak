# backend/services/bluetooth/events.py
import dbus
from typing import Dict

class BluetoothEventHandler:
    def __init__(self, manager):
        self.manager = manager
        self.bus = dbus.SystemBus()
        
    def setup_signal_handlers(self):
        """Configure les gestionnaires de signaux DBus"""
        print("Configuration des gestionnaires d'événements Bluetooth...")
        
        # Observer les changements de propriétés
        self.bus.add_signal_receiver(
            self._properties_changed,
            dbus_interface="org.freedesktop.DBus.Properties",
            signal_name="PropertiesChanged",
            arg0="org.bluez.Device1",
            path_keyword="path"
        )
        print("Gestionnaires d'événements configurés.")

    def _properties_changed(self, interface: str, changed: Dict, invalidated, path: str):
        """Gère les changements de propriétés"""
        if "Connected" in changed:
            is_connected = bool(changed["Connected"])
            print(f"État de connexion changé pour {path}: {is_connected}")
            
            if is_connected:
                print("Appareil connecté - ajout à la liste")
                self.manager.add_device(path)
            else:
                print("Appareil déconnecté - retrait de la liste")
                self.manager.remove_device(path)