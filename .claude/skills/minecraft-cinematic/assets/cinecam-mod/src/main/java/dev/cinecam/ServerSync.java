package dev.cinecam;

import net.minecraft.server.MinecraftServer;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.concurrent.atomic.AtomicLong;

/**
 * v1.4 (18/11/2026): the integrated SERVER in lockstep with the FILM clock (scene.serverSync = true).
 * By default the server runs on the wall clock while the film runs on the FixedTimer (a 1080p60 film is rendered several
 * times slower than real time), so anything the server animates - a mod's tsunami wall, blocks melting on a timer, a mob
 * with AI, an explosion - plays far too fast in the film.  With serverSync the server thread waits at the start of every
 * tick until the film has reached that tick (film second t = server tick floor(t * 20)), and the film holds the current
 * pass until the server has finished the ticks it owes and their packets were applied by the client.  Server tasks
 * (commands, packets) still run while it waits.  Off = nothing changes.
 */
@Mod.EventBusSubscriber(modid = CineCam.MOD_ID)
public final class ServerSync {
    private static volatile boolean on;
    private static final AtomicLong granted = new AtomicLong();
    private static final AtomicLong done = new AtomicLong();
    private static volatile int settle;          // extra film passes after the server caught up (packets -> client -> chunk rebuild)
    private static long holdStartNs;
    private static int stalls;
    private static volatile long bonus;

    private ServerSync() {}

    public static void start() {
        granted.set(0);
        bonus = 0;
        done.set(0);
        settle = 0;
        stalls = 0;
        holdStartNs = 0;
        on = true;
        CineCam.LOG.info("[cinecam] serverSync ON: server ticks follow the film clock");
    }

    public static void stop() {
        if (on) CineCam.LOG.info("[cinecam] serverSync OFF ({} server ticks in the film, {} stalls)", done.get(), stalls);
        on = false;
    }

    public static boolean active() {
        return on;
    }

    /** Start of a film pass at time t (s): the server may run up to tick floor(t * 20). */
    public static void need(double t) {
        if (!on) return;
        long n = (long) Math.floor(t * 20.0 + 1e-6) + bonus;
        if (n > granted.get()) {
            granted.set(n);
            settle = 2;
        }
    }

    /** The film is stuck waiting for chunks (the camera crossed a chunk border and the server has to send the new edge): the frozen
     *  server would never send them.  One free tick, off the film clock (the mechanics drift 50 ms; a deadlock costs 40 s a row). */
    public static void extra() {
        if (!on || done.get() < granted.get()) return;
        bonus++;
        granted.incrementAndGet();
    }

    /** True while the film must re-render the same pass: the server still owes ticks, or their packets are still landing. */
    public static boolean holding() {
        if (!on) return false;
        if (done.get() < granted.get()) {
            if (holdStartNs == 0) holdStartNs = System.nanoTime();
            if ((System.nanoTime() - holdStartNs) / 1e9 > 20.0) {       // server stuck (crash/pause): do not hang the film forever
                stalls++;
                CineCam.LOG.warn("[cinecam] serverSync: server did not reach tick {} in 20 s (at {}); going on", granted.get(), done.get());
                done.set(granted.get());
                holdStartNs = 0;
                return false;
            }
            return true;
        }
        holdStartNs = 0;
        if (settle > 0) { settle--; return true; }
        return false;
    }

    @SubscribeEvent
    public static void serverTick(TickEvent.ServerTickEvent e) {
        if (!on) return;
        if (e.phase == TickEvent.Phase.END) { done.incrementAndGet(); return; }
        MinecraftServer s = e.getServer();
        long t0 = System.nanoTime();
        // managedBlock runs the queued server tasks (commands of scene.events, packets) even though the server is "late";
        // the chunk tasks are polled by hand because the vanilla loop only runs them while it "has time".
        s.managedBlock(() -> {
            if (!on || done.get() < granted.get() || (System.nanoTime() - t0) / 1e9 > 600.0) return true;
            try { for (net.minecraft.server.level.ServerLevel l : s.getAllLevels()) l.getChunkSource().pollTask(); } catch (Throwable ignored) { }
            return false;
        });
    }
}
