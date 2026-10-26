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

/** Parsed job.json. See references/job-schema.md in the skill for the documented format. */
public final class Job {
    public Path file;
    public Path dir;
    public Path outDir;
    public String name = "shot";
    public int width = 1920, height = 1080;
    public double fps = 30;
    /** Samples per output frame, taken from camera.csv (rows = frames * subframes). */
    public int subframes = 1;
    public String ffmpeg = "ffmpeg";
    /** Extra ffmpeg output args after the input (defaults to lossless RGB master). */
    public String codec = "lossless";
    /** Also write a linear-depth stream (gray16, 1/128 block units) for post-process depth of field. */
    public boolean depth = false;

    // world
    public String worldMode = "fresh";          // fresh | copy
    public long seed = 20261015L;
    public String preset = "normal";            // normal | flat
    public boolean structures = true;
    public int groundY = Integer.MIN_VALUE;      // v1.1 (preset flat): chão de grama com o topo nesta altura em TODO o mundo (Shorts: 64)
    public String copyFrom = null;               // absolute path of a save folder (mode=copy)

    // client settings
    public int renderDistance = 16;
    public int simulationDistance = 8;
    public boolean worldTicks = true;            // false = frozen world (still frames), true = clock runs with the film
    public double gamma = 0.5;
    public int mipmap = 4;
    public int biomeBlend = 7;
    public boolean clouds = true;
    public boolean particles = true;
    public List<String> resourcePacks = new ArrayList<>();

    // scene
    public long dayTime = 6000;
    public String weather = "clear";
    public String dimension = "minecraft:overworld";
    public double[] anchor = null;               // x,y,z of the (invisible) player; default = first camera sample
    public List<String> commands = new ArrayList<>();
    public int settleTicks = 100;
    public double sunScale = 1.0;
    public double[] fog = null;                  // v1.1: [perto, longe, r, g, b] (névoa do estúdio do Shorts); null = a do jogo
    public List<double[]> blockAt = new ArrayList<>();   // v1.1: scene.blocks [t, x, y, z, state] = blocos que mudam no meio do plano
    public List<String> blockState = new ArrayList<>();
    public double[] sunTint = {1.0, 0.86, 0.52};  // big-sun colour (vanilla texture path)
    public String sunTexture = null;             // optional RGBA PNG drawn with straight alpha (exact colours)                // >1 draws the vanilla sun texture bigger at the exact vanilla sun position
    public int preloadTimeoutSec = 300;

    // scouting
    public List<Scout.Spec> scoutMaps = new ArrayList<>();
    public List<String> queries = new ArrayList<>();

    // camera table
    public Path cameraCsv;
    // optional actors / water animation table (anim.json), rows aligned with camera.csv
    public Path animFile = null;
    // batch (v0.8): more shots rendered in this same game session, same world, one after the other
    public List<Path> next = new ArrayList<>();
    public Path inbox = null;                    // v1.1 live session: when the queue empties, wait here for "<n>.go" files (path of the next job)
    public int idleSec = 900;                    // ...and quit after this long with nothing to do (or when "<inbox>/stop" appears)
    public String mode = null;                   // film | stills | scout (overrides -Pmode for this shot)

