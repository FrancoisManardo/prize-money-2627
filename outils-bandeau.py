# -*- coding: utf-8 -*-
import io, math, random

W, H = 1200, 320
random.seed(7)

def courbe(y0, amp, phase, periode, pente):
    pts = []
    for i in range(0, W + 1, 34):
        x = i
        y = y0 + pente * (x / W) * H * 0.25 \
            + amp * math.sin(phase + x / periode) \
            + amp * 0.45 * math.sin(phase * 1.7 + x / (periode * 0.43))
        pts.append((x, y))
    d = 'M%d %d' % (round(pts[0][0]), round(pts[0][1]))
    for j in range(1, len(pts) - 1):
        x0, y0_ = pts[j]
        x1, y1 = pts[j + 1]
        d += ' Q%d %d %d %d' % (round(x0), round(y0_), round((x0 + x1) / 2), round((y0_ + y1) / 2))
    return d

lignes = []
n = 26
for k in range(n):
    t = k / (n - 1.0)
    y0 = -40 + t * (H + 80)
    amp = 16 + 26 * math.sin(t * math.pi)
    phase = 0.6 * k
    periode = 150 + 70 * math.sin(t * 3.1)
    pente = -0.5 + t * 0.9
    d = courbe(y0, amp, phase, periode, pente)
    op = 0.22 + 0.42 * math.sin(t * math.pi) ** 0.6
    lignes.append((d, op, 1.0 + 1.3 * math.sin(t * math.pi)))

parts = []
parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid slice">' % (W, H))
parts.append('<defs>')
parts.append('<linearGradient id="fond" x1="0" y1="0" x2="1" y2="1">'
             '<stop offset="0" stop-color="#1616c8"/>'
             '<stop offset="0.55" stop-color="#1b1bd8"/>'
             '<stop offset="1" stop-color="#0f0f9c"/></linearGradient>')
parts.append('<linearGradient id="iris" x1="0" y1="0" x2="1" y2="0">'
             '<stop offset="0" stop-color="#ff2fd0"/>'
             '<stop offset="0.18" stop-color="#ff3b3b"/>'
             '<stop offset="0.38" stop-color="#ff9a1f"/>'
             '<stop offset="0.55" stop-color="#ffe14d"/>'
             '<stop offset="0.72" stop-color="#5cf08a"/>'
             '<stop offset="0.88" stop-color="#3fd8ff"/>'
             '<stop offset="1" stop-color="#7a5cff"/></linearGradient>')
parts.append('</defs>')
parts.append('<rect width="%d" height="%d" fill="url(#fond)"/>' % (W, H))
parts.append('<g fill="none" stroke="url(#iris)" stroke-linecap="round">')
for d, op, sw in lignes:
    parts.append('<path d="%s" stroke-width="%.1f" opacity="%.2f"/>' % (d, sw, op))
parts.append('</g>')
# Reflets blancs fins pour le relief
parts.append('<g fill="none" stroke="#ffffff" stroke-linecap="round" opacity="0.16">')
for k in range(0, n, 6):
    d, op, sw = lignes[k]
    parts.append('<path d="%s" stroke-width="0.8"/>' % d)
parts.append('</g>')
parts.append('</svg>')

svg = ''.join(parts)
io.open('header-lines.svg', 'w', encoding='utf-8').write(svg)
print('svg genere :', len(svg), 'octets')
