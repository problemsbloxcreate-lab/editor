package dev.cinecam;

import net.minecraft.client.Timer;

/**
 * Replaces Minecraft's wall-clock timer so game time advances only when we say so.
 * {@link #schedule(double)} sets how many milliseconds of GAME time the next loop iteration represents.
 * With 0 the world does not tick and partialTick stays put: the same frame can be re-rendered while
 * chunks finish building without the world moving.
 */
public final class FixedTimer extends Timer {
    private double pendingMs = 0;
    private double acc = 0;

    public FixedTimer() {
        super(20.0F, 0L);
    }

    public void schedule(double ms) {
        pendingMs = ms;
    }

    @Override
    public int advanceTime(long ignoredWallClockMs) {
        double ticks = pendingMs / 50.0;
        pendingMs = 0;
        this.tickDelta = (float) ticks;
        acc += ticks;
        int n = (int) Math.floor(acc);
        acc -= n;
        this.partialTick = (float) acc;
        return n;
    }
}
