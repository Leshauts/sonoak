# backend/services/bluetooth/manager.py
import dbus
import dbus.mainloop.glib
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

class BluetoothManager:
    def __init__(self, websocket_manager):
        print("Initialisation du BluetoothManager...")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.websocket_manager = websocket_manager
        self.active_device: Optional[dict] = None
        self.pending_device: Optional[dict] = None
        self.initialized = False
        self.last_active_address = None  # Pour suivre le dernier appareil actif
        
        try:
            self.obj_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/"),
                "org.freedesktop.DBus.ObjectManager"
            )
            
            self.adapter_obj = self.bus.get_object('org.bluez', '/org/bluez/hci0')
            self.adapter = dbus.Interface(self.adapter_obj, 'org.bluez.Adapter1')
            print("Adaptateur Bluetooth initialisé")
            self.initialized = True
            
            self._setup_signal_handlers()
            self._check_existing_connections()
        except Exception as e:
            print(f"Erreur d'initialisation: {e}")
            self.active_device = None
            self.pending_device = None

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
            print(f"Erreur lors de la récupération des infos de l'appareil: {e}")
            return None

    def handle_new_connection(self, device_path: str):
            """Gère une nouvelle connexion"""
            print(f"Nouvelle connexion détectée: {device_path}")
            device_info = self._get_device_info(device_path)
            if not device_info:
                return

            print(f"Infos appareil: {device_info}")
            print(f"État actuel - Actif: {self.active_device}, En attente: {self.pending_device}")

            # Si c'est le premier appareil à se connecter
            if not self.active_device:
                print(f"Premier appareil - devient actif: {device_info['name']}")
                self.active_device = device_info
            else:
                # Si ce n'est pas l'appareil actif qui se reconnecte
                if device_info['address'] != self.active_device['address']:
                    print(f"Nouvel appareil détecté - devient pending: {device_info['name']}")
                    self.pending_device = device_info

            print(f"Nouvel état - Actif: {self.active_device}, En attente: {self.pending_device}")
            asyncio.create_task(self.notify_devices_status())

    def handle_disconnection(self, device_path: str):
        """Gère une déconnexion"""
        print(f"Déconnexion détectée: {device_path}")
        need_update = False
        
        # Obtenir l'adresse de l'appareil déconnecté
        try:
            device = self.bus.get_object('org.bluez', device_path)
            props_iface = dbus.Interface(device, 'org.freedesktop.DBus.Properties')
            props = props_iface.GetAll('org.bluez.Device1')
            disconnected_address = str(props.get("Address", ""))
        except:
            disconnected_address = None

        if self.active_device and (self.active_device["path"] == device_path or 
                                 (disconnected_address and self.active_device["address"] == disconnected_address)):
            print(f"Appareil actif déconnecté: {self.active_device['name']}")
            self.active_device = None
            need_update = True
            
        if self.pending_device and (self.pending_device["path"] == device_path or 
                                  (disconnected_address and self.pending_device["address"] == disconnected_address)):
            print(f"Appareil en attente déconnecté: {self.pending_device['name']}")
            self.pending_device = None
            need_update = True

        if need_update:
            # Forcer une vérification complète des connexions
            self._check_existing_connections()
        else:
            asyncio.create_task(self.notify_devices_status())

    async def switch_devices(self, old_address: str, new_address: str):
        """Gère le changement d'appareil actif"""
        print(f"Changement d'appareil: {old_address} -> {new_address}")
        
        if (self.active_device and self.active_device['address'] == old_address and 
            self.pending_device and self.pending_device['address'] == new_address):
            
            # Déconnecter l'ancien appareil
            old_path = f"/org/bluez/hci0/dev_{'_'.join(old_address.split(':'))}"
            self.disconnect_device(old_path)
            
            # Mettre à jour l'état immédiatement
            self.active_device = self.pending_device
            self.pending_device = None
            
            # Notifier le frontend
            await self.notify_devices_status()
        else:
            print("État des appareils incorrect pour le changement")
            # Forcer une vérification complète
            self._check_existing_connections()

    def _check_existing_connections(self):
        """Vérifie les appareils déjà connectés au démarrage"""
        print("Recherche des appareils connectés...")
        
        try:
            if not self.initialized:
                print("BluetoothManager non initialisé")
                asyncio.create_task(self.notify_devices_status())
                return

            objects = self.obj_manager.GetManagedObjects()
            connected_devices = []
            
            for path, interfaces in objects.items():
                if "org.bluez.Device1" not in interfaces:
                    continue
                    
                device_info = self._get_device_info(path)
                if device_info:
                    connected_devices.append(device_info)
            
            print(f"Appareils connectés trouvés: {connected_devices}")
            
            # Conservation de l'appareil actif s'il existe toujours
            if self.active_device:
                active_still_exists = any(
                    device['address'] == self.active_device['address'] 
                    for device in connected_devices
                )
                if not active_still_exists:
                    self.active_device = None

            # S'il n'y a pas d'appareil actif, prendre le premier appareil connecté
            if not self.active_device and connected_devices:
                self.active_device = connected_devices[0]
                
            # Pour le pending device, prendre le dernier appareil connecté
            # qui n'est pas l'appareil actif
            self.pending_device = None
            if len(connected_devices) > 1:
                for device in reversed(connected_devices):
                    if not self.active_device or device['address'] != self.active_device['address']:
                        self.pending_device = device
                        break
            
            print(f"État après vérification - Actif: {self.active_device}, En attente: {self.pending_device}")
            
        except Exception as e:
            print(f"Erreur lors de la vérification des connexions: {e}")
            self.active_device = None
            self.pending_device = None
        finally:
            asyncio.create_task(self.notify_devices_status())

    async def notify_devices_status(self):
        """Envoie la liste des appareils au frontend"""
        try:
            # Vérification que les appareils sont toujours connectés
            active_still_connected = (
                self.active_device and 
                self.is_device_really_connected(self.active_device['path'])
            )
            
            pending_still_connected = (
                self.pending_device and 
                self.is_device_really_connected(self.pending_device['path'])
            )
            
            # Ne jamais échanger automatiquement les appareils
            message = {
                "type": "devices_status",
                "activeDevice": self.active_device if active_still_connected else None,
                "pendingDevice": self.pending_device if pending_still_connected else None
            }
            
            print(f"[DEBUG] Envoi du statut Bluetooth:")
            print(f"  - Actif: {self.active_device['name'] if self.active_device else 'None'}")
            print(f"  - En attente: {self.pending_device['name'] if self.pending_device else 'None'}")
            
            await self.websocket_manager.broadcast_to_service(message, "bluetooth")
            
        except Exception as e:
            print(f"Erreur lors de l'envoi du statut: {e}")
            self._check_existing_connections()


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
            return False

    async def handle_message(self, message: dict):
        """Gère les messages du frontend"""
        print(f"[DEBUG] Message WebSocket reçu: {message}")
        message_type = message.get("type")
        data = message.get("data", {})

        if message_type == "get_status":
            print("[DEBUG] Traitement de la demande get_status")
            self._check_existing_connections()
        elif message_type == "disconnect_device":
            address = data.get("address")
            if address:
                device_path = f"/org/bluez/hci0/dev_{'_'.join(address.split(':'))}"
                self.disconnect_device(device_path)
        elif message_type == "switch_device":
            old_address = data.get("oldDeviceAddress")
            new_address = data.get("newDeviceAddress")
            if old_address and new_address:
                await self.switch_devices(old_address, new_address)

    def disconnect_device(self, device_path: str):
        """Déconnecte un appareil"""
        if not self.initialized:
            return
            
        try:
            device = self.bus.get_object('org.bluez', device_path)
            device_iface = dbus.Interface(device, 'org.bluez.Device1')
            device_iface.Disconnect()
            print(f"Appareil déconnecté: {device_path}")
        except Exception as e:
            print(f"Erreur lors de la déconnexion: {e}")