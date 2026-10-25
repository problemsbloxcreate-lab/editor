package dev.cinecam;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Per-pass animation table (anim.json): posed player-model actors, water-level drain and water beams.
 * Rows are aligned 1:1 with camera.csv rows. See references/actors.md in the skill.
 *
 * Pose vector (PN numbers, angles in degrees, positions in blocks):
 *  0-2 feet x,y,z | 3 yaw | 4-6 scale xyz | 7-9 head rot | 10-12 right arm | 13-15 left arm | 16-18 right leg | 19-21 left leg
 *  22 belly (x/z scale of torso) | 23 belly y scale | 24 head scale | 25 lean (deg about feet, X axis) | 26 item on (0/1)
 *  27 jump/hover offset (blocks) | 28 roll (deg about feet, Z axis) | 29 fullbright (0/1)
 *  30-33 limb length (y scale) right arm, left arm, right leg, left leg (0 = 1) | 34 blob-shadow ground y (0 = no shadow) | 35 silhouette 0..1 (backlit darkening)
 *  36 voxel belly radius (model px, 0 = off) | 37 its centre y (px below the neck) | 38 protrusion in front of the torso (px)
 *  39 slosh ripple amplitude (px) | 40 jiggle (+ = taller/narrower) | 41 voxel size (px, 0 = 1) | 42 water shimmer 0..1 on the belly
 *  v1.0 body: 43-46 bend (deg) right arm, left arm (elbow, - = forward), right leg, left leg (knee, + = backward)
 *  47-49 torso about the hip (deg): pitch (+ = lean forward), yaw (twist), roll (side) | 50 mouth open 0..1 | 51 blink 0..1
 * Prop vector (PRN): x,y,z of the block's BOTTOM CENTRE | sx,sy,sz | yaw,pitch,roll (deg, applied Y then X then Z about that point)
 *  sx == 0 hides the prop on that row. Props are rubbery block models drawn with the level's biome tint.
 * Beam vector (BN): x1,y1,z1, x2,y2,z2, r1, r2, alpha, lift (control point up), push_z (control point shift in z),
 *  r,g,b (0..1), style (0 water shimmer, 1 red/white straw stripes, 2 plain colour), segments (0 = auto)
 */
public final class Anim {
    public static final int PN = 52;
    public static final int PRN = 9;
    public static final int BN = 16;

    public static final class ActorDef {
        public String name, skin, item;
        public boolean slim, hat;
        public Face face;
    }

    /** Face rig in face pixels (the skin's 8x8 face; x right, y down): mouth rect, how many px it grows when open, eye rects, lid colour. */
    public static final class Face {
        public float[] mouth;            // x0,y0,x1,y1
        public float mouthOpen = 1f;
        public float[] mouthColor = {0.12f, 0.03f, 0.03f};
        public float[][] eyes;           // [x0,y0,x1,y1]...
        public float[] lid = {0.8f, 0.6f, 0.5f};
        public float z = -0.03f;          // px in front of the face (-0.53 when the face is drawn on the hat layer)
    }

    private static float[] floats(JsonArray a) {
        float[] f = new float[a.size()];
        for (int i = 0; i < f.length; i++) f[i] = a.get(i).getAsFloat();
        return f;
    }

    public static final class MobDef {
        public String name, type;
    }

    public static final class PropDef {
        public String name, block;
    }

    public final List<ActorDef> actors = new ArrayList<>();
    public final List<PropDef> propDefs = new ArrayList<>();
    public final List<MobDef> mobDefs = new ArrayList<>();
    public static final int MBN = 12;   // mob row: centre x,y,z | yaw pitch roll | sx sy sz (world-axis squash) | shadow y | limb swing step | age ticks (0 = frozen; drives tail/fin/wing anims)
    public int[] box = null;          // x0,z0,x1,z1 of the water region
    public int yMin = 0, yMax = 0;
    public double cx = 0, cz = 0;      // funnel centre (blocks)
    public double[] funnel;           // per row: extra surface height per block of distance from the centre
    public double[] water;            // per row, NaN = leave alone
    public double[][][] poses;        // [row][actor][PN]
    public double[][][] beams;        // [row][beam][BN]
    public double[][][] props;        // [row][prop][PRN]
    public double[][][] mobs;         // [row][mob][MBN]

