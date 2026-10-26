package dev.cinecam;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * v1.1: blocks that change DURING the shot (the Shorts studio opens the base door in "leaveBase"): scene.blocks =
 * [[t, x, y, z, "minecraft:oak_door[...,open=true]"], ...].  Client side only, like WaterDrain: every pass shows, for each
 * position, the state of the latest event with t <= pass time (or the world's own state before the first one); the
 * original states come back when the shot ends, so a live session's next shot starts from the world as built.
 */
public final class BlockEvents {
    private static final int FLAGS = 2 | 16; // update clients, no neighbour shape updates (the two door halves come as two events)

    private static long[] pos;
    private static double[] t;
    private static BlockState[] st;
    private static final Map<Long, BlockState> ORIG = new HashMap<>();
    private static final Map<Long, BlockState> NOW = new HashMap<>();

    private BlockEvents() {}

    public static void init(Minecraft mc, List<double[]> at, List<String> states) {
        reset(mc);
        if (at == null || at.isEmpty()) return;
        List<Integer> ok = new ArrayList<>();
        BlockState[] parsed = new BlockState[at.size()];
        for (int i = 0; i < at.size(); i++) {
            try {
                parsed[i] = BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK.asLookup(), states.get(i), false).blockState();
                ok.add(i);
            } catch (Exception ex) {
                CineCam.LOG.warn("[cinecam] block event {} ignored: {}", states.get(i), ex.toString());
            }
        }
        // stable by time: later events win at the same t
        ok.sort((a, b) -> Double.compare(at.get(a)[0], at.get(b)[0]));
        int n = ok.size();
        pos = new long[n]; t = new double[n]; st = new BlockState[n];
        for (int k = 0; k < n; k++) {
            double[] e = at.get(ok.get(k));
            t[k] = e[0];
            pos[k] = BlockPos.asLong((int) Math.floor(e[1]), (int) Math.floor(e[2]), (int) Math.floor(e[3]));
            st[k] = parsed[ok.get(k)];
        }
        CineCam.LOG.info("[cinecam] block events: {}", n);
    }

    /** Pass time (s): every touched position shows its latest event at or before `time`. */
    public static void apply(Minecraft mc, double time) {
        if (pos == null || pos.length == 0) return;
        ClientLevel lvl = mc.level;
        if (lvl == null) return;
        Map<Long, BlockState> want = new HashMap<>();
        for (int k = 0; k < pos.length; k++) {
            if (!ORIG.containsKey(pos[k])) ORIG.put(pos[k], lvl.getBlockState(BlockPos.of(pos[k])));
            if (t[k] <= time + 1e-6) want.put(pos[k], st[k]);
        }
        for (Map.Entry<Long, BlockState> o : ORIG.entrySet()) {
            BlockState w = want.getOrDefault(o.getKey(), o.getValue());
            if (NOW.get(o.getKey()) == w) continue;
            NOW.put(o.getKey(), w);
            BlockPos p = BlockPos.of(o.getKey());
            if (lvl.getBlockState(p) != w) lvl.setBlock(p, w, FLAGS);
        }
    }

    /** End of shot: put the original states back and forget the events. */
    public static void reset(Minecraft mc) {
        if (mc.level != null) {
            for (Map.Entry<Long, BlockState> o : ORIG.entrySet()) {
                BlockPos p = BlockPos.of(o.getKey());
                if (mc.level.getBlockState(p) != o.getValue()) mc.level.setBlock(p, o.getValue(), FLAGS);
            }
        }
        ORIG.clear(); NOW.clear();
        pos = null; t = null; st = null;
    }
}
