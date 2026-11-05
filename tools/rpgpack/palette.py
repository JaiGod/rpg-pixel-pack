"""Master palette for the RPG Pixel Pack.

Every sprite in the pack is drawn exclusively from these ramps. Each ramp has
four shades ordered dark -> light: [shadow, base, light, highlight].
Lighting convention across the whole pack: light comes from the top-left.
"""

def _h(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

def ramp(*hexes):
    return [_h(h) for h in hexes]

OUTLINE = _h('1c1626')       # universal sprite outline
INK = _h('2a2135')           # interior line work / eyes
WHITE = _h('f4f1ea')
EYE_WHITE = _h('e8e4f0')
TRANSPARENT = (0, 0, 0, 0)

RAMPS = {
    # ---- skin tones (6) -------------------------------------------------
    'skin_porcelain': ramp('b9786a', 'dea08a', 'f2c3a7', 'fde0cc'),
    'skin_light':     ramp('a8664f', 'd08c6b', 'e9af8b', 'f7cfae'),
    'skin_tan':       ramp('8e5639', 'b57650', 'd39a6c', 'e8bb8e'),
    'skin_olive':     ramp('7a4a2e', '9e6640', 'bf8656', 'd9a776'),
    'skin_brown':     ramp('5a3422', '7c4a30', '9c6644', 'ba845c'),
    'skin_deep':      ramp('3a2018', '553022', '734431', '925c44'),
    # ---- hair (8) -------------------------------------------------------
    'hair_black':  ramp('1f1a24', '2f2836', '463d4f', '5f5568'),
    'hair_brown':  ramp('3d2416', '5c3820', '7d5130', '9e6d44'),
    'hair_blonde': ramp('8a5f22', 'c08a34', 'e2b75a', 'f5dc8e'),
    'hair_red':    ramp('6b1f16', '9a3220', 'c4502e', 'e0784a'),
    'hair_silver': ramp('6e6a7a', '9894a6', 'c4c1cf', 'eceaf2'),
    'hair_blue':   ramp('1e2f6b', '2f4ea0', '4f78d0', '86aaf0'),
    'hair_pink':   ramp('7a2a5c', 'b24684', 'dc6eac', 'f4a6d0'),
    'hair_green':  ramp('1f4a2c', '2f6e3c', '4d9a50', '84c470'),
    # ---- cloth (16) -----------------------------------------------------
    'cloth_red':     ramp('5e1a1e', '8f2a2a', 'c0453a', 'e2705a'),
    'cloth_crimson': ramp('4a1030', '7a1c44', 'a8325c', 'd05a80'),
    'cloth_orange':  ramp('7a3412', 'b25a1e', 'e08434', 'f4b060'),
    'cloth_yellow':  ramp('7e5a12', 'b8861e', 'e2b83a', 'f6e07a'),
    'cloth_green':   ramp('1e4a26', '2e6e32', '4c9a40', '80c45c'),
    'cloth_forest':  ramp('1a3224', '284a30', '3c6a3e', '5c8c50'),
    'cloth_teal':    ramp('103e44', '1a6466', '2a9088', '5cc0a8'),
    'cloth_blue':    ramp('1c2c5e', '284492', '3c68c4', '6c98e6'),
    'cloth_navy':    ramp('141a36', '1e2850', '2e3c70', '485a94'),
    'cloth_purple':  ramp('2e1a4a', '4a2a74', '6c42a4', '9a6ed0'),
    'cloth_brown':   ramp('3a2418', '5a3a24', '7c5434', 'a07448'),
    'cloth_tan':     ramp('6e5434', '9c7c52', 'c4a476', 'e2c99c'),
    'cloth_gray':    ramp('34343e', '50525e', '747886', '9ea2ae'),
    'cloth_black':   ramp('121018', '1e1a26', '2e2a3a', '444054'),
    'cloth_white':   ramp('8e8ca0', 'bcbccc', 'e0e0ea', 'f8f8fc'),
    'cloth_pink':    ramp('6e2a4c', 'a4466e', 'd46e94', 'f2a2bc'),
    # ---- leather / materials -------------------------------------------
    'leather':      ramp('2e1c14', '4a2e1e', '6c4429', '8e5e3a'),
    'leather_dark': ramp('1c1210', '2c1e18', '402c22', '5a3e2e'),
    'iron':         ramp('2f3442', '4c5366', '737c92', 'aab3c6'),
    'steel':        ramp('3a4456', '5e6c84', '8e9cb4', 'd0daea'),
    'gold':         ramp('6e4a12', 'a8741e', 'dcab3a', 'f7e08a'),
    'bronze':       ramp('4e2c16', '7a4a24', 'a8703a', 'd4a060'),
    'silver':       ramp('5c6070', '8a90a2', 'bcc2d0', 'eef0f6'),
    'crystal':      ramp('1d5b7a', '2f93b8', '6fd0e6', 'c8f4fa'),
    'amethyst':     ramp('3e1c5e', '6a34a0', '9e62d6', 'd4a8f4'),
    'ruby':         ramp('5a0e1c', '961c2c', 'd23a40', 'f4848a'),
    'emerald':      ramp('0e4a30', '1a7a4a', '30b068', '84e4a4'),
    'bone':         ramp('7a7058', 'b0a684', 'd8d0b0', 'f4f0dc'),
    'shadow':       ramp('100c1a', '1e1630', '342650', '54407a'),
    'neon_pink':    ramp('6a1a6e', 'b02aa8', 'ee50d8', 'ffa8f4'),
    'neon_cyan':    ramp('0e4a62', '1a88a8', '30d0e6', 'a8f8ff'),
    'neon_green':   ramp('1a5a1e', '2aa030', '5ae84a', 'c4ffa0'),
    'fire':         ramp('8a1c10', 'd8461a', 'f88c22', 'fcdc5a'),
    'magic_blue':   ramp('1a2a8a', '2e54d8', '5e9cfa', 'c4e4ff'),
    'magic_purple': ramp('3a1070', '7020c0', 'b060f0', 'ecc4ff'),
    'poison':       ramp('2e4a10', '5a8a1a', '94c82a', 'd8f46a'),
    # ---- nature ---------------------------------------------------------
    'grass':      ramp('24502e', '357a3a', '58a646', '8ccf5c'),
    'grass_dry':  ramp('4e5424', '767a32', 'a0a24a', 'c8c46e'),
    'leaf':       ramp('163a26', '22583a', '347a44', '58a050'),
    'leaf_autumn':ramp('6a2a14', 'a24a1c', 'd2782a', 'f0b048'),
    'pine':       ramp('0e2a26', '163e34', '22584a', '3a7a5e'),
    'dirt':       ramp('4a2f22', '6e4630', '93633f', 'b88a5c'),
    'sand':       ramp('9c7a48', 'c9a36a', 'e6c88e', 'f6e4b4'),
    'sandstone':  ramp('7a5232', 'a87444', 'cc9a5c', 'e8c088'),
    'snow':       ramp('7d8fb0', 'a9bad6', 'd4e0f0', 'f8fbff'),
    'ice':        ramp('3a6a9a', '5a9acc', '94cdee', 'dcf4ff'),
    'stone':      ramp('393c4a', '565a6b', '7d8294', 'a8adbd'),
    'stone_dark': ramp('1e1e2a', '2e2e3e', '444658', '5e6274'),
    'stone_warm': ramp('4a3e3a', '6a5a52', '8e7c70', 'b4a294'),
    'cobble':     ramp('3e3a40', '5c5660', '807a82', 'a6a0a6'),
    'brick':      ramp('5a2420', '84362a', 'ac5038', 'cc7a56'),
    'water':      ramp('1a3a6e', '2860a8', '3f8fd6', '7cc4f0'),
    'water_deep': ramp('0e1e46', '16306e', '22489a', '3a6ec4'),
    'swamp':      ramp('1e2a1e', '2e3e2a', '44583a', '62744c'),
    'swamp_water':ramp('1c2a24', '2a3e30', '3e5640', '587050'),
    'mud':        ramp('2e2218', '44321e', '5e4628', '7a5e36'),
    'lava':       ramp('6e1410', 'b8301a', 'ec6a20', 'fcc048'),
    'wood':       ramp('3d2618', '5e3b22', '835532', 'a8744a'),
    'wood_dark':  ramp('24160e', '3a2416', '553620', '74502e'),
    'wood_light': ramp('7a5434', 'a8784c', 'cca06a', 'e8c690'),
    'thatch':     ramp('6e5420', '9c7a30', 'c4a04a', 'e2c470'),
    'roof_red':   ramp('5a1c1a', '8a2c24', 'b24432', 'd4684a'),
    'roof_blue':  ramp('1e2a4e', '2c3e72', '40589a', '6480c0'),
    'roof_slate': ramp('24263a', '363a52', '4c5270', '6a7294'),
    'roof_green': ramp('1c3a2a', '2a543a', '3c7450', '5a966a'),
    'plaster':    ramp('9a8a74', 'c4b498', 'e0d4b8', 'f4ecd8'),
    # ---- tech -----------------------------------------------------------
    'tech':       ramp('2a2f3e', '3e4659', '5b6680', '8794b0'),
    'tech_light': ramp('6a7488', '9aa4b8', 'c8d0dc', 'eef2f8'),
    'tech_dark':  ramp('12141c', '1c202c', '2a3040', '3c4458'),
    'glass':      ramp('1a3a5a', '2a5a84', '4a8ab4', '9ad0ee'),
    'screen':     ramp('0a2a2a', '0e4a44', '1a8a6e', '5ae4b0'),
    'warning':    ramp('6a4a0a', 'b88a14', 'f0c81e', 'fcec7a'),
}

# Palette-swap keys: tintable layers are exported using these exact colors.
# The Godot shader `palette_swap.gdshader` (and the Python baker) replace
# them with any ramp from RAMPS.  Two independent channels: PRIMARY / SECONDARY.
KEY_PRIMARY = [(60, 60, 60), (110, 110, 110), (165, 165, 165), (220, 220, 220)]
KEY_SECONDARY = [(52, 40, 92), (92, 72, 152), (140, 120, 204), (190, 176, 236)]

SKINS = ['skin_porcelain', 'skin_light', 'skin_tan', 'skin_olive', 'skin_brown', 'skin_deep']
HAIR_COLORS = ['hair_black', 'hair_brown', 'hair_blonde', 'hair_red', 'hair_silver',
               'hair_blue', 'hair_pink', 'hair_green']
CLOTH_COLORS = [k for k in RAMPS if k.startswith('cloth_')]


def all_colors():
    seen, out = set(), []
    for c in [OUTLINE, INK, WHITE, EYE_WHITE]:
        if c not in seen:
            seen.add(c); out.append(c)
    for r in RAMPS.values():
        for c in r:
            if c not in seen:
                seen.add(c); out.append(c)
    return out
