"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import "../index.css";

// ─── Animated Background ──────────────────────────────────────────────────────
function ParticleBackground() {
    const canvasRef = useRef(null);
    const animRef = useRef(null);
    const mouseRef = useRef({ x: -9999, y: -9999 });

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");

        let W = (canvas.width = window.innerWidth);
        let H = (canvas.height = window.innerHeight);

        const NODE_COUNT = 38;
        const nodes = Array.from({ length: NODE_COUNT }, (_, i) => ({
            x: Math.random() * W,
            y: Math.random() * H,
            r: 1.5 + Math.random() * 3,
            vx: (Math.random() - 0.5) * 0.35,
            vy: (Math.random() - 0.5) * 0.35,
            phase: Math.random() * Math.PI * 2,
            speed: 0.004 + Math.random() * 0.006,
            hue: 200 + Math.random() * 60,
            opacity: 0.25 + Math.random() * 0.5,
        }));

        const WAVE_COUNT = 4;
        const waves = Array.from({ length: WAVE_COUNT }, (_, i) => ({
            y: H * (0.2 + i * 0.22),
            amp: 18 + Math.random() * 30,
            freq: 0.008 + Math.random() * 0.006,
            speed: 0.0006 + Math.random() * 0.001,
            phase: Math.random() * Math.PI * 2,
            hue: 195 + i * 25,
            alpha: 0.04 + i * 0.018,
        }));

        const onResize = () => {
            W = canvas.width = window.innerWidth;
            H = canvas.height = window.innerHeight;
        };
        const onMouse = (e) => {
            mouseRef.current = { x: e.clientX, y: e.clientY };
        };

        window.addEventListener("resize", onResize);
        window.addEventListener("mousemove", onMouse);

        let t = 0;
        const draw = () => {
            t++;
            ctx.clearRect(0, 0, W, H);

            waves.forEach((w) => {
                w.phase += w.speed;
                ctx.beginPath();
                ctx.moveTo(0, w.y);
                for (let x = 0; x <= W; x += 3) {
                    const noise =
                        Math.sin(x * w.freq + w.phase) * w.amp +
                        Math.sin(x * w.freq * 2.3 + w.phase * 1.7) * w.amp * 0.4;
                    ctx.lineTo(x, w.y + noise);
                }
                ctx.strokeStyle = `hsla(${w.hue}, 70%, 65%, ${w.alpha})`;
                ctx.lineWidth = 1.5;
                ctx.stroke();
            });

            const mx = mouseRef.current.x;
            const my = mouseRef.current.y;

            nodes.forEach((n) => {
                n.phase += n.speed;
                n.x += n.vx + Math.sin(n.phase) * 0.12;
                n.y += n.vy + Math.cos(n.phase * 0.7) * 0.12;

                const dx = n.x - mx,
                    dy = n.y - my;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    const force = (120 - dist) / 120;
                    n.x += (dx / dist) * force * 1.8;
                    n.y += (dy / dist) * force * 1.8;
                }

                if (n.x < 0) n.x = W;
                if (n.x > W) n.x = 0;
                if (n.y < 0) n.y = H;
                if (n.y > H) n.y = 0;

                const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 6);
                grd.addColorStop(0, `hsla(${n.hue}, 80%, 75%, ${n.opacity})`);
                grd.addColorStop(1, `hsla(${n.hue}, 80%, 75%, 0)`);
                ctx.beginPath();
                ctx.arc(n.x, n.y, n.r * 6, 0, Math.PI * 2);
                ctx.fillStyle = grd;
                ctx.fill();

                ctx.beginPath();
                ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
                ctx.fillStyle = `hsla(${n.hue}, 90%, 85%, ${n.opacity + 0.2})`;
                ctx.fill();
            });

            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const a = nodes[i],
                        b = nodes[j];
                    const dx = a.x - b.x,
                        dy = a.y - b.y;
                    const d = Math.sqrt(dx * dx + dy * dy);
                    if (d < 130) {
                        const alpha = (1 - d / 130) * 0.18;
                        ctx.beginPath();
                        ctx.moveTo(a.x, a.y);
                        ctx.lineTo(b.x, b.y);
                        ctx.strokeStyle = `hsla(215, 70%, 75%, ${alpha})`;
                        ctx.lineWidth = 0.8;
                        ctx.stroke();
                    }
                }
            }

            animRef.current = requestAnimationFrame(draw);
        };

        draw();

        return () => {
            cancelAnimationFrame(animRef.current);
            window.removeEventListener("resize", onResize);
            window.removeEventListener("mousemove", onMouse);
        };
    }, []);

    return <canvas ref={canvasRef} className="hero-canvas" />;
}

