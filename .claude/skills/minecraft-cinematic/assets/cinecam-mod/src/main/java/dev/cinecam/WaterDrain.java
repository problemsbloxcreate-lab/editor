package dev.cinecam;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

import java.util.ArrayList;
import java.util.List;

/**
 * Client-side only "the sea goes away": water cells inside the job box are replaced by air from the top.
 * Nothing touches the server world, so there is no flowing/fluid tick fighting the animation.
 * Every cell has its own surface height  h_cell = h + funnel * horizontalDistance(cell, centre)  (funnel > 0 makes a
 * whirlpool-like depression around the centre).  Cell state code: 0 = original, 1 = drained, 10+L = flowing water LEVEL L.
 */
public final class WaterDrain {
    private static final int FLAGS = 2 | 16; // update clients, no neighbour shape updates

    private static long[] pos;
    private static int[] ys;
    private static float[] dist;
    private static BlockState[] orig;
    private static int[] code;
    private static double lastH = Double.NaN, lastF = Double.NaN;

    private WaterDrain() {}

    public static void scan(Minecraft mc, Anim a) {
        if (a.box == null) return;
        ClientLevel lvl = mc.level;
        List<Long> p = new ArrayList<>();
        List<Integer> yy = new ArrayList<>();
        List<Float> dd = new ArrayList<>();
        List<BlockState> ss = new ArrayList<>();
        BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
        int x0 = Math.min(a.box[0], a.box[2]), x1 = Math.max(a.box[0], a.box[2]);
        int z0 = Math.min(a.box[1], a.box[3]), z1 = Math.max(a.box[1], a.box[3]);
        for (int x = x0; x <= x1; x++) for (int z = z0; z <= z1; z++) for (int y = a.yMin; y <= a.yMax; y++) {
            m.set(x, y, z);
            BlockState st = lvl.getBlockState(m);
            if (st.getFluidState().is(FluidTags.WATER)) {
                p.add(m.asLong());
                yy.add(y);
                dd.add((float) Math.hypot(x + 0.5 - a.cx, z + 0.5 - a.cz));
                ss.add(st);
            }
        }
        int n = p.size();
        pos = new long[n]; ys = new int[n]; dist = new float[n]; orig = new BlockState[n]; code = new int[n];
        for (int i = 0; i < n; i++) { pos[i] = p.get(i); ys[i] = yy.get(i); dist[i] = dd.get(i); orig[i] = ss.get(i); }
        CineCam.LOG.info("[cinecam] water scan: {} cells in box {} y {}..{}", n, java.util.Arrays.toString(a.box), a.yMin, a.yMax);
    }

    /** Surface height h (blocks, fractional) at the centre; funnel = extra height per block of distance. */
    public static void apply(Minecraft mc, double h, double funnel) {
        if (pos == null || Double.isNaN(h)) return;
        if (h == lastH && funnel == lastF) return;
        lastH = h; lastF = funnel;
        ClientLevel lvl = mc.level;
        BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
        for (int i = 0; i < pos.length; i++) {
            double hc = h + funnel * dist[i];
            int base = (int) Math.floor(hc);
            double frac = hc - base;
            int y = ys[i];
            int want;
            if (y < base) want = 0;
            else if (y == base && frac >= 0.12) want = 10 + Math.max(1, Math.min(7, 8 - (int) Math.round(frac * 8)));
            else want = 1;
            if (want == code[i]) continue;
            code[i] = want;
            m.set(pos[i]);
            BlockState o = orig[i];
            BlockState ns;
            if (want == 0) ns = o;
            else if (want == 1) ns = drained(o);
            else ns = (o.getBlock() instanceof LiquidBlock) ? Blocks.WATER.defaultBlockState().setValue(LiquidBlock.LEVEL, want - 10) : drained(o);
            if (lvl.getBlockState(m) != ns) lvl.setBlock(m, ns, FLAGS);
        }
    }

    /** Batch: give the previous shot's drained cells their original state back and forget the box. */
    public static void reset(Minecraft mc) {
        if (pos != null && mc.level != null) {
            BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
            for (int i = 0; i < pos.length; i++) if (code[i] != 0) { m.set(pos[i]); mc.level.setBlock(m, orig[i], FLAGS); }
        }
        pos = null; ys = null; dist = null; orig = null; code = null;
        lastH = Double.NaN; lastF = Double.NaN;
    }

    private static BlockState drained(BlockState o) {
        if (o.getBlock() instanceof LiquidBlock) return Blocks.AIR.defaultBlockState();
        if (o.hasProperty(BlockStateProperties.WATERLOGGED)) return o.setValue(BlockStateProperties.WATERLOGGED, false);
        return Blocks.AIR.defaultBlockState(); // kelp, seagrass, bubble columns
    }
}
