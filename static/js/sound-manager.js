class SoundManager {
    constructor() {
        this.sounds = {};
        this.volume = this.getSavedVolume();
        this.muted = this.getSavedMuteState();
        
        // Ses dosyalarını yükle
        this.loadSounds();
    }
    
    loadSounds() {
        const soundFiles = {
            correct: '/static/sounds/correct.mp3',
            wrong: '/static/sounds/wrong.mp3',
            victory: '/static/sounds/victory.mp3',
            defeat: '/static/sounds/defeat.mp3',
            levelup: '/static/sounds/levelup.mp3',
            badge: '/static/sounds/badge.mp3',
            tick: '/static/sounds/tick.mp3',
            notification: '/static/sounds/notification.mp3',
            countdown: '/static/sounds/countdown.mp3',
            click: '/static/sounds/click.mp3'
        };
        
        for (const [name, path] of Object.entries(soundFiles)) {
            const audio = new Audio(path);
            audio.volume = this.volume;
            audio.preload = 'auto';
            
            // Hata yakalama
            audio.addEventListener('error', () => {
                console.warn(`Ses yüklenemedi: ${name}`);
            });
            
            this.sounds[name] = audio;
        }
        
        console.log('✅ Sesler yüklendi:', Object.keys(this.sounds));
    }
    
    play(soundName, options = {}) {
        if (this.muted) return;
        
        const sound = this.sounds[soundName];
        if (!sound) {
            console.warn(`Ses bulunamadı: ${soundName}`);
            return;
        }
        
        // Ses zaten çalıyorsa baştan başlat
        sound.currentTime = 0;
        
        // Özel ayarlar
        if (options.volume !== undefined) {
            sound.volume = Math.max(0, Math.min(1, options.volume));
        } else {
            sound.volume = this.volume;
        }
        
        if (options.loop) {
            sound.loop = true;
        }
        
        // Çal
        sound.play().catch(err => {
            console.warn('Ses çalma hatası:', err.message);
        });
        
        // Loop değilse bitince sıfırla
        if (!options.loop) {
            sound.addEventListener('ended', () => {
                sound.currentTime = 0;
                sound.loop = false;
            }, { once: true });
        }
    }
    
    stop(soundName) {
        const sound = this.sounds[soundName];
        if (sound) {
            sound.pause();
            sound.currentTime = 0;
            sound.loop = false;
        }
    }
    
    stopAll() {
        Object.values(this.sounds).forEach(sound => {
            sound.pause();
            sound.currentTime = 0;
            sound.loop = false;
        });
    }
    
    setVolume(level) {
        this.volume = Math.max(0, Math.min(1, level));
        Object.values(this.sounds).forEach(sound => {
            sound.volume = this.volume;
        });
        this.saveVolume();
    }
    
    toggleMute() {
        this.muted = !this.muted;
        this.saveMuteState();
        return this.muted;
    }
    
    getSavedVolume() {
        const saved = localStorage.getItem('soundVolume');
        return saved ? parseFloat(saved) : 0.5;
    }
    
    saveVolume() {
        localStorage.setItem('soundVolume', this.volume.toString());
    }
    
    getSavedMuteState() {
        const saved = localStorage.getItem('soundMuted');
        return saved === 'true';
    }
    
    saveMuteState() {
        localStorage.setItem('soundMuted', this.muted.toString());
    }
    
    // Özel efektler
    playSuccess() {
        this.play('correct');
    }
    
    playError() {
        this.play('wrong');
    }
    
    playVictory() {
        this.play('victory');
    }
    
    playDefeat() {
        this.play('defeat');
    }
    
    playLevelUp() {
        this.play('levelup');
    }
    
    playBadge() {
        this.play('badge');
    }
    
    playNotification() {
        this.play('notification');
    }
    
    playClick() {
        this.play('click', { volume: 0.3 });
    }
    
    // Geri sayım için özel fonksiyon
    playCountdown() {
        this.play('countdown', { loop: true });
    }
    
    stopCountdown() {
        this.stop('countdown');
    }
    
    playTick() {
        this.play('tick', { volume: 0.4 });
    }
}

// Global instance
window.soundManager = new SoundManager();