// backend/services/audioManager.js
const { exec, spawn } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);
const path = require('path');
const fs = require('fs');

class AudioManager {
  constructor() {
    this.services = {
      spotify: null,
      bluetooth: null,
      macos: null
    };
    this.basePath = '/home/leo/go-sonoak/backend';
  }

  async startSpotify() {
    try {
      if (this.services.spotify) {
        console.log('Spotify service already running');
        return;
      }

      console.log('Starting Spotify service...');
      
      const librespotPath = path.join(this.basePath, 'go-librespot');
      console.log('Using go-librespot at:', librespotPath);

      // Vérifier si le fichier existe
      if (!fs.existsSync(librespotPath)) {
        throw new Error(`go-librespot not found at path: ${librespotPath}`);
      }

      // Utiliser spawn au lieu d'exec pour une meilleure gestion du processus
      const process = spawn(librespotPath, [], {
        cwd: this.basePath,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      this.services.spotify = process;

      return new Promise((resolve, reject) => {
        let started = false;

        // Capturer la sortie standard
        process.stdout.on('data', (data) => {
          console.log('Spotify stdout:', data.toString());
        });

        // Capturer les erreurs et vérifier le démarrage
        process.stderr.on('data', (data) => {
          const output = data.toString();
          console.log('Spotify stderr:', output);
          
          // Vérifier si le service est prêt (le message apparaît dans stderr)
          if (output.includes('api server listening')) {
            started = true;
            console.log('Spotify service is ready');
            resolve();
          }
        });

        // Gérer la fin du processus
        process.on('close', (code) => {
          console.log(`Spotify process exited with code ${code}`);
          this.services.spotify = null;
          if (!started) {
            reject(new Error(`Failed to start Spotify process (exit code: ${code})`));
          }
        });

        // Timeout si le service ne démarre pas
        setTimeout(() => {
          if (!started) {
            process.kill();
            reject(new Error('Timeout waiting for Spotify service to start'));
          }
        }, 5000); // 5 secondes de timeout
      });
    } catch (error) {
      console.error('Error starting Spotify:', error);
      // Nettoyage en cas d'erreur
      if (this.services.spotify) {
        this.services.spotify.kill();
        this.services.spotify = null;
      }
      throw error;
    }
  }

  async stopSpotify() {
    try {
      if (this.services.spotify) {
        console.log('Stopping Spotify service...');
        this.services.spotify.kill();
        this.services.spotify = null;
        
        // Attendre que le processus soit bien terminé
        await new Promise(resolve => setTimeout(resolve, 1000));
        console.log('Spotify service stopped');
      }
    } catch (error) {
      console.error('Error stopping Spotify:', error);
      throw error;
    }
  }

  async startBluetooth() {
    try {
      const commands = [
        'sudo rfkill unblock bluetooth',
        'sudo systemctl start bluetooth',
        'pulseaudio --start',
        `bluetoothctl << EOF
power on
discoverable on
pairable on
agent NoInputNoOutput
default-agent
EOF`
      ];

      for (const cmd of commands) {
        await execPromise(cmd).catch(err => {
          if (!err.message.includes("Impossible de tuer le démon")) {
            throw err;
          }
        });
      }
      console.log('Bluetooth service started');
    } catch (error) {
      console.error('Error starting Bluetooth:', error);
      throw error;
    }
  }

  async stopBluetooth() {
    try {
      const commands = [
        'sudo systemctl stop bluetooth',
        'if pulseaudio --check 2>/dev/null; then pulseaudio --kill; fi',
        'sudo rfkill block bluetooth'
      ];

      for (const cmd of commands) {
        await execPromise(cmd).catch(err => {
          if (!err.message.includes("Impossible de tuer le démon")) {
            throw err;
          }
        });
      }
      console.log('Bluetooth service stopped');
    } catch (error) {
      console.error('Error stopping Bluetooth:', error);
      if (!error.message.includes("Impossible de tuer le démon")) {
        throw error;
      }
    }
  }

  async startMacos() {
    try {
      if (this.services.macos) return;
      this.services.macos = exec('snapclient -h 192.168.1.173');
      console.log('MacOS service started');
    } catch (error) {
      console.error('Error starting MacOS:', error);
      throw error;
    }
  }

  async stopMacos() {
    try {
      if (this.services.macos) {
        this.services.macos.kill();
        this.services.macos = null;
        console.log('MacOS service stopped');
      }
    } catch (error) {
      console.error('Error stopping MacOS:', error);
      throw error;
    }
  }

  async getSpotifyStatus() {
    return {
      paused: this.services.spotify === null,
      volume: 75,
      track: {}
    };
  }
}

module.exports = new AudioManager();