    public static Job load(Path file) throws IOException {
        Job j = new Job();
        j.file = file.toAbsolutePath();
        j.dir = j.file.getParent();
        JsonObject o;
        try (BufferedReader r = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            o = JsonParser.parseReader(r).getAsJsonObject();
        }
        j.name = str(o, "name", j.name);
        j.outDir = Path.of(str(o, "out", j.dir.resolve("out").toString()));
        j.width = i(o, "width", j.width);
        j.height = i(o, "height", j.height);
        j.fps = d(o, "fps", j.fps);
        j.subframes = Math.max(1, i(o, "subframes", j.subframes));
        j.ffmpeg = str(o, "ffmpeg", j.ffmpeg);
        j.codec = str(o, "codec", j.codec);
        j.depth = b(o, "depth", j.depth);

        JsonObject w = obj(o, "world");
        if (w != null) {
            j.worldMode = str(w, "mode", j.worldMode);
            j.seed = (long) d(w, "seed", j.seed);
            j.preset = str(w, "preset", j.preset);
            j.structures = b(w, "structures", j.structures);
            j.groundY = i(w, "groundY", j.groundY);
            j.copyFrom = str(w, "copyFrom", null);
        }
        JsonObject s = obj(o, "settings");
        if (s != null) {
            j.renderDistance = i(s, "renderDistance", j.renderDistance);
            j.simulationDistance = i(s, "simulationDistance", j.simulationDistance);
            j.worldTicks = b(s, "worldTicks", j.worldTicks);
            j.gamma = d(s, "gamma", j.gamma);
            j.mipmap = i(s, "mipmap", j.mipmap);
            j.biomeBlend = i(s, "biomeBlend", j.biomeBlend);
            j.clouds = b(s, "clouds", j.clouds);
            j.particles = b(s, "particles", j.particles);
            JsonArray rp = arr(s, "resourcePacks");
            if (rp != null) for (JsonElement e : rp) j.resourcePacks.add(e.getAsString());
        }
        JsonObject sc = obj(o, "scene");
        if (sc != null) {
            j.dayTime = (long) d(sc, "time", j.dayTime);
            j.weather = str(sc, "weather", j.weather);
            j.dimension = str(sc, "dimension", j.dimension);
            j.settleTicks = i(sc, "settleTicks", j.settleTicks);
            j.sunScale = d(sc, "sunScale", j.sunScale);
            if (sc.has("fog") && sc.get("fog").isJsonArray()) { var fa = sc.getAsJsonArray("fog"); j.fog = new double[fa.size()]; for (int i = 0; i < fa.size(); i++) j.fog[i] = fa.get(i).getAsDouble(); }
            JsonArray be = arr(sc, "blocks");
            if (be != null) for (JsonElement e : be) {
                JsonArray a = e.getAsJsonArray();
                j.blockAt.add(new double[]{a.get(0).getAsDouble(), a.get(1).getAsDouble(), a.get(2).getAsDouble(), a.get(3).getAsDouble()});
                j.blockState.add(a.get(4).getAsString());
            }
            j.sunTexture = str(sc, "sunTexture", j.sunTexture);
            JsonArray st = arr(sc, "sunTint");
            if (st != null && st.size() >= 3) j.sunTint = new double[]{st.get(0).getAsDouble(), st.get(1).getAsDouble(), st.get(2).getAsDouble()};
            j.preloadTimeoutSec = i(sc, "preloadTimeoutSec", j.preloadTimeoutSec);
            JsonArray a = arr(sc, "anchor");
            if (a != null && a.size() >= 3) j.anchor = new double[]{a.get(0).getAsDouble(), a.get(1).getAsDouble(), a.get(2).getAsDouble()};
            JsonArray cm = arr(sc, "commands");
            if (cm != null) for (JsonElement e : cm) j.commands.add(e.getAsString());
        }
        JsonObject sct = obj(o, "scout");
        if (sct != null) {
            JsonArray maps = arr(sct, "maps");
            if (maps != null) for (JsonElement e : maps) {
                JsonObject m = e.getAsJsonObject();
                Scout.Spec sp = new Scout.Spec();
                sp.name = str(m, "name", "map");
                sp.x0 = i(m, "x0", 0); sp.z0 = i(m, "z0", 0); sp.x1 = i(m, "x1", 64); sp.z1 = i(m, "z1", 64);
                sp.step = i(m, "step", 2); sp.generate = b(m, "generate", false);
                j.scoutMaps.add(sp);
            }
            JsonArray qs = arr(sct, "queries");
            if (qs != null) for (JsonElement e : qs) j.queries.add(e.getAsString());
        }
        String cam = str(o, "camera", "camera.csv");
        Path cp = Path.of(cam);
        j.cameraCsv = cp.isAbsolute() ? cp : j.dir.resolve(cam);
        String an = str(o, "anim", null);
        if (an != null) j.animFile = Path.of(an).isAbsolute() ? Path.of(an) : j.dir.resolve(an);
        JsonArray nx = arr(o, "next");
        if (nx != null) for (JsonElement e : nx) j.next.add(Path.of(e.getAsString()));
        j.mode = str(o, "mode", null);
        String ib = str(o, "inbox", null);
        if (ib != null) j.inbox = Path.of(ib);
        if (o.has("idleSec")) j.idleSec = o.get("idleSec").getAsInt();
        return j;
    }

    private static JsonObject obj(JsonObject o, String k) { return o.has(k) && o.get(k).isJsonObject() ? o.getAsJsonObject(k) : null; }
    private static JsonArray arr(JsonObject o, String k) { return o.has(k) && o.get(k).isJsonArray() ? o.getAsJsonArray(k) : null; }
    private static String str(JsonObject o, String k, String def) { return o.has(k) && !o.get(k).isJsonNull() ? o.get(k).getAsString() : def; }
    private static int i(JsonObject o, String k, int def) { return o.has(k) ? o.get(k).getAsInt() : def; }
    private static double d(JsonObject o, String k, double def) { return o.has(k) ? o.get(k).getAsDouble() : def; }
    private static boolean b(JsonObject o, String k, boolean def) { return o.has(k) ? o.get(k).getAsBoolean() : def; }
}
