package dev.cinecam;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.minecraft.client.model.geom.ModelPart;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Vector4f;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/**
 * v1.0 (25/10/2026) "corpo que dobra": arms and legs as ONE continuous mesh that bends at the elbow/knee (like Mine-imator's
 * bend and the Shorts web studio's dobraMesh), the torso turning about the hip, and a tiny face rig (mouth open, blink).
 *
 * Geometry and UVs are read from the vanilla ModelPart cubes themselves (reflection by TYPE, so dev and SRG names both work),
 * so a skin looks exactly as in-game when every bend is 0. Side faces are cut into rings across the bend arc; the arc follows a
 * circle of length {@link #ARC} px centred at the middle of the limb, the part above it stays put and the part below turns
 * rigidly by the bend angle (about model X: negative = toward the front, like an elbow; positive = backward, like a knee).
 */
public final class Body {
    private Body() {}

    /** Arc length (model px) of the elbow/knee. 4 px keeps the inner side from pinching up to ~120 degrees on a 4 px limb. */
    public static final float ARC = 4f;
    private static final float[] RING_T = {0f, 1f / 6f, 2f / 6f, 3f / 6f, 4f / 6f, 5f / 6f, 1f};

    /** One face of a part in model pixels: 4 corners (pos + uv) and the vanilla normal. */
    static final class Quad {
        final float[][] p = new float[4][3];
        final float[][] uv = new float[4][2];
        final float[] n = new float[3];
    }

    static final class Part {
        final List<Quad> quads = new ArrayList<>();
        float minY = Float.MAX_VALUE, maxY = -Float.MAX_VALUE;
        float yc() { return (minY + maxY) * 0.5f; }
    }

    private static final Map<ModelPart, Part> CACHE = new IdentityHashMap<>();
    private static Field fCubes, fPolys, fVerts, fNormal, fPos;
    private static Field[] fUV;

    public static void clear() { CACHE.clear(); }

