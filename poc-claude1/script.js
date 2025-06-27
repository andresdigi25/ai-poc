class ASCIIArtMusicCanvas {
    constructor() {
        this.canvas = document.getElementById('asciiCanvas');
        this.patternBtn = document.getElementById('patternBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.volumeSlider = document.getElementById('volumeSlider');
        
        this.isDrawing = false;
        this.currentPatternIndex = 0;
        this.audioContext = null;
        this.masterGain = null;
        
        this.patterns = [
            {
                name: 'Stars',
                emoji: '✨',
                chars: ['★', '☆', '✦', '✧', '✩', '✪', '✫', '✬'],
                colors: ['#FFD700', '#FFA500', '#FF69B4', '#9370DB', '#00CED1', '#32CD32', '#FF6347', '#DDA0DD'],
                scale: [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25] // C4 to C5
            },
            {
                name: 'Hearts',
                emoji: '💖',
                chars: ['♥', '♡', '💖', '💝', '💕', '💗', '💓', '💘'],
                colors: ['#FF1493', '#FF69B4', '#FFB6C1', '#FFC0CB', '#FF91A4', '#FF1493', '#DC143C', '#B22222'],
                scale: [220.00, 246.94, 277.18, 293.66, 329.63, 369.99, 415.30, 440.00] // A3 to A4
            },
            {
                name: 'Nature',
                emoji: '🌿',
                chars: ['🌸', '🌺', '🌻', '🌹', '🌷', '🌿', '🍃', '🌳'],
                colors: ['#FF69B4', '#FF1493', '#FFD700', '#FF0000', '#FF69B4', '#32CD32', '#228B22', '#006400'],
                scale: [174.61, 196.00, 220.00, 233.08, 261.63, 293.66, 329.63, 349.23] // F3 to F4
            },
            {
                name: 'Symbols',
                emoji: '⚡',
                chars: ['⚡', '⭐', '💫', '🔥', '💎', '🌟', '✨', '💥'],
                colors: ['#FFFF00', '#FFD700', '#E6E6FA', '#FF4500', '#00BFFF', '#FFD700', '#FFA500', '#FF6347'],
                scale: [130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94, 261.63] // C3 to C4
            },
            {
                name: 'Geometric',
                emoji: '🔷',
                chars: ['◆', '◇', '■', '□', '●', '○', '▲', '△'],
                colors: ['#0066CC', '#66B2FF', '#800080', '#DDA0DD', '#FF4500', '#FFA500', '#008000', '#90EE90'],
                scale: [329.63, 369.99, 415.30, 440.00, 493.88, 554.37, 622.25, 659.25] // E4 to E5
            }
        ];
        
        this.init();
    }
    
    async init() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.masterGain = this.audioContext.createGain();
            this.masterGain.connect(this.audioContext.destination);
            this.masterGain.gain.setValueAtTime(0.5, this.audioContext.currentTime);
        } catch (error) {
            console.warn('Web Audio API not supported:', error);
        }
        
        this.setupEventListeners();
        this.updatePatternButton();
    }
    
    setupEventListeners() {
        // Mouse events
        this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.canvas.addEventListener('mousemove', (e) => this.draw(e));
        this.canvas.addEventListener('mouseup', () => this.stopDrawing());
        this.canvas.addEventListener('mouseleave', () => this.stopDrawing());
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startDrawing(e.touches[0]);
        });
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            this.draw(e.touches[0]);
        });
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopDrawing();
        });
        
        // Button events
        this.patternBtn.addEventListener('click', () => this.switchPattern());
        this.clearBtn.addEventListener('click', () => this.clearCanvas());
        
        // Volume control
        this.volumeSlider.addEventListener('input', (e) => {
            if (this.masterGain) {
                this.masterGain.gain.setValueAtTime(e.target.value / 100, this.audioContext.currentTime);
            }
        });
        
        // Resume audio context on user interaction
        document.addEventListener('click', () => {
            if (this.audioContext && this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
        });
    }
    
    startDrawing(e) {
        this.isDrawing = true;
        this.draw(e);
    }
    
    draw(e) {
        if (!this.isDrawing) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Throttle drawing to prevent too many characters
        if (!this.lastDrawTime || Date.now() - this.lastDrawTime > 100) {
            this.placeCharacter(x, y);
            this.lastDrawTime = Date.now();
        }
    }
    
    stopDrawing() {
        this.isDrawing = false;
    }
    
    placeCharacter(x, y) {
        const pattern = this.patterns[this.currentPatternIndex];
        const charIndex = Math.floor(Math.random() * pattern.chars.length);
        const char = pattern.chars[charIndex];
        const color = pattern.colors[charIndex];
        const frequency = pattern.scale[charIndex];
        
        // Create character element
        const charElement = document.createElement('div');
        charElement.className = 'ascii-char';
        charElement.textContent = char;
        charElement.style.left = x + 'px';
        charElement.style.top = y + 'px';
        charElement.style.color = color;
        
        // Add random offset for more natural placement
        const offsetX = (Math.random() - 0.5) * 20;
        const offsetY = (Math.random() - 0.5) * 20;
        charElement.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        
        this.canvas.appendChild(charElement);
        
        // Play sound
        this.playNote(frequency);
        
        // Remove old characters if too many (performance)
        const chars = this.canvas.querySelectorAll('.ascii-char');
        if (chars.length > 200) {
            chars[0].remove();
        }
    }
    
    playNote(frequency) {
        if (!this.audioContext) return;
        
        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.masterGain);
            
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
            
            // Create envelope for pleasant sound
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.3, this.audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.5);
            
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + 0.5);
            
            // Add some harmonic richness
            const harmonicOsc = this.audioContext.createOscillator();
            const harmonicGain = this.audioContext.createGain();
            
            harmonicOsc.connect(harmonicGain);
            harmonicGain.connect(this.masterGain);
            
            harmonicOsc.type = 'triangle';
            harmonicOsc.frequency.setValueAtTime(frequency * 2, this.audioContext.currentTime);
            
            harmonicGain.gain.setValueAtTime(0, this.audioContext.currentTime);
            harmonicGain.gain.linearRampToValueAtTime(0.1, this.audioContext.currentTime + 0.01);
            harmonicGain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
            
            harmonicOsc.start(this.audioContext.currentTime);
            harmonicOsc.stop(this.audioContext.currentTime + 0.3);
            
        } catch (error) {
            console.warn('Error playing note:', error);
        }
    }
    
    switchPattern() {
        this.currentPatternIndex = (this.currentPatternIndex + 1) % this.patterns.length;
        this.updatePatternButton();
    }
    
    updatePatternButton() {
        const pattern = this.patterns[this.currentPatternIndex];
        this.patternBtn.textContent = `Pattern: ${pattern.name} ${pattern.emoji}`;
    }
    
    clearCanvas() {
        const chars = this.canvas.querySelectorAll('.ascii-char');
        chars.forEach(char => {
            char.style.animation = 'charAppear 0.3s ease-out reverse';
            setTimeout(() => char.remove(), 300);
        });
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new ASCIIArtMusicCanvas();
});