package dev.cinecam;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.commands.CommandSource;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkStatus;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec2;
import net.minecraft.world.phys.Vec3;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Terrain scouting for camera planning: height/colour/biome grids and command-output queries (/locate...). */
public final class Scout {
    private Scout() {}

    public static final class Spec {
        public String name = "map";
        public int x0, z0, x1, z1, step = 2;
        public boolean generate = false;   // true = force-generate missing chunks (slow, synchronous)
    }

    /** Collects command feedback so /locate results can be read back. */
    private static final class Collector implements CommandSource {
        final List<String> lines = new ArrayList<>();
        @Override public void sendSystemMessage(Component c) { lines.add(c.getString()); }
        @Override public boolean acceptsSuccess() { return true; }
        @Override public boolean acceptsFailure() { return true; }
        @Override public boolean shouldInformAdmins() { return false; }
    }

    public static void queries(ServerPlayer p, List<String> cmds, Path outFile) throws IOException {
        JsonObject root = new JsonObject();
        for (String raw : cmds) {
            String c = raw.startsWith("/") ? raw.substring(1) : raw;
            Collector col = new Collector();
            CommandSourceStack src = new CommandSourceStack(col, p.position(), Vec2.ZERO, p.serverLevel(), 4, "cinecam", Component.literal("cinecam"), p.server, p);
            try {
                p.server.getCommands().performPrefixedCommand(src, c);
            } catch (Throwable t) {
                col.lines.add("ERROR " + t);
            }
            JsonArray a = new JsonArray();
            col.lines.forEach(a::add);
            root.add(raw, a);
            CineCam.LOG.info("[cinecam] query '{}' -> {}", raw, col.lines);
        }
        Files.writeString(outFile, root.toString(), StandardCharsets.UTF_8);
    }

    public static void map(ServerPlayer p, Spec s, Path outFile) throws IOException {
        ServerLevel level = p.serverLevel();
        int step = Math.max(1, s.step);
        int w = (s.x1 - s.x0) / step + 1, h = (s.z1 - s.z0) / step + 1;
        int[] surface = new int[w * h], ground = new int[w * h], floor = new int[w * h], rgb = new int[w * h], biome = new int[w * h];
        List<String> biomes = new ArrayList<>();
        Map<String, Integer> biomeIdx = new LinkedHashMap<>();
        int missing = 0;
        for (int iz = 0; iz < h; iz++) {
            for (int ix = 0; ix < w; ix++) {
                int x = s.x0 + ix * step, z = s.z0 + iz * step, k = iz * w + ix;
                ChunkAccess ch = level.getChunkSource().getChunk(x >> 4, z >> 4, ChunkStatus.FULL, s.generate);
                if (ch == null) {
                    surface[k] = ground[k] = floor[k] = -999;
                    biome[k] = -1;
                    missing++;
                    continue;
                }
                int ys = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
                int yg = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
                int yf = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
                surface[k] = ys; ground[k] = yg; floor[k] = yf;
                BlockPos top = new BlockPos(x, ys - 1, z);
                BlockState st = level.getBlockState(top);
                rgb[k] = st.getMapColor(level, top).col;
                String b = level.getBiome(top).unwrapKey().map(r -> r.location().toString()).orElse("unknown");
                biome[k] = biomeIdx.computeIfAbsent(b, kk -> { biomes.add(kk); return biomes.size() - 1; });
            }
        }
        JsonObject o = new JsonObject();
        o.addProperty("name", s.name);
        o.addProperty("x0", s.x0); o.addProperty("z0", s.z0); o.addProperty("step", step);
        o.addProperty("w", w); o.addProperty("h", h); o.addProperty("missing", missing);
        o.add("surface", arr(surface)); o.add("ground", arr(ground)); o.add("floor", arr(floor));
        o.add("rgb", arr(rgb)); o.add("biome", arr(biome));
        JsonArray bn = new JsonArray();
        biomes.forEach(bn::add);
        o.add("biomes", bn);
        Files.writeString(outFile, o.toString(), StandardCharsets.UTF_8);
        CineCam.LOG.info("[cinecam] scout '{}' {}x{} cells ({} unloaded) -> {}", s.name, w, h, missing, outFile);
    }

    private static JsonArray arr(int[] v) {
        JsonArray a = new JsonArray();
        for (int x : v) a.add(x);
        return a;
    }
}
