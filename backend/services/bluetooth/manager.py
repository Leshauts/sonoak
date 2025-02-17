# backend/services/bluetooth/manager.py
import dbus
import dbus.mainloop.glib
import asyncio
import subprocess
import time
from typing import Dict, List, Optional
from datetime import datetime
from services.audio.manager import AudioSource


def set_a2dp_sink(device_address: str):
    """Configure l'audio A2DP pour le périphérique Bluetooth."""
    try:
        subprocess.run(["bluetoothctl", "trust", device_address], capture_output=True)
        subprocess.run(["bluetoothctl", "connect", device_address], capture_output=True)
        
        # Attendre la stabilisation
        time.sleep(1)
        print(f"[A2DP] Audio configuré pour {device_address}")
            
    except subprocess.CalledProcessError as e:
        print(f"[A2DP] Erreur lors de la configuration: {e}")

class BluetoothManager:
    def __init__(self, websocket_manager, audio_manager=None):
        print("Initialisation du BluetoothManager...")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.websocket_manager = websocket_manager
        self.audio_manager = audio_manager
        self.active_device: Optional[dict] = None
        self.initialized = False
        self.initialization_retries = 0
        self.max_retries = 5
        self.obj_manager = None
        self.adapter = None
        self.adapter_obj = None
        
        self.initialize()

    def initialize(self):
        """Initialise le manager Bluetooth"""
        try:
            print("Tentative d'initialisation du BluetoothManager...")
            self.obj_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/"),
                "org.freedesktop.DBus.ObjectManager"
            )
            
            self.adapter_obj = self.bus.get_object('org.bluez', '/org/bluez/hci0')
            self.adapter = dbus.Interface(self.adapter_obj, 'org.bluez.Adapter1')
            
            # Configuration de l'adaptateur
            adapter_props = dbus.Interface(self.adapter_obj, 'org.freedesktop.DBus.Properties')
            adapter_props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(True))
            adapter_props.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(True))
            adapter_props.Set('org.bluez.Adapter1', 'Pairable', dbus.Boolean(True))
            
            print("Adaptateur Bluetooth initialisé")
            self.initialized = True
            self.initialization_retries = 0
            
            self._setup_signal_handlers()
            self._check_existing_connections()
            
        except Exception as e:
            print(f"Erreur d'initialisation: {e}")
            self.initialized = False
            self.active_device = None
            
            self.initialization_retries += 1
            if self.initialization_retries < self.max_retries:
                print(f"Nouvelle tentative dans 2 secondes ({self.initialization_retries}/{self.max_retries})")
                asyncio.get_event_loop().call_later(2, self.initialize)

    def _setup_signal_handlers(self):
        """Configure les gestionnaires de signaux DBus"""
        try:
            self.bus.add_signal_receiver(
                self._properties_changed,
                dbus_interface="org.freedesktop.DBus.Properties",
                signal_name="PropertiesChanged",
                path_keyword="path"
            )
        except Exception as e:
            print(f"Erreur configuration signaux: {e}")

    def _properties_changed(self, interface, changed, invalidated, path=None):
        """Gère les changements de propriétés des appareils"""
        if interface != "org.bluez.Device1":
            return

        try:
            if "Connected" in changed:
                is_connected = changed["Connected"]
                if is_connected:
                    self.handle_new_connection(path)
                else:
                    asyncio.create_task(self.handle_disconnection(path))
        except Exception as e:
            print(f"Erreur changement propriétés: {e}")

    def _get_device_info(self, path: str) -> Optional[dict]:
        """Récupère les informations d'un appareil"""
        if not self.initialized:
            return None
            
        try:
            device = self.bus.get_object('org.bluez', path)
            props_iface = dbus.Interface(device, 'org.freedesktop.DBus.Properties')
            props = props_iface.GetAll('org.bluez.Device1')
            
            if not props.get("Connected", False):
                return None
                
            return {
                "address": str(props.get("Address", "")),
                "name": str(props.get("Name", "Unknown")),
                "path": path,
                "timestamp": datetime.now().timestamp()
            }
        except Exception as e:
            print(f"Erreur récupération infos appareil: {e}")
            return None

    async def handle_new_connection(self, device_path: str):
        """Gère une nouvelle connexion"""
        device_info = self._get_device_info(device_path)
        if not device_info:
            return

        if self.active_device:
            if device_info['address'] != self.active_device['address']:
                print(f"Refus connexion (appareil déjà connecté): {device_info['name']}")
                self.disconnect_device(device_path)
                set_a2dp_sink(self.active_device['address'])
        else:
            print(f"Premier appareil connecté: {device_info['name']}")
            self.active_device = device_info
            set_a2dp_sink(device_info['address'])
            # Notifier AudioManager
            if self.audio_manager:
                await self.audio_manager.switch_source(AudioSource.BLUETOOTH)

        await self.notify_devices_status()

    async def handle_disconnection(self, device_path: str):
        """Gère la déconnexion d'un appareil"""
        if self.active_device and self.active_device["path"] == device_path:
            print(f"Appareil actif déconnecté: {self.active_device['name']}")
            self.active_device = None
            # Notifier AudioManager
            if self.audio_manager:
                await self.audio_manager.switch_source(AudioSource.NONE)
            await self.notify_devices_status()

    def _check_existing_connections(self):
        """Vérifie les appareils déjà connectés"""
        try:
            if not self.initialized:
                return

            connected_devices = self._check_bluetoothctl_connections()
            if not connected_devices:
                self.active_device = None
            else:
                # Si un appareil actif existe déjà
                if self.active_device:
                    # Vérifier si l'appareil actif est toujours dans la liste
                    active_still_connected = any(
                        device['address'] == self.active_device['address']
                        for device in connected_devices
                    )
                    
                    if active_still_connected:
                        # Déconnecter tous les autres appareils
                        for device in connected_devices:
                            if device['address'] != self.active_device['address']:
                                print(f"Déconnexion appareil non autorisé: {device['name']}")
                                self.disconnect_device(device['path'])
                        # Restaurer l'audio de l'appareil actif
                        set_a2dp_sink(self.active_device['address'])
                    else:
                        # L'appareil actif n'est plus connecté
                        self.active_device = None
                else:
                    # Pas d'appareil actif, prendre le premier
                    self.active_device = connected_devices[0]
                    # Déconnecter les autres
                    for device in connected_devices[1:]:
                        self.disconnect_device(device['path'])

            asyncio.create_task(self.notify_devices_status())
                
        except Exception as e:
            print(f"Erreur vérification connexions: {e}")

    def _check_bluetoothctl_connections(self) -> List[dict]:
        """Vérifie les connexions via bluetoothctl"""
        try:
            result = subprocess.run(['bluetoothctl', 'devices', 'Connected'], 
                                 capture_output=True, text=True)
            
            if result.returncode != 0:
                return []

            connected_devices = []
            for line in result.stdout.splitlines():
                if "Device" in line:
                    parts = line.split(" ", 2)
                    if len(parts) >= 3:
                        address = parts[1]
                        name = parts[2]
                        path = f"/org/bluez/hci0/dev_{'_'.join(address.split(':'))}"
                        device_info = {
                            "address": address,
                            "name": name,
                            "path": path,
                            "timestamp": datetime.now().timestamp()
                        }
                        connected_devices.append(device_info)
            
            return connected_devices
        except Exception as e:
            print(f"Erreur vérification bluetoothctl: {e}")
            return []

    async def notify_devices_status(self):
        """Envoie l'état au frontend"""
        try:
            message = {
                "type": "devices_status",
                "activeDevice": self.active_device if self.active_device else None,
                "pendingDevice": None  # Plus de pending device
            }
            
            await self.websocket_manager.broadcast_to_service(message, "bluetooth")
            
        except Exception as e:
            print(f"Erreur envoi statut: {e}")

    def disconnect_device(self, device_path: str):
        """Déconnecte un appareil"""
        if not self.initialized:
            return
                
        try:
            # Déconnecter rapidement via bluetoothctl
            device = self.bus.get_object('org.bluez', device_path)
            device_props = dbus.Interface(device, 'org.freedesktop.DBus.Properties')
            address = str(device_props.Get('org.bluez.Device1', 'Address'))
            
            # Déconnexion brutale via bluetoothctl
            subprocess.run(["bluetoothctl", "disconnect", address], check=True)
            
            # Puis déconnexion via DBus
            device_iface = dbus.Interface(device, 'org.bluez.Device1')
            device_iface.Disconnect()
            
            print(f"Appareil déconnecté: {device_path}")
        except Exception as e:
            print(f"Erreur déconnexion: {e}")

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        message_type = message.get("type")
        data = message.get("data", {})

        if message_type == "get_status":
            self._check_existing_connections()
            await self.notify_devices_status()  # Ajout de cette ligne
        elif message_type == "disconnect_device":
            address = data.get("address")
            if address:
                device_path = f"/org/bluez/hci0/dev_{'_'.join(address.split(':'))}"
                self.disconnect_device(device_path)