    /** The part's own cubes as quads (cached per ModelPart instance). */
    static Part part(ModelPart mp) {
        Part cached = CACHE.get(mp);
        if (cached != null) return cached;
        Part out = new Part();
        try {
            if (fCubes == null) {
                for (Field f : ModelPart.class.getDeclaredFields())
                    if (List.class.isAssignableFrom(f.getType())) { fCubes = f; f.setAccessible(true); break; }
            }
            List<?> cubes = (List<?>) fCubes.get(mp);
            for (Object cube : cubes) {
                if (fPolys == null) {
                    for (Field f : cube.getClass().getDeclaredFields())
                        if (f.getType().isArray()) { fPolys = f; f.setAccessible(true); break; }
                }
                Object[] polys = (Object[]) fPolys.get(cube);
                for (Object poly : polys) {
                    if (fVerts == null) {
                        for (Field f : poly.getClass().getDeclaredFields()) {
                            if (f.getType().isArray()) { fVerts = f; f.setAccessible(true); }
                            else if (f.getType() == Vector3f.class) { fNormal = f; f.setAccessible(true); }
                        }
                    }
                    Object[] verts = (Object[]) fVerts.get(poly);
                    Vector3f nv = (Vector3f) fNormal.get(poly);
                    if (fPos == null) {
                        List<Field> fl = new ArrayList<>();
                        for (Field f : verts[0].getClass().getDeclaredFields()) {
                            if (java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
                            if (f.getType() == Vector3f.class) { fPos = f; f.setAccessible(true); }
                            else if (f.getType() == float.class) { f.setAccessible(true); fl.add(f); }
                        }
                        fUV = fl.toArray(new Field[0]);   // declaration order: u, v
                    }
                    Quad q = new Quad();
                    for (int k = 0; k < 4; k++) {
                        Vector3f pos = (Vector3f) fPos.get(verts[k]);
                        q.p[k][0] = pos.x(); q.p[k][1] = pos.y(); q.p[k][2] = pos.z();
                        q.uv[k][0] = fUV[0].getFloat(verts[k]); q.uv[k][1] = fUV[1].getFloat(verts[k]);
                        out.minY = Math.min(out.minY, pos.y()); out.maxY = Math.max(out.maxY, pos.y());
                    }
                    q.n[0] = nv.x(); q.n[1] = nv.y(); q.n[2] = nv.z();
                    out.quads.add(q);
                }
            }
        } catch (Exception e) {
            CineCam.LOG.error("[cinecam] body: cannot read model cubes", e);
        }
        CACHE.put(mp, out);
        return out;
    }

    /** Bend deformation of a model-px point; yc = joint centre, a = angle (rad). Writes into out[0..2]. Returns the local angle. */
    static float deform(float x, float y, float z, float yc, float a, float[] out) {
        float s0 = yc - ARC * 0.5f, s1 = yc + ARC * 0.5f;
        if (Math.abs(a) < 1e-5f || y <= s0) { out[0] = x; out[1] = y; out[2] = z; return 0f; }
        float k = a / ARC;
        if (y < s1) {
            float ph = k * (y - s0), s = (float) Math.sin(ph), c = (float) Math.cos(ph);
            float cy = s0 + s / k, cz = (1f - c) / k;
            out[0] = x; out[1] = cy - z * s; out[2] = cz + z * c;
            return ph;
        }
        float s = (float) Math.sin(a), c = (float) Math.cos(a);
        float cy = s0 + s / k, cz = (1f - c) / k, e = y - s1;
        out[0] = x; out[1] = cy + e * c - z * s; out[2] = cz + e * s + z * c;
        return a;
    }

    /**
     * Draws a part (already positioned with mp.translateAndRotate) bent by angle a (radians). Leaves the PoseStack as it found it.
     */
    static void drawBent(PoseStack ps, VertexConsumer vc, ModelPart mp, float a, int light, int overlay, float r, float g, float b, float alpha) {
        if (!mp.visible) return;
        Part pt = part(mp);
        ps.pushPose();
        mp.translateAndRotate(ps);
        PoseStack.Pose pose = ps.last();
        Matrix4f m = pose.pose();
        Matrix3f nm = pose.normal();
        float yc = pt.yc();
        float[] d = new float[3];
        float[][] P = new float[4][3];
        float[][] UV = new float[4][2];
        for (Quad q : pt.quads) {
            boolean side = Math.abs(q.n[1]) < 0.5f;
            if (!side || Math.abs(a) < 1e-5f) { emit(vc, m, nm, q.p, q.uv, q.n, yc, a, light, overlay, r, g, b, alpha, d); continue; }
            // top/bottom edge of this side face and, for each corner, its partner on the other edge (adjacent with different y)
            float yTop = Float.MAX_VALUE, yBot = -Float.MAX_VALUE;
            for (float[] v : q.p) { yTop = Math.min(yTop, v[1]); yBot = Math.max(yBot, v[1]); }
            boolean[] top = new boolean[4];
            for (int k = 0; k < 4; k++) top[k] = q.p[k][1] < (yTop + yBot) * 0.5f;
            int[] partner = new int[4];
            for (int k = 0; k < 4; k++) { int nx = (k + 1) & 3, pv = (k + 3) & 3; partner[k] = top[nx] != top[k] ? nx : pv; }
            float s0 = yc - ARC * 0.5f, H = yBot - yTop;
            float[] ys = new float[RING_T.length + 2];
            int ny = 0;
            ys[ny++] = yTop;
            for (float t : RING_T) { float y = s0 + t * ARC; if (y > yTop + 1e-3f && y < yBot - 1e-3f) ys[ny++] = y; }
            ys[ny++] = yBot;
            for (int i = 0; i + 1 < ny; i++) {
                float ta = (ys[i] - yTop) / H, tb = (ys[i + 1] - yTop) / H;
                for (int k = 0; k < 4; k++) {
                    int tk = top[k] ? k : partner[k], bk = top[k] ? partner[k] : k;
                    float t = top[k] ? ta : tb;
                    for (int c = 0; c < 3; c++) P[k][c] = q.p[tk][c] + (q.p[bk][c] - q.p[tk][c]) * t;
                    for (int c = 0; c < 2; c++) UV[k][c] = q.uv[tk][c] + (q.uv[bk][c] - q.uv[tk][c]) * t;
                }
                emit(vc, m, nm, P, UV, q.n, yc, a, light, overlay, r, g, b, alpha, d);
            }
        }
        ps.popPose();
    }

    private static void emit(VertexConsumer vc, Matrix4f m, Matrix3f nm, float[][] p, float[][] uv, float[] n0, float yc, float a,
                             int light, int overlay, float r, float g, float b, float alpha, float[] d) {
        float[][] w = new float[4][3];
        float phSum = 0;
        for (int k = 0; k < 4; k++) { phSum += deform(p[k][0], p[k][1], p[k][2], yc, a, d); w[k][0] = d[0]; w[k][1] = d[1]; w[k][2] = d[2]; }
        // normal: the vanilla one turned by the mean bend of the quad (flat shading, matches the in-game look)
        float ph = phSum / 4f, s = (float) Math.sin(ph), c = (float) Math.cos(ph);
        Vector3f nv = new Vector3f(n0[0], n0[1] * c - n0[2] * s, n0[1] * s + n0[2] * c);
        nm.transform(nv);
        for (int k = 0; k < 4; k++) {
            Vector4f v = m.transform(new Vector4f(w[k][0] / 16f, w[k][1] / 16f, w[k][2] / 16f, 1f));
            vc.vertex(v.x(), v.y(), v.z(), r, g, b, alpha, uv[k][0], uv[k][1], overlay, light, nv.x(), nv.y(), nv.z());
        }
    }

    /** After mp.translateAndRotate: moves the PoseStack into the frame of the part BELOW the bend (hand / foot end). */
    static void lowerFrame(PoseStack ps, ModelPart mp, float a) {
        if (Math.abs(a) < 1e-5f) return;
        Part pt = part(mp);
        float yc = pt.yc(), s0 = yc - ARC * 0.5f, s1 = yc + ARC * 0.5f, k = a / ARC;
        float cy = s0 + (float) Math.sin(a) / k, cz = (1f - (float) Math.cos(a)) / k;
        ps.translate(0, cy / 16f, cz / 16f);
        ps.mulPose(Axis.XP.rotation(a));
        ps.translate(0, -s1 / 16f, 0);
    }

    /** Torso turn about the hip (model px y = 12): yaw (twist), then pitch (lean, + = forward), then roll (side), all in degrees. */
    static void torso(PoseStack ps, double tx, double ty, double tz) {
        if (tx == 0 && ty == 0 && tz == 0) return;
        ps.translate(0, 12f / 16f, 0);
        if (ty != 0) ps.mulPose(Axis.YP.rotationDegrees((float) ty));
        if (tx != 0) ps.mulPose(Axis.XP.rotationDegrees((float) tx));
        if (tz != 0) ps.mulPose(Axis.ZP.rotationDegrees((float) tz));
        ps.translate(0, -12f / 16f, 0);
    }

    /**
     * Face rig on the head's front (call with the PoseStack at the head: head.translateAndRotate). Coordinates are face pixels
     * (0..8, as in the skin's 8x8 face, x to the right of the image, y down). The face plane and its mirroring come from the
     * vanilla head cube's front polygon, so this works for any head pose.
     */
    static void face(PoseStack ps, VertexConsumer vc, ModelPart head, Anim.Face f, float mouth, float blink, int light) {
        if (f == null || (mouth < 0.04f && blink < 0.04f)) return;
        Quad front = null;
        for (Quad q : part(head).quads) if (q.n[2] < -0.5f) { front = q; break; }
        if (front == null) return;
        // corner with min u/min v, and the edge vectors per face pixel
        int i00 = 0;
        for (int k = 1; k < 4; k++) if (front.uv[k][0] + front.uv[k][1] < front.uv[i00][0] + front.uv[i00][1]) i00 = k;
        float u0 = front.uv[i00][0], v0 = front.uv[i00][1];
        float[] du = null, dv = null;
        for (int k = 0; k < 4; k++) {
            if (k == i00) continue;
            float eu = front.uv[k][0] - u0, ev = front.uv[k][1] - v0;
            float[] e = {front.p[k][0] - front.p[i00][0], front.p[k][1] - front.p[i00][1], front.p[k][2] - front.p[i00][2]};
            if (Math.abs(eu) > 1e-6f && Math.abs(ev) < 1e-6f) du = new float[]{e[0] / (eu * 64f), e[1] / (eu * 64f), e[2] / (eu * 64f)};
            if (Math.abs(ev) > 1e-6f && Math.abs(eu) < 1e-6f) dv = new float[]{e[0] / (ev * 64f), e[1] / (ev * 64f), e[2] / (ev * 64f)};
        }
        if (du == null || dv == null) return;
        float[] o = front.p[i00];
        ps.pushPose();
        head.translateAndRotate(ps);
        PoseStack.Pose pose = ps.last();
        float zOff = f.z;   // just in front of the face (or of the hat layer when the face is drawn there)
        if (mouth >= 0.04f && f.mouth != null) {
            float x0 = f.mouth[0], y0 = f.mouth[1], x1 = f.mouth[2], y1 = f.mouth[3] + mouth * f.mouthOpen;
            rect(vc, pose, o, du, dv, zOff, x0, y0, x1, y1, f.mouthColor, light);
        }
        if (blink >= 0.04f && f.eyes != null) {
            for (float[] e : f.eyes) {
                float h = (e[3] - e[1]) * Math.min(1f, blink);
                rect(vc, pose, o, du, dv, zOff - 0.02f, e[0] - 0.02f, e[1] - 0.02f, e[2] + 0.02f, e[1] + h + 0.02f, f.lid, light);
            }
        }
        ps.popPose();
    }

    private static void rect(VertexConsumer vc, PoseStack.Pose pose, float[] o, float[] du, float[] dv, float zOff,
                             float x0, float y0, float x1, float y1, float[] col, int light) {
        float[][] c = {{x0, y0}, {x0, y1}, {x1, y1}, {x1, y0}};
        Vector3f nv = new Vector3f(0, 0, -1);
        pose.normal().transform(nv);
        for (float[] q : c) {
            float px = o[0] + du[0] * q[0] + dv[0] * q[1], py = o[1] + du[1] * q[0] + dv[1] * q[1], pz = o[2] + du[2] * q[0] + dv[2] * q[1] + zOff;
            Vector4f v = pose.pose().transform(new Vector4f(px / 16f, py / 16f, pz / 16f, 1f));
            vc.vertex(v.x(), v.y(), v.z(), col[0], col[1], col[2], 1f, 0.5f, 0.5f, net.minecraft.client.renderer.texture.OverlayTexture.NO_OVERLAY, light, nv.x(), nv.y(), nv.z());
        }
    }
}
