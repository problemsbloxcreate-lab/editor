package dev.cinecam;

import net.minecraft.client.Minecraft;

import java.util.ArrayList;
import java.util.List;

/**
 * v1.3 (05/11/2026): SERVER commands at an exact FILM time: scene.events = [[t, "command"], ...] (the dragon's End turning
 * red: the exit portal lighting up, the sky preset fading in, a smoke column rising).  The integrated server runs on the
 * wall clock while the film runs on the FixedTimer, so a command is not "at" a film time by itself: when the first pass at or
 * after t starts, every due command is sent to the server thread and the film HOLDS (re-renders the same pass, the world
 * does not tick) for {@link #HOLD_NS} of real time - enough for the server to run them and for their packets (blocks,
 * particles, the preset) to reach and be applied by the client.  Then the pass is captured as usual (chunk readiness
 * included), so the change lands exactly on that frame.  Client-only block changes stay in {@link BlockEvents}.
 */
public final class Events {
    static final long HOLD_NS = 350_000_000L;

    private static double[] t;
    private static String[] cmd;
    private static int next;
    private static long holdUntil;
    private static int fired;

    private Events() {}

    public static void init(List<Double> at, List<String> cmds) {
        reset();
        if (at == null || at.isEmpty()) return;
        Integer[] ord = new Integer[at.size()];
        for (int i = 0; i < ord.length; i++) ord[i] = i;
        java.util.Arrays.sort(ord, (a, b) -> Double.compare(at.get(a), at.get(b)));   // stable: same t keeps list order
        t = new double[ord.length];
        cmd = new String[ord.length];
        for (int k = 0; k < ord.length; k++) { t[k] = at.get(ord[k]); cmd[k] = cmds.get(ord[k]); }
        CineCam.LOG.info("[cinecam] timed events: {}", t.length);
    }

    /** Start of a pass at film time `time`: fires every command due by then (once) and starts a hold. */
    public static void fire(Minecraft mc, double time) {
        if (t == null || next >= t.length || t[next] > time + 1e-6) return;
        var s = mc.getSingleplayerServer();
        if (s == null) return;
        List<String> due = new ArrayList<>();
        while (next < t.length && t[next] <= time + 1e-6) due.add(cmd[next++]);
        fired += due.size();
        s.execute(() -> {
            var players = s.getPlayerList().getPlayers();
            if (players.isEmpty()) return;
            for (String c : due) Controller.run(players.get(0), c);
        });
        holdUntil = System.nanoTime() + HOLD_NS;
        CineCam.LOG.info("[cinecam] t={} s: {} timed command(s), holding the film {} ms", String.format("%.3f", time), due.size(), HOLD_NS / 1_000_000);
    }

    /** True while the film must keep re-rendering the current pass (server commands still travelling). */
    public static boolean holding() {
        if (holdUntil == 0) return false;
        if (System.nanoTime() < holdUntil) return true;
        holdUntil = 0;
        return false;
    }

    public static int fired() {
        return fired;
    }

    public static void reset() {
        t = null;
        cmd = null;
        next = 0;
        holdUntil = 0;
        fired = 0;
    }
}
