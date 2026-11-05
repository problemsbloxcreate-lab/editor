#version 150
// Portal Macabro (05/11/2026): o céu estrelado do portal do End em VERMELHO - usado só pelo end_gateway no render da cinemática

#moj_import <matrix.glsl>

uniform sampler2D Sampler0;
uniform sampler2D Sampler1;

uniform float GameTime;
uniform int EndPortalLayers;

in vec4 texProj0;

const vec3[] COLORS = vec3[](
    vec3(0.318601, 0.028813, 0.014184),
    vec3(0.275781, 0.024939, 0.012278),
    vec3(0.292355, 0.026439, 0.013016),
    vec3(0.330158, 0.029858, 0.014699),
    vec3(0.338376, 0.030602, 0.015066),
    vec3(0.355483, 0.032149, 0.015827),
    vec3(0.478342, 0.043259, 0.021296),
    vec3(0.443095, 0.040071, 0.019728),
    vec3(0.561175, 0.050749, 0.024984),
    vec3(0.538283, 0.048680, 0.023965),
    vec3(0.427172, 0.038631, 0.019019),
    vec3(0.699580, 0.063266, 0.031147),
    vec3(0.617251, 0.055822, 0.027482),
    vec3(0.925663, 0.083712, 0.041213),
    vec3(1.121280, 0.101403, 0.049922),
    vec3(1.200000, 0.171987, 0.084670)
);

const mat4 SCALE_TRANSLATE = mat4(
    0.5, 0.0, 0.0, 0.25,
    0.0, 0.5, 0.0, 0.25,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
);

mat4 end_portal_layer(float layer) {
    mat4 translate = mat4(
        1.0, 0.0, 0.0, 17.0 / layer,
        0.0, 1.0, 0.0, (2.0 + layer / 1.5) * (GameTime * 1.5),
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    );

    mat2 rotate = mat2_rotate_z(radians((layer * layer * 4321.0 + layer * 9.0) * 2.0));

    mat2 scale = mat2((4.5 - layer / 4.0) * 2.0);

    return mat4(scale * rotate) * translate * SCALE_TRANSLATE;
}

out vec4 fragColor;

void main() {
    vec3 color = textureProj(Sampler0, texProj0).rgb * COLORS[0];
    for (int i = 0; i < EndPortalLayers; i++) {
        color += textureProj(Sampler1, texProj0 * end_portal_layer(float(i + 1))).rgb * COLORS[i];
    }
    fragColor = vec4(color, 1.0);
}
