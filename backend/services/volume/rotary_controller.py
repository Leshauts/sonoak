# backend/services/volume/rotary_controller.py
import lgpio
import asyncio
import logging
from typing import Optional
from time import monotonic

logger = logging.getLogger(__name__)

class RotaryVolumeController:
    def __init__(self, volume_manager, clk_pin=22, dt_pin=27, sw_pin=23):
        self.volume_manager = volume_manager
        self.CLK = clk_pin
        self.DT = dt_pin
        self.SW = sw_pin
        self.chip_handle: Optional[int] = None
        self.last_clk = 0
        self.running = False
        self._last_adjustment_time = 0
        
        # Configuration du rotary
        self.DEBOUNCE_TIME = 0.05  # 50ms debounce
        self.ROTARY_SENSITIVITY = 3  # Changement de volume par step de rotation
        self.rotation_accumulator = 0
        self.is_processing = False
        self.PROCESS_INTERVAL = 0.05  # 50ms entre les traitements
        self._last_volume_update = 0
        self.MIN_UPDATE_INTERVAL = 0.1  # Temps minimum entre deux mises à jour de volume

    async def initialize(self):
        """Initialize the rotary encoder"""
        try:
            logger.info(f"Initializing rotary encoder (CLK={self.CLK}, DT={self.DT}, SW={self.SW})")
            self.chip_handle = lgpio.gpiochip_open(0)
            
            # Configure les pins
            for pin in [self.CLK, self.DT, self.SW]:
                lgpio.gpio_claim_input(self.chip_handle, pin, lgpio.SET_PULL_UP)
            
            self.last_clk = lgpio.gpio_read(self.chip_handle, self.CLK)
            self.running = True
            
            # Démarrer les boucles de surveillance
            asyncio.create_task(self._monitor_loop())
            asyncio.create_task(self._process_rotations_loop())
            logger.info("Rotary encoder initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize rotary encoder: {e}")
            self.cleanup()
            raise

    async def _monitor_loop(self):
        """Boucle principale de surveillance du rotary encoder"""
        logger.info("Starting rotary encoder monitoring loop")
        
        while self.running:
            try:
                await self._check_rotation()
                await self._check_button()
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1)

    async def _process_rotations_loop(self):
        """Boucle de traitement des rotations accumulées"""
        last_process_time = monotonic()
        
        while self.running:
            try:
                current_time = monotonic()
                if (current_time - last_process_time >= self.PROCESS_INTERVAL 
                    and self.rotation_accumulator != 0 
                    and not self.is_processing
                    and current_time - self._last_volume_update >= self.MIN_UPDATE_INTERVAL):
                    
                    self.is_processing = True
                    
                    # Calculer le changement de volume
                    volume_change = self.rotation_accumulator * self.ROTARY_SENSITIVITY
                    self.rotation_accumulator = 0
                    last_process_time = current_time
                    
                    # Appliquer directement le changement de volume
                    current_volume = await self.volume_manager.get_volume()
                    new_volume = max(0, min(100, current_volume + volume_change))
                    
                    # Mise à jour du volume uniquement si changement
                    if new_volume != current_volume:
                        await self.volume_manager.set_volume(new_volume)
                        self._last_volume_update = current_time
                    
                    self.is_processing = False
                
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in process rotations loop: {e}")
                self.is_processing = False
                await asyncio.sleep(0.1)

    async def _check_rotation(self):
        """Vérifie et accumule la rotation de l'encodeur"""
        clk_state = lgpio.gpio_read(self.chip_handle, self.CLK)
        
        if clk_state != self.last_clk:
            current_time = monotonic()
            if current_time - self._last_adjustment_time >= self.DEBOUNCE_TIME:
                dt_state = lgpio.gpio_read(self.chip_handle, self.DT)
                
                if dt_state != clk_state:
                    logger.debug("Rotation horaire →")
                    self.rotation_accumulator += 1
                else:
                    logger.debug("Rotation anti-horaire ←")
                    self.rotation_accumulator -= 1
                
                self._last_adjustment_time = current_time
            
            self.last_clk = clk_state

    async def _check_button(self):
        """Vérifie et traite l'appui sur le bouton"""
        if lgpio.gpio_read(self.chip_handle, self.SW) == 0:
            current_time = monotonic()
            if current_time - self._last_adjustment_time >= self.DEBOUNCE_TIME:
                logger.debug("Bouton pressé")
                # Vous pouvez ajouter une action pour le bouton ici
                self._last_adjustment_time = current_time
            await asyncio.sleep(0.2)

    def cleanup(self):
        """Nettoie les ressources GPIO"""
        logger.info("Cleaning up rotary encoder resources")
        self.running = False
        
        if self.chip_handle is not None:
            try:
                for pin in [self.CLK, self.DT, self.SW]:
                    try:
                        lgpio.gpio_free(self.chip_handle, pin)
                    except:
                        pass
                lgpio.gpiochip_close(self.chip_handle)
                logger.info("GPIO cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")