    public static Anim load(Path file) throws IOException {
        JsonObject o;
        try (BufferedReader r = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            o = JsonParser.parseReader(r).getAsJsonObject();
        }
        Anim a = new Anim();
        if (o.has("actors")) for (JsonElement e : o.getAsJsonArray("actors")) {
            JsonObject j = e.getAsJsonObject();
            ActorDef d = new ActorDef();
            d.name = j.get("name").getAsString();
            d.skin = j.get("skin").getAsString();
            d.slim = j.has("slim") && j.get("slim").getAsBoolean();
            d.item = j.has("item") && !j.get("item").isJsonNull() ? j.get("item").getAsString() : null;
            d.hat = j.has("hat") && j.get("hat").getAsBoolean();
            if (j.has("face") && j.get("face").isJsonObject()) {
                JsonObject fj = j.getAsJsonObject("face");
                Face f = new Face();
                if (fj.has("mouth")) f.mouth = floats(fj.getAsJsonArray("mouth"));
                if (fj.has("mouthOpen")) f.mouthOpen = fj.get("mouthOpen").getAsFloat();
                if (fj.has("mouthColor")) f.mouthColor = floats(fj.getAsJsonArray("mouthColor"));
                if (fj.has("lid")) f.lid = floats(fj.getAsJsonArray("lid"));
                if (fj.has("z")) f.z = fj.get("z").getAsFloat();
                if (fj.has("eyes")) {
                    JsonArray ea = fj.getAsJsonArray("eyes");
                    f.eyes = new float[ea.size()][];
                    for (int i = 0; i < ea.size(); i++) f.eyes[i] = floats(ea.get(i).getAsJsonArray());
                }
                d.face = f;
            }
            a.actors.add(d);
        }
        if (o.has("mobs")) for (JsonElement e : o.getAsJsonArray("mobs")) {
            JsonObject j = e.getAsJsonObject();
            MobDef d = new MobDef();
            d.name = j.get("name").getAsString();
            d.type = j.get("type").getAsString();
            a.mobDefs.add(d);
        }
        if (o.has("props")) for (JsonElement e : o.getAsJsonArray("props")) {
            JsonObject j = e.getAsJsonObject();
            PropDef d = new PropDef();
            d.name = j.get("name").getAsString();
            d.block = j.get("block").getAsString();
            a.propDefs.add(d);
        }
        if (o.has("water") && o.get("water").isJsonObject()) {
            JsonObject w = o.getAsJsonObject("water");
            JsonArray b = w.getAsJsonArray("box");
            a.box = new int[]{b.get(0).getAsInt(), b.get(1).getAsInt(), b.get(2).getAsInt(), b.get(3).getAsInt()};
            a.yMin = w.get("yMin").getAsInt();
            a.yMax = w.get("yMax").getAsInt();
            if (w.has("center")) { a.cx = w.getAsJsonArray("center").get(0).getAsDouble(); a.cz = w.getAsJsonArray("center").get(1).getAsDouble(); }
        }
        JsonArray rows = o.getAsJsonArray("rows");
        int n = rows.size();
        a.water = new double[n];
        a.funnel = new double[n];
        a.poses = new double[n][][];
        a.beams = new double[n][][];
        a.props = new double[n][][];
        a.mobs = new double[n][][];
        for (int i = 0; i < n; i++) {
            JsonObject r = rows.get(i).getAsJsonObject();
            a.water[i] = r.has("w") && !r.get("w").isJsonNull() ? r.get("w").getAsDouble() : Double.NaN;
            a.funnel[i] = r.has("f") && !r.get("f").isJsonNull() ? r.get("f").getAsDouble() : 0.0;
            a.poses[i] = grid(r, "a", a.actors.size(), PN);
            a.beams[i] = grid(r, "b", -1, BN);
            a.props[i] = grid(r, "p", a.propDefs.size(), PRN);
            a.mobs[i] = grid(r, "m", a.mobDefs.size(), MBN);
        }
        return a;
    }

    private static double[][] grid(JsonObject r, String key, int expect, int width) {
        if (!r.has(key)) return new double[0][];
        JsonArray arr = r.getAsJsonArray(key);
        double[][] g = new double[arr.size()][width];
        for (int i = 0; i < arr.size(); i++) {
            JsonArray v = arr.get(i).getAsJsonArray();
            for (int k = 0; k < width && k < v.size(); k++) g[i][k] = v.get(k).getAsDouble();
        }
        return g;
    }
}
