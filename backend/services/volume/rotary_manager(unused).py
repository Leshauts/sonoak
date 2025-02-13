import lgpio
import asyncio
import logging

logger = logging.getLogger(__name__)

class RotaryVolumeManager:
    def __init__(self, volume_manager, clk_pin: int = 22, dt_pin: int = 27, sw_pin: int = 23):
        self.volume_manager = volume_manager
        self.is_running = False
        
        # Ouvre le chip GPIO
        self.chip_handle = lgpio.gpiochip_open(0)

        # Configure les GPIO en entrée avec pull-up
        lgpio.gpio_claim_input(self.chip_handle, clk_pin, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self.chip_handle, dt_pin, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(self.chip_handle, sw_pin, lgpio.SET_PULL_UP)

        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.last_clk_state = lgpio.gpio_read(self.chip_handle, self.clk_pin)

    async def start_monitoring(self):
        """Surveille le rotary encoder et ajuste le volume"""
        self.is_running = True
        logger.info("Démarrage du monitoring du rotary encoder")
        
        try:
            while self.is_running:
                clk_state = lgpio.gpio_read(self.chip_handle, self.clk_pin)
                dt_state = lgpio.gpio_read(self.chip_handle, self.dt_pin)
                
                if clk_state != self.last_clk_state:  # Détection de rotation
                    if dt_state != clk_state:
                        logger.info("→ Rotation horaire - Augmenter volume")
                        await self.volume_manager.adjust_volume(2)
                    else:
                        logger.info("← Rotation anti-horaire - Diminuer volume")
                        await self.volume_manager.adjust_volume(-2)

                    self.last_clk_state = clk_state  # Mettre à jour l'état précédent

                # Vérifier si le bouton est pressé
                if lgpio.gpio_read(self.chip_handle, self.sw_pin) == 0:
                    logger.info("🔘 Bouton pressé!")
                    await self.volume_manager.set_volume(50)  # Exemple : reset à 50%

                await asyncio.sleep(0.005)  # Petite pause pour éviter surcharge CPU
                
        except Exception as e:
            logger.error(f"Erreur dans le monitoring du rotary: {e}", exc_info=True)
        finally:
            self.cleanup()

    def cleanup(self):
        """Libère les GPIO"""
        logger.info("Nettoyage des GPIO du rotary encoder")
        lgpio.gpio_free(self.chip_handle, self.clk_pin)
        lgpio.gpio_free(self.chip_handle, self.dt_pin)
        lgpio.gpio_free(self.chip_handle, self.sw_pin)
        lgpio.gpiochip_close(self.chip_handle)