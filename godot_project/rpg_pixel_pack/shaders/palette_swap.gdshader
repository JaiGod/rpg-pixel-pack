// RPG Pixel Pack — palette swap for tintable layers.
// Tintable layer PNGs are drawn with two 4-shade "key" ramps (see assets/palette/swap_keys.json).
// This shader replaces each key shade with the matching shade of any ramp you choose.
// Leave a channel at its default (the key colors) to keep it unchanged.
shader_type canvas_item;

uniform bool swap_enabled = true;
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);

uniform vec4 primary_0 : source_color = vec4(0.235, 0.235, 0.235, 1.0);
uniform vec4 primary_1 : source_color = vec4(0.431, 0.431, 0.431, 1.0);
uniform vec4 primary_2 : source_color = vec4(0.647, 0.647, 0.647, 1.0);
uniform vec4 primary_3 : source_color = vec4(0.863, 0.863, 0.863, 1.0);
uniform vec4 secondary_0 : source_color = vec4(0.204, 0.157, 0.361, 1.0);
uniform vec4 secondary_1 : source_color = vec4(0.361, 0.282, 0.596, 1.0);
uniform vec4 secondary_2 : source_color = vec4(0.549, 0.471, 0.800, 1.0);
uniform vec4 secondary_3 : source_color = vec4(0.745, 0.690, 0.925, 1.0);

const vec3 KP0 = vec3(60.0, 60.0, 60.0) / 255.0;
const vec3 KP1 = vec3(110.0, 110.0, 110.0) / 255.0;
const vec3 KP2 = vec3(165.0, 165.0, 165.0) / 255.0;
const vec3 KP3 = vec3(220.0, 220.0, 220.0) / 255.0;
const vec3 KS0 = vec3(52.0, 40.0, 92.0) / 255.0;
const vec3 KS1 = vec3(92.0, 72.0, 152.0) / 255.0;
const vec3 KS2 = vec3(140.0, 120.0, 204.0) / 255.0;
const vec3 KS3 = vec3(190.0, 176.0, 236.0) / 255.0;
const float EPS = 0.012;

bool is_key(vec3 c, vec3 k) {
	return all(lessThan(abs(c - k), vec3(EPS)));
}

vec3 swap(vec3 c) {
	if (is_key(c, KP0)) return primary_0.rgb;
	if (is_key(c, KP1)) return primary_1.rgb;
	if (is_key(c, KP2)) return primary_2.rgb;
	if (is_key(c, KP3)) return primary_3.rgb;
	if (is_key(c, KS0)) return secondary_0.rgb;
	if (is_key(c, KS1)) return secondary_1.rgb;
	if (is_key(c, KS2)) return secondary_2.rgb;
	if (is_key(c, KS3)) return secondary_3.rgb;
	return c;
}

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	vec3 rgb = swap_enabled ? swap(tex.rgb) : tex.rgb;
	rgb = mix(rgb, flash_color.rgb, flash);
	COLOR = vec4(rgb, tex.a);
}
