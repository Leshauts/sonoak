import dbus
import dbus.mainloop.glib
import asyncio
from typing import List

class BluetoothManager:
    def __init__(self, websocket_manager):
        print("Initialisation du BluetoothManager...")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.websocket_manager = websocket_manager
        self.connected_devices: List[dict] = []
        self.initialized = False
        
        try:
            self.obj_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/"),
                "org.freedesktop.DBus.ObjectManager"
            )
            
            self.adapter_obj = self.bus.get_object('org.bluez', '/org/bluez/hci0')
            self.adapter = dbus.Interface(self.adapter_obj, 'org.bluez.Adapter1')
            print("Adaptateur Bluetooth initialisé")
            self.initialized = True
            
            # Vérification initiale des connexions
            self._check_existing_connections()
        except Exception as e:
            print(f"Erreur d'initialisation: {e}")
            # Même en cas d'erreur, on initialise une liste vide
            self.connected_devices = []

    def _check_existing_connections(self):
        """Vérifie les appareils déjà connectés au démarrage"""
        print("Recherche des appareils connectés...")
        self.connected_devices = []  # Reset la liste
        
        try:
            if not self.initialized:
                print("BluetoothManager non initialisé")
                asyncio.create_task(self.notify_devices_status())
                return

            objects = self.obj_manager.GetManagedObjects()
            for path, interfaces in objects.items():
                if "org.bluez.Device1" not in interfaces:
                    continue
                    
                props = interfaces["org.bluez.Device1"]
                # Vérifie si l'appareil est réellement connecté
                if props.get("Connected", False):
                    print(f"Appareil connecté trouvé: {props.get('Name', 'Unknown')}")
                    device_info = {
                        "address": str(props.get("Address", "")),
                        "name": str(props.get("Name", "Unknown"))
                    }
                    self.connected_devices = [device_info]
                    break  # Un seul appareil à la fois
            
            print(f"Statut actuel des connexions: {self.connected_devices}")
            
        except Exception as e:
            print(f"Erreur lors de la vérification des connexions: {e}")
            # En cas d'erreur, on s'assure que la liste est vide
            self.connected_devices = []
        finally:
            # On envoie toujours une notification, même en cas d'erreur
            asyncio.create_task(self.notify_devices_status())

    async def notify_devices_status(self):
        """Envoie la liste des appareils au frontend"""
        try:
            message = {
                "type": "devices_status",
                "devices": self.connected_devices
            }
            print(f"Envoi du statut: {message}")
            await self.websocket_manager.broadcast_to_service(message, "bluetooth")
        except Exception as e:
            print(f"Erreur lors de l'envoi du statut: {e}")

    def is_device_really_connected(self, device_path: str) -> bool:
        """Vérifie si un appareil est réellement connecté"""
        if not self.initialized:
            return False
            
        try:
            device = self.bus.get_object('org.bluez', device_path)
            props_iface = dbus.Interface(device, 'org.freedesktop.DBus.Properties')
            props = props_iface.GetAll('org.bluez.Device1')
            return bool(props.get("Connected", False))
        except Exception as e:
            print(f"Erreur lors de la vérification de la connexion: {e}")
            return False

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        print(f"[DEBUG] Message WebSocket reçu: {message}")
        message_type = message.get("type")
        data = message.get("data", {})

        if message_type == "get_status":
            print("[DEBUG] Traitement de la demande get_status")
            self._check_existing_connections()
            print("[DEBUG] État des connexions vérifié")
        elif message_type == "disconnect_device":
            address = data.get("address")
            if address:
                device_path = f"/org/bluez/hci0/dev_{'_'.join(address.split(':'))}"
                self.disconnect_device(device_path)

    def add_device(self, device_path: str):
        """Ajoute un nouvel appareil"""
        if not self.initialized:
            return
            
        try:
            # Vérifier si l'appareil est réellement connecté
            if not self.is_device_really_connected(device_path):
                print(f"L'appareil {device_path} n'est pas réellement connecté")
                return

            device = self.bus.get_object('org.bluez', device_path)
            props_iface = dbus.Interface(device, 'org.freedesktop.DBus.Properties')
            props = props_iface.GetAll('org.bluez.Device1')
            
            device_info = {
                "address": str(props.get("Address", "")),
                "name": str(props.get("Name", "Unknown"))
            }
            print(f"Ajout de l'appareil: {device_info['name']}")
            
            # Déconnecter l'appareil précédent si nécessaire
            if len(self.connected_devices) > 0:
                old_address = self.connected_devices[0]['address']
                old_path = f"/org/bluez/hci0/dev_{'_'.join(old_address.split(':'))}"
                print(f"Déconnexion de l'ancien appareil: {self.connected_devices[0]['name']}")
                self.disconnect_device(old_path)
            
            self.connected_devices = [device_info]
            asyncio.create_task(self.notify_devices_status())
                
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'appareil: {e}")
            asyncio.create_task(self.notify_devices_status())

    def remove_device(self, device_path: str):
        """Retire un appareil déconnecté"""
        try:
            if not self.is_device_really_connected(device_path):
                print(f"Appareil déconnecté: {device_path}")
                self.connected_devices = []
                asyncio.create_task(self.notify_devices_status())
        except Exception as e:
            print(f"Erreur lors du retrait de l'appareil: {e}")
            asyncio.create_task(self.notify_devices_status())

    def disconnect_device(self, device_path: str):
        """Déconnecte un appareil"""
        if not self.initialized:
            return
            
        try:
            device = self.bus.get_object('org.bluez', device_path)
            device_iface = dbus.Interface(device, 'org.bluez.Device1')
            device_iface.Disconnect()
            print(f"Appareil déconnecté: {device_path}")
            self.connected_devices = []
        except Exception as e:
            print(f"Erreur lors de la déconnexion: {e}")
        finally:
            asyncio.create_task(self.notify_devices_status())