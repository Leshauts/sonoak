# import lgpio
# import sys

# print("Testing lgpio functionality...")

# try:
#     # Essaie d'ouvrir le chip GPIO
#     h = lgpio.gpiochip_open(0)
#     print(f"Successfully opened GPIO chip: handle={h}")
    
#     # Test de lecture sur quelques pins
#     for pin in [22, 27, 23]:
#         try:
#             lgpio.gpio_claim_input(h, pin, lgpio.SET_PULL_UP)
#             state = lgpio.gpio_read(h, pin)
#             print(f"Pin {pin} state: {state}")
#             lgpio.gpio_free(h, pin)
#         except Exception as e:
#             print(f"Error testing pin {pin}: {e}")
    
#     lgpio.gpiochip_close(h)
#     print("GPIO test completed successfully")
#     sys.exit(0)
    
# except Exception as e:
#     print(f"Error testing lgpio: {e}")
#     sys.exit(1)




















# # test_rotary_alt.py
import lgpio
import time
import sys

def check_gpio_availability(chip_handle, pins):
    """Vérifie si les GPIO sont disponibles"""
    for pin in pins:
        try:
            # Essaie de réclamer le pin brièvement
            lgpio.gpio_claim_input(chip_handle, pin, lgpio.SET_PULL_UP)
            lgpio.gpio_free(chip_handle, pin)
            print(f"GPIO {pin} est disponible")
        except Exception as e:
            print(f"GPIO {pin} n'est pas disponible: {e}")
            return False
    return True

# Pins à utiliser
CLK = 22    # Inchangé
DT = 27     # Inchangé
SW = 23     # Changé de 17 à 23

print(f"Test rotary encoder avec pins: CLK={CLK}, DT={DT}, SW={SW}")
print("Vérification de la disponibilité des GPIO...")

try:
    # Ouvre le chip GPIO
    h = lgpio.gpiochip_open(0)
    print("Chip GPIO ouvert avec succès")
    
    # Vérifie la disponibilité
    PINS = [CLK, DT, SW]
    if check_gpio_availability(h, PINS):
        print("\nTous les GPIO sont disponibles!")
        
        # Configure les pins
        for pin in PINS:
            lgpio.gpio_claim_input(h, pin, lgpio.SET_PULL_UP)
        
        print("\nÉtats initiaux:")
        states = {pin: lgpio.gpio_read(h, pin) for pin in PINS}
        for pin, state in states.items():
            print(f"GPIO {pin}: {state}")
        
        print("\nSurveillance du rotary encoder. Ctrl+C pour quitter...")
        print("- Tournez l'encodeur pour voir les changements")
        print("- Appuyez sur le bouton pour voir l'état du switch")
        
        last_clk = lgpio.gpio_read(h, CLK)
        while True:
            # Vérification de la rotation
            clk_state = lgpio.gpio_read(h, CLK)
            if clk_state != last_clk:
                dt_state = lgpio.gpio_read(h, DT)
                if dt_state != clk_state:
                    print("Rotation horaire →")
                else:
                    print("Rotation anti-horaire ←")
                last_clk = clk_state
            
            # Vérification du bouton
            if lgpio.gpio_read(h, SW) == 0:  # Bouton pressé (actif bas)
                print("Bouton pressé!")
                time.sleep(0.2)  # Debounce
            
            time.sleep(0.001)
            
except KeyboardInterrupt:
    print("\nProgramme arrêté par l'utilisateur")
except Exception as e:
    print(f"\nErreur: {e}")
finally:
    try:
        # Libération des GPIO
        for pin in PINS:
            try:
                lgpio.gpio_free(h, pin)
            except:
                pass
        lgpio.gpiochip_close(h)
        print("GPIO nettoyés et chip fermé")
    except:
        pass