/**
 * CyberSecure Sound Effects Engine
 * All sounds generated via Web Audio API - no external files needed.
 */
const CyberSound = (function () {
    let ctx = null;

    function getCtx() {
        if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
        if (ctx.state === 'suspended') ctx.resume();
        return ctx;
    }

    /* ─── Utility ─── */
    function osc(type, freq, start, dur, gain, destination) {
        const c = getCtx();
        const o = c.createOscillator();
        const g = c.createGain();
        o.type = type;
        o.frequency.setValueAtTime(freq, start);
        g.gain.setValueAtTime(gain, start);
        g.gain.exponentialRampToValueAtTime(0.001, start + dur);
        o.connect(g);
        g.connect(destination || c.destination);
        o.start(start);
        o.stop(start + dur);
    }

    function noise(dur, gainVal, start) {
        const c = getCtx();
        const len = c.sampleRate * dur;
        const buf = c.createBuffer(1, len, c.sampleRate);
        const data = buf.getChannelData(0);
        for (let i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * 0.3;
        const src = c.createBufferSource();
        src.buffer = buf;
        const g = c.createGain();
        const f = c.createBiquadFilter();
        f.type = 'bandpass';
        f.frequency.value = 4000;
        f.Q.value = 0.8;
        g.gain.setValueAtTime(gainVal, start);
        g.gain.exponentialRampToValueAtTime(0.001, start + dur);
        src.connect(f);
        f.connect(g);
        g.connect(c.destination);
        src.start(start);
        src.stop(start + dur);
    }

    /* ══════════════════════════════════════
       1. BUTTON CLICK — short cyber "pip"
       ══════════════════════════════════════ */
    function click() {
        const c = getCtx();
        const t = c.currentTime;
        osc('square', 1800, t, 0.04, 0.12);
        osc('sine', 2400, t + 0.01, 0.03, 0.08);
    }

    /* ══════════════════════════════════════
       2. HOVER — very subtle tick
       ══════════════════════════════════════ */
    function hover() {
        const c = getCtx();
        osc('sine', 3200, c.currentTime, 0.02, 0.04);
    }

    /* ══════════════════════════════════════
       3. SPLASH / BOOT SCAN SEQUENCE
       Full 5-second cinematic cyber loading
       ══════════════════════════════════════ */
    function bootScan() {
        const c = getCtx();
        const t = c.currentTime;

        /* Phase 1 (0-1.5s): Power-up — deep rumble rising */
        const pw = c.createOscillator();
        const pwG = c.createGain();
        pw.type = 'sawtooth';
        pw.frequency.setValueAtTime(35, t);
        pw.frequency.exponentialRampToValueAtTime(180, t + 1.5);
        pwG.gain.setValueAtTime(0.001, t);
        pwG.gain.linearRampToValueAtTime(0.14, t + 0.8);
        pwG.gain.exponentialRampToValueAtTime(0.001, t + 1.8);
        pw.connect(pwG); pwG.connect(c.destination);
        pw.start(t); pw.stop(t + 1.8);

        // Sub-bass thud
        osc('sine', 45, t + 0.05, 0.6, 0.12);

        /* Phase 2 (0.5-2.5s): Scanning sweep — rising freq */
        const sw = c.createOscillator();
        const swG = c.createGain();
        sw.type = 'sine';
        sw.frequency.setValueAtTime(200, t + 0.5);
        sw.frequency.exponentialRampToValueAtTime(4000, t + 2.5);
        swG.gain.setValueAtTime(0.07, t + 0.5);
        swG.gain.exponentialRampToValueAtTime(0.001, t + 2.8);
        sw.connect(swG); swG.connect(c.destination);
        sw.start(t + 0.5); sw.stop(t + 2.8);

        // Reverse sweep underneath
        const sw2 = c.createOscillator();
        const sw2G = c.createGain();
        sw2.type = 'triangle';
        sw2.frequency.setValueAtTime(3000, t + 0.8);
        sw2.frequency.exponentialRampToValueAtTime(150, t + 2.3);
        sw2G.gain.setValueAtTime(0.04, t + 0.8);
        sw2G.gain.exponentialRampToValueAtTime(0.001, t + 2.5);
        sw2.connect(sw2G); sw2G.connect(c.destination);
        sw2.start(t + 0.8); sw2.stop(t + 2.5);

        /* Phase 3 (1.0-3.2s): Digital data stream — rapid beeps */
        const dataFreqs = [700, 1100, 950, 1300, 800, 1500, 1050, 1700, 900, 1400, 1200, 1800, 1000, 1600];
        dataFreqs.forEach((f, i) => {
            osc('square', f, t + 1.0 + i * 0.15, 0.06, 0.05);
        });

        /* Phase 4 (0.4-3.0s): Noise — scanning hiss layers */
        noise(2.5, 0.06, t + 0.4);
        noise(1.0, 0.04, t + 2.0);

        /* Phase 5 (2.5-3.5s): System analysis pulses */
        [660, 880, 660, 1100, 880].forEach((f, i) => {
            osc('sine', f, t + 2.5 + i * 0.2, 0.12, 0.08);
        });

        /* Phase 6 (3.0-4.0s): Encryption lock sequence */
        const enc = c.createOscillator();
        const encG = c.createGain();
        enc.type = 'square';
        enc.frequency.setValueAtTime(120, t + 3.0);
        enc.frequency.setValueAtTime(240, t + 3.2);
        enc.frequency.setValueAtTime(120, t + 3.4);
        enc.frequency.setValueAtTime(360, t + 3.6);
        encG.gain.setValueAtTime(0.06, t + 3.0);
        encG.gain.exponentialRampToValueAtTime(0.001, t + 4.0);
        enc.connect(encG); encG.connect(c.destination);
        enc.start(t + 3.0); enc.stop(t + 4.0);

        /* Phase 7 (3.5-4.2s): Firewall load — metallic tones */
        osc('sawtooth', 500, t + 3.5, 0.1, 0.06);
        osc('sawtooth', 750, t + 3.65, 0.1, 0.06);
        osc('sawtooth', 1000, t + 3.8, 0.12, 0.07);

        /* Phase 8 (4.2-5.0s): SYSTEM READY — triumphant chime */
        osc('sine', 880, t + 4.2, 0.18, 0.12);
        osc('sine', 1320, t + 4.35, 0.18, 0.12);
        osc('sine', 1760, t + 4.5, 0.35, 0.15);
        // Harmonic overtone
        osc('sine', 2640, t + 4.55, 0.3, 0.06);
        // Final sub confirmation pulse
        osc('sine', 110, t + 4.5, 0.5, 0.08);
    }

    /* ══════════════════════════════════════
       4. LOGIN SUCCESS — ascending confirm
       ══════════════════════════════════════ */
    function loginSuccess() {
        const c = getCtx();
        const t = c.currentTime;
        osc('sine', 660, t, 0.12, 0.12);
        osc('sine', 880, t + 0.1, 0.12, 0.12);
        osc('sine', 1320, t + 0.2, 0.25, 0.14);
    }

    /* ══════════════════════════════════════
       5. LOGIN FAILED — descending warning
       ══════════════════════════════════════ */
    function loginFailed() {
        const c = getCtx();
        const t = c.currentTime;
        osc('sawtooth', 400, t, 0.15, 0.1);
        osc('sawtooth', 250, t + 0.15, 0.25, 0.12);
        osc('square', 150, t + 0.35, 0.2, 0.06);
    }

    /* ══════════════════════════════════════
       6. NOTIFICATION ALERT — security beep
       ══════════════════════════════════════ */
    function notification() {
        const c = getCtx();
        const t = c.currentTime;
        for (let i = 0; i < 3; i++) {
            osc('sine', 1200, t + i * 0.18, 0.08, 0.1);
            osc('sine', 1800, t + i * 0.18 + 0.04, 0.06, 0.06);
        }
    }

    /* ══════════════════════════════════════
       7. LOCKOUT ALARM — pulsing red alert
       ══════════════════════════════════════ */
    function lockoutAlarm() {
        const c = getCtx();
        const t = c.currentTime;
        // 3 descending alarm bursts
        for (let i = 0; i < 3; i++) {
            const s = t + i * 0.4;
            osc('sawtooth', 600, s, 0.12, 0.12);
            osc('sawtooth', 350, s + 0.1, 0.2, 0.1);
        }
        // Low rumble
        osc('sine', 80, t, 1.4, 0.08);
    }

    /* ══════════════════════════════════════
       8. SQL INJECTION SIREN — loud alarm
       Full emergency siren effect
       ══════════════════════════════════════ */
    let sirenInterval = null;
    function sirenStart() {
        const c = getCtx();

        // Initial impact boom
        const t = c.currentTime;
        osc('sawtooth', 100, t, 0.5, 0.2);
        noise(0.3, 0.15, t);

        // Repeating siren wail
        let cycle = 0;
        sirenInterval = setInterval(() => {
            if (cycle >= 12) { sirenStop(); return; }
            const now = c.currentTime;

            // Wailing siren sweep up-down
            const o = c.createOscillator();
            const g = c.createGain();
            o.type = 'sawtooth';
            o.frequency.setValueAtTime(400, now);
            o.frequency.linearRampToValueAtTime(900, now + 0.35);
            o.frequency.linearRampToValueAtTime(400, now + 0.7);
            g.gain.setValueAtTime(0.15, now);
            g.gain.setValueAtTime(0.15, now + 0.5);
            g.gain.exponentialRampToValueAtTime(0.001, now + 0.75);
            o.connect(g); g.connect(c.destination);
            o.start(now); o.stop(now + 0.75);

            // Higher overtone for harsh alarm
            const o2 = c.createOscillator();
            const g2 = c.createGain();
            o2.type = 'square';
            o2.frequency.setValueAtTime(800, now);
            o2.frequency.linearRampToValueAtTime(1600, now + 0.35);
            o2.frequency.linearRampToValueAtTime(800, now + 0.7);
            g2.gain.setValueAtTime(0.06, now);
            g2.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
            o2.connect(g2); g2.connect(c.destination);
            o2.start(now); o2.stop(now + 0.75);

            cycle++;
        }, 750);
    }
    function sirenStop() {
        if (sirenInterval) { clearInterval(sirenInterval); sirenInterval = null; }
    }

    /* ══════════════════════════════════════
       9. PAGE TRANSITION — short whoosh
       ══════════════════════════════════════ */
    function transition() {
        const c = getCtx();
        const t = c.currentTime;
        const o = c.createOscillator();
        const g = c.createGain();
        o.type = 'sine';
        o.frequency.setValueAtTime(400, t);
        o.frequency.exponentialRampToValueAtTime(2000, t + 0.15);
        g.gain.setValueAtTime(0.08, t);
        g.gain.exponentialRampToValueAtTime(0.001, t + 0.2);
        o.connect(g); g.connect(c.destination);
        o.start(t); o.stop(t + 0.2);
        noise(0.12, 0.04, t);
    }

    /* ══════════════════════════════════════
       10. TYPING BEEP — for form interactions
       ══════════════════════════════════════ */
    function type() {
        const c = getCtx();
        osc('sine', 2800 + Math.random() * 400, c.currentTime, 0.015, 0.03);
    }

    /* ══════════════════════════════════════
       11. GATE AMBIENT — looping cyber hum
       with radar pings & data blips
       ══════════════════════════════════════ */
    let ambientInterval = null;
    let ambientNodes = [];

    function gateAmbient() {
        const c = getCtx();
        const t = c.currentTime;

        // Layer 1: Deep sub-bass drone
        const drone = c.createOscillator();
        const droneG = c.createGain();
        drone.type = 'sine';
        drone.frequency.setValueAtTime(55, t);
        droneG.gain.setValueAtTime(0.06, t);
        drone.connect(droneG); droneG.connect(c.destination);
        drone.start(t);
        ambientNodes.push(drone, droneG);

        // Layer 2: Mid-range pulsing hum
        const hum = c.createOscillator();
        const humG = c.createGain();
        const humLFO = c.createOscillator();
        const humLFOG = c.createGain();
        hum.type = 'triangle';
        hum.frequency.setValueAtTime(110, t);
        humG.gain.setValueAtTime(0.03, t);
        humLFO.type = 'sine';
        humLFO.frequency.setValueAtTime(0.5, t);
        humLFOG.gain.setValueAtTime(0.015, t);
        humLFO.connect(humLFOG);
        humLFOG.connect(humG.gain);
        hum.connect(humG); humG.connect(c.destination);
        hum.start(t); humLFO.start(t);
        ambientNodes.push(hum, humG, humLFO, humLFOG);

        // Layer 3: Periodic radar pings + data blips
        let pingCycle = 0;
        ambientInterval = setInterval(function() {
            const now = c.currentTime;
            pingCycle++;

            // Radar ping every cycle
            const ping = c.createOscillator();
            const pingG = c.createGain();
            ping.type = 'sine';
            ping.frequency.setValueAtTime(1800 + Math.random() * 400, now);
            pingG.gain.setValueAtTime(0.05, now);
            pingG.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
            ping.connect(pingG); pingG.connect(c.destination);
            ping.start(now); ping.stop(now + 0.15);

            // Data blip (every other cycle)
            if (pingCycle % 2 === 0) {
                const blip = c.createOscillator();
                const blipG = c.createGain();
                blip.type = 'square';
                blip.frequency.setValueAtTime(600 + Math.random() * 800, now + 0.08);
                blipG.gain.setValueAtTime(0.025, now + 0.08);
                blipG.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
                blip.connect(blipG); blipG.connect(c.destination);
                blip.start(now + 0.08); blip.stop(now + 0.15);
            }

            // Sweep tone every 4th cycle
            if (pingCycle % 4 === 0) {
                const sw = c.createOscillator();
                const swG = c.createGain();
                sw.type = 'sine';
                sw.frequency.setValueAtTime(300, now);
                sw.frequency.exponentialRampToValueAtTime(1200, now + 0.3);
                swG.gain.setValueAtTime(0.03, now);
                swG.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
                sw.connect(swG); swG.connect(c.destination);
                sw.start(now); sw.stop(now + 0.35);
            }
        }, 1200);
    }

    function gateAmbientStop() {
        if (ambientInterval) { clearInterval(ambientInterval); ambientInterval = null; }
        ambientNodes.forEach(function(n) {
            try { n.stop(); } catch(e) {}
            try { n.disconnect(); } catch(e) {}
        });
        ambientNodes = [];
    }

    /* ═══ Auto-attach to buttons & links ═══ */
    function autoAttach() {
        document.addEventListener('click', function (e) {
            const el = e.target.closest('button, .cyber-btn, a.cyber-btn, a.option-card, .btn-card-edit, .btn-edit, .btn-edit-profile, .btn-unlock, .btn-save, [type="submit"]');
            if (el) click();
        }, true);
    }

    /* ══════════════════════════════════════
       12. RADAR SCAN — scanning ping loop
       ══════════════════════════════════════ */
    let radarScanTimer = null;
    function radarScan() {
        const c = getCtx();
        let cycle = 0;
        function ping() {
            const now = c.currentTime;
            // Sonar ping
            osc('sine', 1200, now, 0.15, 0.08);
            osc('sine', 1800, now + 0.05, 0.1, 0.04);
            // Sub pulse
            osc('sine', 60, now, 0.4, 0.06);
            // Data blip
            if (cycle % 3 === 0) {
                osc('square', 2400, now + 0.2, 0.05, 0.03);
                osc('square', 3200, now + 0.25, 0.04, 0.02);
            }
            noise(0.08, 0.04, now + 0.1);
            cycle++;
        }
        ping();
        radarScanTimer = setInterval(ping, 800);
    }
    function radarScanStop() {
        if (radarScanTimer) { clearInterval(radarScanTimer); radarScanTimer = null; }
    }

    /* ══════════════════════════════════════
       13. RADAR ALERT — threat detected sound
       ══════════════════════════════════════ */
    function radarAlertWarning() {
        const c = getCtx();
        const t = c.currentTime;
        osc('sawtooth', 500, t, 0.3, 0.1);
        osc('sawtooth', 700, t + 0.15, 0.3, 0.08);
        osc('sine', 300, t, 0.5, 0.06);
        noise(0.2, 0.06, t);
        for (let i = 0; i < 4; i++) {
            osc('sine', 900 + i * 200, t + 0.4 + i * 0.12, 0.1, 0.05);
        }
    }
    function radarAlertCritical() {
        const c = getCtx();
        const t = c.currentTime;
        osc('sawtooth', 80, t, 0.6, 0.2);
        noise(0.4, 0.15, t);
        const o = c.createOscillator();
        const g = c.createGain();
        o.type = 'sawtooth';
        o.frequency.setValueAtTime(300, t + 0.3);
        o.frequency.linearRampToValueAtTime(1200, t + 0.8);
        o.frequency.linearRampToValueAtTime(300, t + 1.3);
        g.gain.setValueAtTime(0.12, t + 0.3);
        g.gain.exponentialRampToValueAtTime(0.001, t + 1.5);
        o.connect(g); g.connect(c.destination);
        o.start(t + 0.3); o.stop(t + 1.5);
        const o2 = c.createOscillator();
        const g2 = c.createGain();
        o2.type = 'square';
        o2.frequency.setValueAtTime(600, t + 0.3);
        o2.frequency.linearRampToValueAtTime(2000, t + 0.8);
        o2.frequency.linearRampToValueAtTime(600, t + 1.3);
        g2.gain.setValueAtTime(0.06, t + 0.3);
        g2.gain.exponentialRampToValueAtTime(0.001, t + 1.4);
        o2.connect(g2); g2.connect(c.destination);
        o2.start(t + 0.3); o2.stop(t + 1.5);
        for (let i = 0; i < 6; i++) {
            osc('square', 1500, t + 1.5 + i * 0.15, 0.08, 0.08);
        }
    }

    // Initialize on first user interaction
    let attached = false;
    function init() {
        if (attached) return;
        attached = true;
        document.addEventListener('click', function firstClick() {
            getCtx();
            document.removeEventListener('click', firstClick, true);
        }, true);
        autoAttach();
    }

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return {
        click,
        hover,
        bootScan,
        loginSuccess,
        loginFailed,
        notification,
        lockoutAlarm,
        sirenStart,
        sirenStop,
        transition,
        type,
        gateAmbient,
        gateAmbientStop,
        radarScan,
        radarScanStop,
        radarAlertWarning,
        radarAlertCritical
    };
})();
