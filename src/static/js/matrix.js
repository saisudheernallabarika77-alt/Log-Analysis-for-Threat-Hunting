/**
 * Matrix Rain Animation
 * Creates the iconic falling green characters background
 */
(function() {
    const canvas = document.getElementById('matrixCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);
    
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%^&*()_+-=[]{}|;:<>?/~`アイウエオカキクケコサシスセソタチツテト';
    const fontSize = 14;
    let columns = Math.floor(canvas.width / fontSize);
    let drops = Array(columns).fill(1);
    
    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.08)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.font = fontSize + 'px monospace';
        
        for (let i = 0; i < drops.length; i++) {
            // Skip ~40% of columns each frame to reduce density
            if (Math.random() < 0.4) {
                drops[i]++;
                continue;
            }
            const char = chars[Math.floor(Math.random() * chars.length)];
            const x = i * fontSize;
            const y = drops[i] * fontSize;
            
            // Dimmer tones
            const brightness = Math.random();
            if (brightness > 0.97) {
                ctx.fillStyle = '#aaffaa';
            } else if (brightness > 0.85) {
                ctx.fillStyle = '#00aa00';
            } else {
                ctx.fillStyle = '#006600';
            }
            
            ctx.fillText(char, x, y);
            
            if (y > canvas.height && Math.random() > 0.985) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }
    
    setInterval(draw, 70);
    
    // Re-init on resize
    window.addEventListener('resize', function() {
        columns = Math.floor(canvas.width / fontSize);
        drops = Array(columns).fill(1);
    });
})();
