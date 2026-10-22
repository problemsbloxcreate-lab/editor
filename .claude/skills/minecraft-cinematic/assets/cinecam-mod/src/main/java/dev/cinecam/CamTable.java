package dev.cinecam;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * Per-sample camera table. One row per render pass (frames * subframes).
 * Columns: t(seconds), x, y, z, yaw, pitch, roll, fov [, ...ignored]. Angles in degrees, Minecraft convention
 * (yaw 0 = +Z/south, +yaw turns clockwise seen from above; pitch +down).
 */
public final class CamTable {
    public final int n;
    public final double[] t, x, y, z, yaw, pitch, roll, fov;

    private CamTable(int n) {
        this.n = n;
        t = new double[n]; x = new double[n]; y = new double[n]; z = new double[n];
        yaw = new double[n]; pitch = new double[n]; roll = new double[n]; fov = new double[n];
    }

    public static CamTable load(Path csv) throws IOException {
        List<String> lines = Files.readAllLines(csv, StandardCharsets.UTF_8);
        int rows = 0;
        for (String l : lines) if (!l.isBlank() && !l.startsWith("t") && !l.startsWith("#")) rows++;
        CamTable c = new CamTable(rows);
        int k = 0;
        for (String l : lines) {
            if (l.isBlank() || l.startsWith("t") || l.startsWith("#")) continue;
            String[] p = l.trim().split(",");
            if (p.length < 8) throw new IOException("camera.csv row " + (k + 1) + " has " + p.length + " columns (need >= 8)");
            c.t[k] = Double.parseDouble(p[0]);
            c.x[k] = Double.parseDouble(p[1]);
            c.y[k] = Double.parseDouble(p[2]);
            c.z[k] = Double.parseDouble(p[3]);
            c.yaw[k] = Double.parseDouble(p[4]);
            c.pitch[k] = Double.parseDouble(p[5]);
            c.roll[k] = Double.parseDouble(p[6]);
            c.fov[k] = Double.parseDouble(p[7]);
            k++;
        }
        return c;
    }

    /** Horizontal bounding box center and radius (blocks) of the whole path. */
    public double[] bounds() {
        double minX = 1e18, maxX = -1e18, minY = 1e18, maxY = -1e18, minZ = 1e18, maxZ = -1e18;
        for (int i = 0; i < n; i++) {
            minX = Math.min(minX, x[i]); maxX = Math.max(maxX, x[i]);
            minY = Math.min(minY, y[i]); maxY = Math.max(maxY, y[i]);
            minZ = Math.min(minZ, z[i]); maxZ = Math.max(maxZ, z[i]);
        }
        return new double[]{minX, maxX, minY, maxY, minZ, maxZ};
    }
}