// ─── File Drop Zone ───────────────────────────────────────────────────────────
function DropZone({ label, sublabel, accept, file, onFile }) {
    const inputRef = useRef(null);
    const [dragging, setDragging] = useState(false);

    const handleDrop = useCallback(
        (e) => {
            e.preventDefault();
            setDragging(false);
            const f = e.dataTransfer.files[0];
            if (f) onFile(f);
        },
        [onFile]
    );

    return (
        <div
            className={`dropzone ${dragging ? "dropzone--drag" : ""} ${file ? "dropzone--filled" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
        >
            <input
                ref={inputRef}
                type="file"
                accept={accept}
                style={{ display: "none" }}
                onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
            />
            {file ? (
                <div className="dropzone__filled-content">
                    <span className="dropzone__check">✓</span>
                    <span className="dropzone__filename">{file.name}</span>
                </div>
            ) : (
                <div className="dropzone__empty-content">
                    <span className="dropzone__icon">⊕</span>
                    <span className="dropzone__label">{label}</span>
                    <span className="dropzone__sub">{sublabel}</span>
                </div>
            )}
        </div>
    );
}

// ─── Modality Card ────────────────────────────────────────────────────────────
function ModalityCard({ id, title, description, selected, onToggle, file, onFile }) {
    return (
        <div
            className={`modality-card ${selected ? "modality-card--selected" : ""}`}
            onClick={() => onToggle(id)}
        >
            <div className="modality-card__header">
                <div className={`modality-card__dot ${selected ? "modality-card__dot--on" : ""}`} />
                <div>
                    <div className="modality-card__title">{title}</div>
                    <div className="modality-card__desc">{description}</div>
                </div>
            </div>
            {selected && (
                <div onClick={(e) => e.stopPropagation()}>
                    <DropZone
                        label={`Upload ${title} CSV`}
                        sublabel="two-column: freq, intensity"
                        accept=".csv"
                        file={file}
                        onFile={onFile}
                    />
                </div>
            )}
        </div>
    );
}

// ─── Hero ─────────────────────────────────────────────────────────────────────
export default function Hero() {
    const [selected, setSelected] = useState(new Set());
    const [files, setFiles] = useState({ nmr: null, ms: null });
    const [candidates, setCandidates] = useState(5);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const toggle = (id) => {
        setSelected((prev) => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    };

    const setFile = (id, file) => setFiles((prev) => ({ ...prev, [id]: file }));

    const toBase64 = (file) =>
        new Promise((res, rej) => {
            const r = new FileReader();
            r.onload = () => res(r.result.split(",")[1]);
            r.onerror = rej;
            r.readAsDataURL(file);
        });

    const handleGenerate = async () => {
        if (selected.size === 0) {
            setError("Select at least one spectral modality.");
            return;
        }
        setError(null);
        setLoading(true);
        try {
            const body = { top_k: candidates };
            if (selected.has("nmr") && files.nmr)
                body.nmr_csv = await toBase64(files.nmr);
            if (selected.has("ms") && files.ms)
                body.ms_csv = await toBase64(files.ms);

            const res = await fetch("http://localhost:8000/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            if (!res.ok) throw new Error((await res.json()).detail || "Prediction failed");
            const data = await res.json();
            console.log("Candidates:", data.candidates);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const MODALITIES = [
        { id: "nmr", title: "NMR Spectra", description: "¹H or ¹³C chemical shift data" },
        { id: "ms", title: "Mass Spectrometry", description: "m/z fragmentation pattern" },
    ];

    return (
        <div className="hero">
            <ParticleBackground />
            <div className="orb orb--pink" />
            <div className="orb orb--blue" />
            <div className="orb orb--teal" />

            <div className="hero__content">
                <div className="hero__wordmark">SpectraStruct</div>
                <h1 className="hero__headline">
                    Predict 3D Molecular Structure
                    <br />
                    <span className="hero__headline-accent">from Spectral Data</span>
                </h1>
                <p className="hero__subhead">
                    Select one or both spectral modalities to generate a ranked set of
                    3D molecular structure candidates.
                </p>

                <div className="step-label">
                    <span className="step-label__num">01</span>
                    <span className="step-label__text">Choose spectral modalities</span>
                </div>

                <div className="hero__card">
                    <div className="modality-list">
                        {MODALITIES.map((m) => (
                            <ModalityCard
                                key={m.id}
                                id={m.id}
                                title={m.title}
                                description={m.description}
                                selected={selected.has(m.id)}
                                onToggle={toggle}
                                file={files[m.id]}
                                onFile={(f) => setFile(m.id, f)}
                            />
                        ))}
                    </div>

                    <div className="slider-row">
                        <span className="slider-row__label">K‑Candidates</span>
                        <input
                            className="slider-row__range"
                            type="range"
                            min={1}
                            max={10}
                            value={candidates}
                            onChange={(e) => setCandidates(Number(e.target.value))}
                        />
                        <span className="slider-row__val">{candidates}</span>
                    </div>

                    {error && <div className="hero__error">{error}</div>}

                    <button
                        className={`hero__cta ${loading ? "hero__cta--loading" : ""}`}
                        onClick={handleGenerate}
                        disabled={loading}
                    >
                        {loading ? <span className="hero__spinner" /> : "Generate Molecule →"}
                    </button>
                </div>
            </div>
        </div>
    );
}