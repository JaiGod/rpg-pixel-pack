"""Tiny deterministic pixel-art engine used to draw every asset in the pack."""
import math
import random
import numpy as np
from PIL import Image

from .palette import OUTLINE, RAMPS, KEY_PRIMARY, KEY_SECONDARY


def R(name_or_ramp):
    """Resolve a ramp name (or pass through an explicit ramp list)."""
    if isinstance(name_or_ramp, str):
        return RAMPS[name_or_ramp]
    return name_or_ramp


def rgba(c, a=255):
    if len(c) == 4:
        return tuple(c)
    return (c[0], c[1], c[2], a)


def mix(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1[:3], c2[:3]))


class Canvas:
    def __init__(self, w, h=None):
        h = w if h is None else h
        self.w, self.h = w, h
        self.img = np.zeros((h, w, 4), dtype=np.uint8)

    # ---------------------------------------------------------------- basics
    def copy(self):
        c = Canvas(self.w, self.h)
        c.img = self.img.copy()
        return c

    @property
    def alpha(self):
        return self.img[:, :, 3] > 0

    def px(self, x, y, col):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img[y, x] = rgba(col)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return tuple(self.img[y, x])
        return (0, 0, 0, 0)

    def erase(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img[y, x] = 0

    def rect(self, x0, y0, x1, y1, col):
        """Filled rect, inclusive coords."""
        x0, x1 = sorted((int(x0), int(x1)))
        y0, y1 = sorted((int(y0), int(y1)))
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, self.w - 1), min(y1, self.h - 1)
        if x0 <= x1 and y0 <= y1:
            self.img[y0:y1 + 1, x0:x1 + 1] = rgba(col)

    def hline(self, x0, x1, y, col):
        self.rect(x0, y, x1, y, col)

    def vline(self, x, y0, y1, col):
        self.rect(x, y0, x, y1, col)

    def line(self, x0, y0, x1, y1, col, width=1):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if width == 1:
                self.px(x0, y0, col)
            else:
                self.rect(x0, y0, x0 + width - 1, y0 + width - 1, col)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def paint(self, mask, col):
        self.img[mask] = rgba(col)

    def paste(self, other, dx=0, dy=0):
        """Alpha-over paste (binary alpha)."""
        src = other.img
        h, w = src.shape[:2]
        for_y0, for_x0 = max(0, dy), max(0, dx)
        y1, x1 = min(self.h, dy + h), min(self.w, dx + w)
        if for_y0 >= y1 or for_x0 >= x1:
            return
        s = src[for_y0 - dy:y1 - dy, for_x0 - dx:x1 - dx]
        d = self.img[for_y0:y1, for_x0:x1]
        m = s[:, :, 3] > 0
        d[m] = s[m]

    def shifted(self, dx, dy):
        c = Canvas(self.w, self.h)
        c.paste(self, dx, dy)
        return c

    def flipped(self):
        c = Canvas(self.w, self.h)
        c.img = self.img[:, ::-1].copy()
        return c

    def rot90(self, k=1):
        c = Canvas(self.h, self.w)
        c.img = np.rot90(self.img, k).copy()
        return c

    def to_pil(self):
        return Image.fromarray(self.img, 'RGBA')

    @staticmethod
    def from_pil(im):
        im = im.convert('RGBA')
        c = Canvas(im.width, im.height)
        c.img = np.array(im, dtype=np.uint8)
        return c

    # ------------------------------------------------------------ masks
    def mask_rect(self, x0, y0, x1, y1):
        m = np.zeros((self.h, self.w), bool)
        x0, x1 = sorted((int(x0), int(x1)))
        y0, y1 = sorted((int(y0), int(y1)))
        m[max(y0, 0):max(y1 + 1, 0), max(x0, 0):max(x1 + 1, 0)] = True
        return m

    def mask_ellipse(self, cx, cy, rx, ry):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        return ((xx + 0.5 - cx) / max(rx, 0.01)) ** 2 + ((yy + 0.5 - cy) / max(ry, 0.01)) ** 2 <= 1.0

    def mask_poly(self, pts):
        from PIL import ImageDraw
        im = Image.new('L', (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=1, outline=1)
        return np.array(im, bool)

    def empty_mask(self):
        return np.zeros((self.h, self.w), bool)

    # ------------------------------------------------------------ shading
    def shade(self, mask, ramp, depth=1, hi=True, light=True, base=1):
        """Directional shading: light top-left, shadow bottom-right."""
        ramp = R(ramp)
        if not mask.any():
            return
        n = lambda dy, dx: _shift(mask, dy, dx)
        lvl = np.full(mask.shape, base, np.int8)
        if light:
            lit = mask & (~n(-1, 0) | ~n(0, -1))
            lvl[lit] = min(base + 1, 3)
        sh = mask & (~n(1, 0) | ~n(0, 1))
        if depth >= 2:
            sh |= mask & ~n(2, 0)
        lvl[sh] = max(base - 1, 0)
        if hi:
            h = mask & ~n(-1, 0) & ~n(0, -1) & n(1, 0) & n(0, 1)
            lvl[h] = 3
        for i in range(4):
            sel = mask & (lvl == i)
            if sel.any():
                self.img[sel] = rgba(ramp[i])

    def shade_cyl(self, mask, ramp, axis='x', hi=True):
        """Cylindrical shading along an axis (pillars, limbs, trunks, barrels)."""
        ramp = R(ramp)
        if not mask.any():
            return
        ys, xs = np.nonzero(mask)
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        if axis == 'x':
            lo, hi_ = xs.min(), xs.max()
            t = (xx - lo) / max(hi_ - lo, 1)
        else:
            lo, hi_ = ys.min(), ys.max()
            t = (yy - lo) / max(hi_ - lo, 1)
        lvl = np.where(t < 0.22, 2, np.where(t < 0.68, 1, 0))
        if hi:
            lvl = np.where((t >= 0.12) & (t < 0.28), 3, lvl) if (hi_ - lo) >= 5 else lvl
        for i in range(4):
            sel = mask & (lvl == i)
            if sel.any():
                self.img[sel] = rgba(ramp[i])

    def fill(self, mask, ramp, level=1):
        self.img[mask] = rgba(R(ramp)[level])

    # ------------------------------------------------------------ outline
    def outline(self, col=OUTLINE, diag=False, inside=False):
        a = self.alpha
        n = lambda dy, dx: _shift(a, dy, dx)
        if inside:
            edge = a & (~n(-1, 0) | ~n(1, 0) | ~n(0, -1) | ~n(0, 1))
            self.img[edge] = rgba(col)
            return self
        o = ~a & (n(-1, 0) | n(1, 0) | n(0, -1) | n(0, 1))
        if diag:
            o |= ~a & (n(-1, -1) | n(1, 1) | n(-1, 1) | n(1, -1))
        self.img[o] = rgba(col)
        return self

    def recolor(self, mapping):
        """mapping: {(r,g,b): (r,g,b)} exact replacement."""
        flat = self.img.reshape(-1, 4)
        for src, dst in mapping.items():
            m = (flat[:, 0] == src[0]) & (flat[:, 1] == src[1]) & (flat[:, 2] == src[2]) & (flat[:, 3] > 0)
            flat[m, :3] = dst[:3]
        return self

    def tint_flash(self, col=(255, 255, 255), t=0.6):
        a = self.alpha
        rgb = self.img[:, :, :3].astype(float)
        rgb[a] = rgb[a] * (1 - t) + np.array(col) * t
        self.img[:, :, :3] = rgb.astype(np.uint8)
        return self


def _shift(m, dy, dx):
    """Value at (y,x) = m[y+dy, x+dx]; out of bounds -> False."""
    h, w = m.shape
    out = np.zeros_like(m)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    if ys0 < ys1 and xs0 < xs1:
        out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def key_map(primary=None, secondary=None):
    """Mapping from palette-swap keys to real ramps (for baking)."""
    m = {}
    if primary:
        for k, c in zip(KEY_PRIMARY, R(primary)):
            m[k] = c
    if secondary:
        for k, c in zip(KEY_SECONDARY, R(secondary)):
            m[k] = c
    return m


def rng(seed):
    return random.Random(seed)


def sheet(frames_rows, fw, fh, cols=None):
    """frames_rows: list of rows, each a list of Canvas. Returns Canvas sheet."""
    cols = cols or max(len(r) for r in frames_rows)
    s = Canvas(cols * fw, len(frames_rows) * fh)
    for ry, row in enumerate(frames_rows):
        for cx, fr in enumerate(row):
            s.paste(fr, cx * fw, ry * fh)
    return s


def save(canvas_or_img, path):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = canvas_or_img.to_pil() if isinstance(canvas_or_img, Canvas) else canvas_or_img
    im.save(path, optimize=True)


def upscale(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)
