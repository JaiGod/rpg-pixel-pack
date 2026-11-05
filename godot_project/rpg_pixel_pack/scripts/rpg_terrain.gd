class_name RPGTerrain
extends RefCounted
## Paint biome TileMapLayers from a "corner" grid without relying on the terrain solver.
##
## corners is a (w+1) x (h+1) Array of Arrays of 0/1 (1 = secondary terrain: path, water, ...).
## Atlas layout per biome: row 0 base variants (+decorated), rows 1-2 transitions
## (index = TL*8 + TR*4 + BL*2 + BR), row 3 cols 0-3 secondary variants, cols 4-7 obstacles.
## The TileSets also ship with Godot terrain sets (Match Corners) for painting in the editor.

static func paint(layer: TileMapLayer, corners: Array, rng: RandomNumberGenerator = null, decor_chance: float = 0.12) -> void:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.seed = 12345
	var h := corners.size() - 1
	var w: int = corners[0].size() - 1
	for y in h:
		for x in w:
			var tl: int = corners[y][x]
			var tr: int = corners[y][x + 1]
			var bl: int = corners[y + 1][x]
			var br: int = corners[y + 1][x + 1]
			var idx := tl * 8 + tr * 4 + bl * 2 + br
			var atlas: Vector2i
			if idx == 0:
				var col := rng.randi_range(0, 3)
				if rng.randf() < decor_chance:
					col = rng.randi_range(4, 7)
				atlas = Vector2i(col, 0)
			elif idx == 15:
				atlas = Vector2i(rng.randi_range(0, 3), 3)
			else:
				atlas = Vector2i(idx % 8, 1 + idx / 8)
			layer.set_cell(Vector2i(x, y), 0, atlas)


## Place a solid obstacle tile (row 3, cols 4-7) — has collision in the TileSet.
static func obstacle(layer: TileMapLayer, cell: Vector2i, which: int) -> void:
	layer.set_cell(cell, 0, Vector2i(4 + clampi(which, 0, 3), 3))


## Build an all-zero corner grid.
static func empty_corners(w: int, h: int) -> Array:
	var c: Array = []
	for y in h + 1:
		var row: Array = []
		row.resize(w + 1)
		row.fill(0)
		c.append(row)
	return c


## Mark a rectangle of tiles (inclusive tile coords) as secondary terrain.
static func fill_rect(corners: Array, r: Rect2i) -> void:
	for y in range(r.position.y, r.end.y + 1):
		for x in range(r.position.x, r.end.x + 1):
			if y >= 0 and y < corners.size() and x >= 0 and x < corners[0].size():
				corners[y][x] = 1


static func fill_ellipse(corners: Array, center: Vector2, radii: Vector2) -> void:
	for y in corners.size():
		for x in corners[0].size():
			var d := Vector2((x - center.x) / radii.x, (y - center.y) / radii.y)
			if d.length_squared() <= 1.0:
				corners[y][x] = 1
