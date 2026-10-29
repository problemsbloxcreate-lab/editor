package dev.cinecam;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.client.renderer.block.ModelBlockRenderer;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.Items;
import net.minecraft.client.renderer.entity.EntityRenderDispatcher;
import net.minecraftforge.client.RenderTypeHelper;
import net.minecraftforge.client.model.data.ModelData;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Draws posed player-model "actors" (any skin PNG) and water beams straight into the level render, one pose per pass.
 * Nothing here exists in the world: no entity, no AI, no server involvement - the Python rig is the only animator.
 */
public final class Actors {
    private static final ResourceLocation WHITE = new ResourceLocation("minecraft", "textures/misc/white.png");
    private static final float D2R = (float) (Math.PI / 180.0);

    private static final class Rt {
        Anim.ActorDef def;
        ResourceLocation tex;
        float[][][] front = new float[8][12][3];   // torso front colours (skin + jacket layer) for the voxel belly
        PlayerModel<AbstractClientPlayer> model;
        ItemStack stack = ItemStack.EMPTY;
        BakedModel itemModel;           // "model:ns:path" items (models registered by CineCam) instead of a registry item
        float rax, lax, ray, lay, raz, laz; // default arm pivots
    }

    private static final List<Rt> rts = new ArrayList<>();

    private static final class PropRt {
        BlockState state;
        BakedModel model;
    }

    private static final List<PropRt> props = new ArrayList<>();

    private static final class MobRt {
        Entity e;
        float pivot, radius;
    }

    private static final List<MobRt> mobs = new ArrayList<>();
    private static final ResourceLocation SHADOW = new ResourceLocation("minecraft", "textures/misc/shadow.png");

    private Actors() {}

    private static int gen;                  // batch: every shot registers its skins under fresh texture ids

    public static void init(Minecraft mc, Anim a) throws Exception {
        rts.clear();
        Body.clear();
        gen++;
        int k = 0;
        for (Anim.ActorDef d : a.actors) {
            Rt r = new Rt();
            r.def = d;
            try (InputStream in = Files.newInputStream(Path.of(d.skin))) {
                NativeImage img = NativeImage.read(in);
                for (int cx = 0; cx < 8; cx++) for (int cy = 0; cy < 12; cy++) {
                    int c = img.getPixelRGBA(20 + cx, 20 + cy);
                    if (img.getHeight() == 64) { int o = img.getPixelRGBA(20 + cx, 36 + cy); if (((o >>> 24) & 255) > 127) c = o; }
                    r.front[cx][cy][0] = (c & 255) / 255f; r.front[cx][cy][1] = ((c >> 8) & 255) / 255f; r.front[cx][cy][2] = ((c >> 16) & 255) / 255f;
                }
                if (img.getHeight() == 32) CineCam.LOG.warn("[cinecam] skin {} is legacy 64x32; limbs will look wrong", d.skin);
                r.tex = new ResourceLocation("cinecam", "actor/" + gen + "_" + k + "_" + d.name.toLowerCase().replaceAll("[^a-z0-9_]", "_"));
                mc.getTextureManager().register(r.tex, new DynamicTexture(img));
            }
            r.model = new PlayerModel<>(mc.getEntityModels().bakeLayer(d.slim ? ModelLayers.PLAYER_SLIM : ModelLayers.PLAYER), d.slim);
            r.model.setAllVisible(true);
            r.model.young = false;
            r.rax = r.model.rightArm.x;
            r.lax = r.model.leftArm.x;
            r.ray = r.model.rightArm.y; r.lay = r.model.leftArm.y;
            r.raz = r.model.rightArm.z; r.laz = r.model.leftArm.z;
            if (d.item != null && d.item.startsWith("model:")) {
                r.itemModel = mc.getModelManager().getModel(new ResourceLocation(d.item.substring(6)));
                r.stack = new ItemStack(Items.STICK);
            } else if (d.item != null) r.stack = new ItemStack(BuiltInRegistries.ITEM.get(new ResourceLocation(d.item)));
            rts.add(r);
            k++;
        }
        props.clear();
        for (Anim.PropDef d : a.propDefs) {
            PropRt p = new PropRt();
            p.state = BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK.asLookup(), d.block, false).blockState();
            p.model = mc.getBlockRenderer().getBlockModel(p.state);
            props.add(p);
        }
        mobs.clear();
        for (Anim.MobDef d : a.mobDefs) {
            MobRt mr = new MobRt();
            mr.e = EntityType.byString(d.type).orElseThrow(() -> new IllegalArgumentException("unknown mob " + d.type)).create(mc.level);
            if (mr.e instanceof Mob mob) mob.setNoAi(true);
            mr.pivot = mr.e.getBbHeight() / 2f;
            mr.radius = mr.e.getBbWidth() * 0.7f;
            mobs.add(mr);
        }
        CineCam.LOG.info("[cinecam] actors ready: {}, props: {}, mobs: {}", rts.size(), props.size(), mobs.size());
    }

    public static void render(RenderLevelStageEvent e, Anim a, int row, double filmT) {
        Minecraft mc = Minecraft.getInstance();
        Vec3 cam = e.getCamera().getPosition();
        PoseStack ps = e.getPoseStack();
        MultiBufferSource.BufferSource bs = mc.renderBuffers().bufferSource();
        double[][] pr = a.props[row];
        if (pr.length > 0) {
            for (int i = 0; i < pr.length && i < props.size(); i++) drawProp(mc, ps, bs, cam, props.get(i), pr[i]);
            bs.endBatch();
        }
        double[][] mr = a.mobs[row];
        for (int i = 0; i < mr.length && i < mobs.size(); i++) drawMob(mc, ps, bs, cam, mobs.get(i), mr[i]);
        double[][] poses = a.poses[row];
        for (int i = 0; i < poses.length && i < rts.size(); i++) drawShadow(ps, bs, cam, poses[i]);
        bs.endBatch();
        for (int i = 0; i < poses.length && i < rts.size(); i++) drawActor(mc, ps, bs, cam, rts.get(i), poses[i], filmT);
        double[][] beams = a.beams[row];
        if (beams.length > 0) {
            for (double[] b : beams) drawBeam(ps, bs, cam, b, filmT);
            bs.endBatch();
        }
    }

    private static void drawActor(Minecraft mc, PoseStack ps, MultiBufferSource.BufferSource bs, Vec3 cam, Rt r, double[] p, double filmT) {
        PlayerModel<AbstractClientPlayer> m = r.model;
        float belly = (float) p[22], bellyY = (float) (p[23] == 0 ? 1 : p[23]), hs = (float) (p[24] == 0 ? 1 : p[24]);
        if (belly == 0) belly = 1;
        float sx = (float) (p[4] == 0 ? 1 : p[4]), sy = (float) (p[5] == 0 ? 1 : p[5]), sz = (float) (p[6] == 0 ? 1 : p[6]);

        m.head.xRot = (float) p[7] * D2R; m.head.yRot = (float) p[8] * D2R; m.head.zRot = (float) p[9] * D2R;
        m.rightArm.xRot = (float) p[10] * D2R; m.rightArm.yRot = (float) p[11] * D2R; m.rightArm.zRot = (float) p[12] * D2R;
        m.leftArm.xRot = (float) p[13] * D2R; m.leftArm.yRot = (float) p[14] * D2R; m.leftArm.zRot = (float) p[15] * D2R;
        m.rightLeg.xRot = (float) p[16] * D2R; m.rightLeg.yRot = (float) p[17] * D2R; m.rightLeg.zRot = (float) p[18] * D2R;
        m.leftLeg.xRot = (float) p[19] * D2R; m.leftLeg.yRot = (float) p[20] * D2R; m.leftLeg.zRot = (float) p[21] * D2R;
        m.body.xRot = 0; m.body.yRot = 0; m.body.zRot = 0;
        m.body.xScale = belly; m.body.zScale = belly; m.body.yScale = bellyY;
        float spread = (belly - 1f) * 4.2f;
        m.rightArm.x = r.rax - spread; m.leftArm.x = r.lax + spread;
        m.head.xScale = hs; m.head.yScale = hs; m.head.zScale = hs;
        // Rubber arms: the arm cube starts 2 px ABOVE the shoulder pivot, so a plain y scale would also push that stub back
        // through the torso (arms crossing inside the chest). Slide the pivot along the arm so only the hand end stretches.
        stretchArm(m.rightArm, len(p, 30), r.rax - spread, r.ray, r.raz);
        stretchArm(m.leftArm, len(p, 31), r.lax + spread, r.lay, r.laz);
        m.rightLeg.yScale = len(p, 32); m.leftLeg.yScale = len(p, 33);
        m.hat.copyFrom(m.head);
        m.jacket.copyFrom(m.body);
        m.rightSleeve.copyFrom(m.rightArm);
        m.leftSleeve.copyFrom(m.leftArm);
        m.rightPants.copyFrom(m.rightLeg);
        m.leftPants.copyFrom(m.leftLeg);

        ps.pushPose();
        ps.translate(p[0] - cam.x, p[1] + p[27] - cam.y, p[2] - cam.z);
        ps.mulPose(Axis.YP.rotationDegrees(180f - (float) p[3]));
        if (p[25] != 0) ps.mulPose(Axis.XP.rotationDegrees((float) p[25]));
        if (p[28] != 0) ps.mulPose(Axis.ZP.rotationDegrees((float) p[28]));
        ps.scale(-1f, -1f, 1f);
        ps.scale(sx, sy, sz);
        ps.translate(0.0, -1.501, 0.0);
        BlockPos bp = BlockPos.containing(p[0], p[1] + 1.0, p[2]);
        int light = p[29] > 0.5 ? 0xF000F0 : LevelRenderer.getLightColor(mc.level, bp);
        VertexConsumer vc = bs.getBuffer(RenderType.entityTranslucent(r.tex));
        float sh = p.length > 35 ? (float) (1.0 - 0.96 * Math.max(0, Math.min(1, p[35]))) : 1f;   // silhouette (backlit) darkening
        // v1.0 body: limbs are one bending mesh each (elbow/knee), the upper body turns about the hip; all 0 = the vanilla model
        float bRA = ch(p, 43) * D2R, bLA = ch(p, 44) * D2R, bRL = ch(p, 45) * D2R, bLL = ch(p, 46) * D2R;
        int ov = OverlayTexture.NO_OVERLAY;
        Body.drawBent(ps, vc, m.rightLeg, bRL, light, ov, sh, sh, sh, 1f);
        Body.drawBent(ps, vc, m.leftLeg, bLL, light, ov, sh, sh, sh, 1f);
        Body.drawBent(ps, vc, m.rightPants, bRL, light, ov, sh, sh, sh, 1f);
        Body.drawBent(ps, vc, m.leftPants, bLL, light, ov, sh, sh, sh, 1f);
        ps.pushPose();
        Body.torso(ps, ch(p, 47), ch(p, 48), ch(p, 49));
        m.head.render(ps, vc, light, ov, sh, sh, sh, 1f);
        m.body.render(ps, vc, light, ov, sh, sh, sh, 1f);
        Body.drawBent(ps, vc, m.rightArm, bRA, light, ov, sh, sh, sh, 1f);
        Body.drawBent(ps, vc, m.leftArm, bLA, light, ov, sh, sh, sh, 1f);
        m.hat.render(ps, vc, light, ov, sh, sh, sh, 1f);
        m.jacket.render(ps, vc, light, ov, sh, sh, sh, 1f);
        Body.drawBent(ps, vc, m.rightSleeve, bRA, light, ov, sh, sh, sh, 1f);
        Body.drawBent(ps, vc, m.leftSleeve, bLA, light, ov, sh, sh, sh, 1f);
        bs.endBatch();
        if (r.def.face != null) {
            Body.face(ps, bs.getBuffer(RenderType.entityCutoutNoCull(WHITE)), m.head, r.def.face, ch(p, 50), ch(p, 51), light);
            bs.endBatch();
        }
        if (r.def.hat) {
            ps.pushPose();
            m.head.translateAndRotate(ps);
            ps.scale(1f / 16f, 1f / 16f, 1f / 16f);
            VertexConsumer hv = bs.getBuffer(RenderType.entityCutoutNoCull(r.tex));
            // crown (slightly wider than the head, over the skin's hat band) + brim; textured with the head-top pixels of the skin
            box(ps, hv, -4.35f, -8.7f, -4.35f, 4.35f, -4.9f, 4.35f, light, sh);
            box(ps, hv, -6.6f, -5.35f, -6.6f, 6.6f, -4.55f, 6.6f, light, sh);
            ps.popPose();
            bs.endBatch();
        }
        if (p.length > 41 && p[36] > 0.05) {
            ps.pushPose();
            m.body.translateAndRotate(ps);
            ps.scale(1f / 16f, 1f / 16f, 1f / 16f);
            voxelBelly(ps, bs.getBuffer(RenderType.entityCutoutNoCull(WHITE)), r, p, light, sh, filmT);
            ps.popPose();
            bs.endBatch();
        }
        float isc = (float) p[26];                       // held item scale (0 = hidden; 1 = normal; animate for a "pop")
        if (isc > 0.01f && !r.stack.isEmpty()) {
            ps.pushPose();
            m.translateToHand(HumanoidArm.RIGHT, ps);
            Body.lowerFrame(ps, m.rightArm, bRA);       // the hand rides the forearm below the elbow
            ps.mulPose(Axis.XP.rotationDegrees(-90f));
            ps.mulPose(Axis.YP.rotationDegrees(180f));
            ps.translate(1f / 16f, 0.125f, -0.625f);    // rides the end of the (possibly stretched) arm
            ps.scale(1f, 1f, 1f / len(p, 30));          // ...but the item itself must not stretch with it (arm y == local z here)
            ps.scale(isc, isc, isc);
            if (r.itemModel != null)
                mc.getItemRenderer().render(r.stack, ItemDisplayContext.THIRD_PERSON_RIGHT_HAND, false, ps, bs, light, OverlayTexture.NO_OVERLAY, r.itemModel);
            else
                mc.getItemRenderer().renderStatic(r.stack, ItemDisplayContext.THIRD_PERSON_RIGHT_HAND, light, OverlayTexture.NO_OVERLAY, ps, bs, mc.level, 0);
            ps.popPose();
            bs.endBatch();
        }
        ps.popPose();   // torso
        ps.popPose();
    }

    private static java.lang.reflect.Field[] walkF;   // WalkAnimationState: speedOld, speed, position (declaration order)

    /** limbSwing = pos and limbSwingAmount = amt exactly at this partial tick (position(partial) = position - speed*(1-partial)). */
    private static void setWalk(LivingEntity le, float pos, float amt, float partial) {
        try {
            if (walkF == null) {
                List<java.lang.reflect.Field> fl = new ArrayList<>();
                for (java.lang.reflect.Field f : le.walkAnimation.getClass().getDeclaredFields())
                    if (f.getType() == float.class && !java.lang.reflect.Modifier.isStatic(f.getModifiers())) { f.setAccessible(true); fl.add(f); }
                walkF = fl.toArray(new java.lang.reflect.Field[0]);
            }
            walkF[0].setFloat(le.walkAnimation, amt);
            walkF[1].setFloat(le.walkAnimation, amt);
            walkF[2].setFloat(le.walkAnimation, pos + amt * (1f - partial));
        } catch (Exception ex) {
            CineCam.LOG.warn("[cinecam] walk animation: {}", ex.toString());
        }
    }

    private static float ch(double[] p, int i) {
        return p.length > i ? (float) p[i] : 0f;
    }

    /**
     * The in-game "full of water" belly: a voxel ball (1 model px cubes) bulging out of the torso front, each cube painted with the
     * skin's torso-front pixel behind it. Its implicit surface sloshes: a squash/stretch jiggle plus ripple bands running down it.
     */
    private static boolean inBelly(double x, double y, double z, double cy, double cz, double rad, double amp, double sy, double t) {
        double dx = x, dy = y - cy, dz = z - cz;
        double sxz = 1.0 / Math.sqrt(sy);
        double q = Math.sqrt((dx * dx + dz * dz) / (sxz * sxz) + dy * dy / (sy * sy));
        double wave = amp * Math.sin(5.2 * dy / rad - 11.0 * t + 1.7 * dx / rad) * Math.min(1.0, Math.max(0.0, -dz / rad + 0.4));
        return q < rad + wave;
    }

    private static void voxelBelly(PoseStack ps, VertexConsumer vc, Rt r, double[] p, int light, float sh, double t) {
        double rad = p[36], cy = p[37], out = p[38], amp = p[39], sy = 1.0 + p[40], s = p[41] > 0.01 ? p[41] : 1.0;
        double cz = -2.0 - out + rad;
        int n = (int) Math.ceil((rad * Math.max(sy, 1.0 / Math.sqrt(sy)) + Math.abs(amp) + 1.0) / s);
        int w = 2 * n + 1;
        boolean[] in = new boolean[w * w * w];
        for (int i = 0; i < w; i++) for (int j = 0; j < w; j++) for (int k = 0; k < w; k++)
            in[(i * w + j) * w + k] = inBelly((i - n) * s, cy + (j - n) * s, cz + (k - n) * s, cy, cz, rad, amp, sy, t);
        PoseStack.Pose pose = ps.last();
        Matrix4f mat = pose.pose();
        Matrix3f nrm = pose.normal();
        int[][] dirs = {{1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1}};
        float h = (float) (s / 2);
        for (int i = 0; i < w; i++) for (int j = 0; j < w; j++) for (int k = 0; k < w; k++) {
            if (!in[(i * w + j) * w + k]) continue;
            float x = (float) ((i - n) * s), y = (float) (cy + (j - n) * s), z = (float) (cz + (k - n) * s);
            if (z > 2.2f && Math.abs(x) < 4f && y > 0f && y < 12f) continue;          // fully inside/behind the torso: never seen
            int col = Math.max(0, Math.min(7, (int) Math.floor(x + 4f)));
            int row = Math.max(0, Math.min(11, (int) Math.floor(y)));
            float[] c0 = r.front[col][row];
            float[] c = c0;
            double shine = p.length > 42 ? p[42] : 0.0;
            if (shine > 0.001) {                         // moving caustic glints: the ball reads as liquid, not a rock
                double g1 = Math.sin(0.48 * x + 0.36 * y - 4.6 * t) * Math.sin(0.30 * x - 0.58 * y + 3.3 * t + 0.25 * z);
                double gl = Math.pow(Math.max(0.0, g1), 4.0) * shine;
                float a = (float) Math.min(0.55, 0.6 * gl);      // pale water-blue glint bands sliding over the ball
                c = new float[]{c0[0] + (0.72f - c0[0]) * a, c0[1] + (0.90f - c0[1]) * a, c0[2] + (1f - c0[2]) * a};
            }
            for (int[] d : dirs) {
                int a = i + d[0], b = j + d[1], e = k + d[2];
                if (a >= 0 && a < w && b >= 0 && b < w && e >= 0 && e < w && in[(a * w + b) * w + e]) continue;
                cubeFace(vc, mat, nrm, x, y, z, h, d, c[0] * sh, c[1] * sh, c[2] * sh, light);
            }
        }
    }

    private static void cubeFace(VertexConsumer vc, Matrix4f m, Matrix3f n, float x, float y, float z, float h, int[] d,
                                 float r, float g, float b, int light) {
        float[][] q;
        if (d[0] != 0) { float fx = x + d[0] * h; q = new float[][]{{fx, y - h, z - h}, {fx, y + h, z - h}, {fx, y + h, z + h}, {fx, y - h, z + h}}; }
        else if (d[1] != 0) { float fy = y + d[1] * h; q = new float[][]{{x - h, fy, z - h}, {x + h, fy, z - h}, {x + h, fy, z + h}, {x - h, fy, z + h}}; }
        else { float fz = z + d[2] * h; q = new float[][]{{x - h, y - h, fz}, {x + h, y - h, fz}, {x + h, y + h, fz}, {x - h, y + h, fz}}; }
        float[][] uv = {{0, 0}, {1, 0}, {1, 1}, {0, 1}};
        // block-style face shading in model space (y down, front = -z): steps read as bright rims on a darker front, like in-game
        float f = d[1] < 0 ? 1.0f : d[1] > 0 ? 0.45f : d[2] < 0 ? 0.64f : d[2] > 0 ? 0.6f : 0.78f;
        r *= f; g *= f; b *= f;
        for (int k = 0; k < 4; k++)
            vc.vertex(m, q[k][0], q[k][1], q[k][2]).color(r, g, b, 1f).uv(uv[k][0], uv[k][1])
              .overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, d[0], d[1], d[2]).endVertex();
    }

    private static void stretchArm(net.minecraft.client.model.geom.ModelPart arm, float len, float x0, float y0, float z0) {
        arm.yScale = len;
        Vector3f off = new Vector3f(0f, 2f * (len - 1f), 0f).rotate(new Quaternionf().rotationZYX(arm.zRot, arm.yRot, arm.xRot));
        arm.x = x0 + off.x; arm.y = y0 + off.y; arm.z = z0 + off.z;
    }

    private static float len(double[] p, int i) {
        return p.length > i && p[i] != 0 ? (float) p[i] : 1f;
    }

    /** Axis-aligned box in model pixels (y down), UVs from the skin's head-top square (8..16, 0..8 of 64). */
    private static void box(PoseStack ps, VertexConsumer vc, float x0, float y0, float z0, float x1, float y1, float z1, int light, float sh) {
        PoseStack.Pose pose = ps.last();
        Matrix4f m = pose.pose();
        Matrix3f n = pose.normal();
        float u0 = 8.5f / 64f, u1 = 15.5f / 64f, v0 = 0.5f / 64f, v1 = 7.5f / 64f;
        float[][] f = {
            {x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1, 0, -1, 0},
            {x0, y1, z1, x1, y1, z1, x1, y1, z0, x0, y1, z0, 0, 1, 0},
            {x0, y0, z0, x0, y1, z0, x1, y1, z0, x1, y0, z0, 0, 0, -1},
            {x1, y0, z1, x1, y1, z1, x0, y1, z1, x0, y0, z1, 0, 0, 1},
            {x0, y0, z1, x0, y1, z1, x0, y1, z0, x0, y0, z0, -1, 0, 0},
            {x1, y0, z0, x1, y1, z0, x1, y1, z1, x1, y0, z1, 1, 0, 0}};
        float[][] uv = {{u0, v0}, {u1, v0}, {u1, v1}, {u0, v1}};
        for (float[] q : f)
            for (int k = 0; k < 4; k++)
                vc.vertex(m, q[k * 3], q[k * 3 + 1], q[k * 3 + 2]).color(sh, sh, sh, 1f).uv(uv[k][0], uv[k][1])
                  .overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, q[12], q[13], q[14]).endVertex();
    }

    /** Soft round contact shadow on the ground (p[34] = ground y); fades and shrinks with height. */
    private static void drawShadow(PoseStack ps, MultiBufferSource.BufferSource bs, Vec3 cam, double[] p) {
        if (p.length <= 34 || p[34] == 0) return;
        double h = p[1] + p[27] - p[34];
        double alpha = Math.max(0, Math.min(0.55, 0.55 * (1 - h / 7.0)));
        if (alpha <= 0.01) return;
        double sc = Math.max(p[4] == 0 ? 1 : p[4], p[6] == 0 ? 1 : p[6]);
        double r = 0.62 * sc * (1 - Math.min(0.5, h / 14.0));
        double y = p[34] + 0.015 - cam.y, x = p[0] - cam.x, z = p[2] - cam.z;
        PoseStack.Pose pose = ps.last();
        VertexConsumer vc = bs.getBuffer(RenderType.entityShadow(SHADOW));
        float a = (float) alpha;
        v(vc, pose.pose(), pose.normal(), new double[]{x - r, y, z - r}, 0, 0, 1, 1, 1, a, 0xF000F0, 0, 1, 0);
        v(vc, pose.pose(), pose.normal(), new double[]{x - r, y, z + r}, 0, 1, 1, 1, 1, a, 0xF000F0, 0, 1, 0);
        v(vc, pose.pose(), pose.normal(), new double[]{x + r, y, z + r}, 1, 1, 1, 1, 1, a, 0xF000F0, 0, 1, 0);
        v(vc, pose.pose(), pose.normal(), new double[]{x + r, y, z - r}, 1, 0, 1, 1, 1, a, 0xF000F0, 0, 1, 0);
    }

    private static java.lang.reflect.Field paddleF;   // Boat.paddlePositions (o único float[] da classe)

    /** v1.1: remo do barco no ângulo do estúdio — getRowingTime(lado, 1) devolve paddlePositions[lado] com o remo "ligado". */
    private static void setPaddles(net.minecraft.world.entity.vehicle.Boat b, double a, float part) {
        boolean on = a != 0.0;
        b.setPaddleState(on, on);
        try {
            if (paddleF == null) {
                for (java.lang.reflect.Field f : net.minecraft.world.entity.vehicle.Boat.class.getDeclaredFields())
                    if (f.getType() == float[].class) { f.setAccessible(true); paddleF = f; break; }
            }
            float[] pp = (float[]) paddleF.get(b);
            double k = (1.0 - part) * Math.PI / 8.0;     // o jogo interpola entre pos − π/8 e pos pela fração do tick
            pp[0] = (float) (a + k);
            pp[1] = (float) (a - Math.PI + k);
        } catch (Exception ex) {
            CineCam.LOG.warn("[cinecam] boat paddles: {}", ex.toString());
        }
    }

    /** A vanilla mob (client-only instance, never added to the world) posed by the rig: world-axis squash about its centre,
     *  then yaw/pitch/roll tumble; limbs at walk position q[10] / amount q[12]; head q[13]/q[14]. */
    private static void drawMob(Minecraft mc, PoseStack ps, MultiBufferSource.BufferSource bs, Vec3 cam, MobRt mr, double[] q) {
        if (q[6] == 0) return;
        Entity e = mr.e;
        e.setPos(q[0], q[1] - mr.pivot, q[2]);
        e.setYRot(0f); e.yRotO = 0f; e.setXRot(0f); e.xRotO = 0f;
        float part = 1f;
        if (q.length > 11 && q[11] > 0) {                // age in ticks -> model anims that read tickCount (fish tail, wings...)
            e.tickCount = (int) Math.floor(q[11]);
            part = (float) (q[11] - Math.floor(q[11]));
        }
        if (e instanceof LivingEntity le) {
            le.yBodyRot = le.yBodyRotO = 0f;
            float hy = q.length > 13 ? (float) q[13] : 0f, hp = q.length > 14 ? (float) q[14] : 0f;
            le.yHeadRot = le.yHeadRotO = hy;
            e.setYRot(0f); e.yRotO = 0f; e.setXRot(hp); e.xRotO = hp;
            // v1.0.2 (25/10): the walk cycle is a POSITION computed in Python from the distance walked (vanilla formula), set
            // exactly for this pass.  It used to be walkAnimation.update(step) on EVERY pass — subframes and chunk-wait retries
            // added steps, so legs ran 6-10x too fast and jittered ("mobs com membros super velozes e bugados").
            setWalk(le, (float) q[10], q.length > 12 ? (float) q[12] : 0f, part);
        }
        if (e instanceof net.minecraft.world.entity.vehicle.Boat b) setPaddles(b, q.length > 15 ? q[15] : 0.0, part);
        if (q[9] != 0) {
            double h = q[1] - mr.pivot - q[9];
            double alpha = Math.max(0, Math.min(0.5, 0.5 * (1 - h / 6.0)));
            if (alpha > 0.01) {
                double r = mr.radius * Math.max(q[6], q[8]) * (1 - Math.min(0.5, h / 12.0));
                double y = q[9] + 0.016 - cam.y, x = q[0] - cam.x, z = q[2] - cam.z;
                PoseStack.Pose pose = ps.last();
                VertexConsumer vc = bs.getBuffer(RenderType.entityShadow(SHADOW));
                float a = (float) alpha;
                v(vc, pose.pose(), pose.normal(), new double[]{x - r, y, z - r}, 0, 0, 1, 1, 1, a, 0xF000F0, 0, 1, 0);
                v(vc, pose.pose(), pose.normal(), new double[]{x - r, y, z + r}, 0, 1, 1, 1, 1, a, 0xF000F0, 0, 1, 0);
                v(vc, pose.pose(), pose.normal(), new double[]{x + r, y, z + r}, 1, 1, 1, 1, 1, a, 0xF000F0, 0, 1, 0);
                v(vc, pose.pose(), pose.normal(), new double[]{x + r, y, z - r}, 1, 0, 1, 1, 1, a, 0xF000F0, 0, 1, 0);
                bs.endBatch();
            }
        }
        ps.pushPose();
        ps.translate(q[0] - cam.x, q[1] - cam.y, q[2] - cam.z);
        ps.scale((float) q[6], (float) q[7], (float) q[8]);
        ps.mulPose(Axis.YP.rotationDegrees((float) -q[3]));
        if (q[4] != 0) ps.mulPose(Axis.XP.rotationDegrees((float) q[4]));
        if (q[5] != 0) ps.mulPose(Axis.ZP.rotationDegrees((float) q[5]));
        ps.translate(0.0, -mr.pivot, 0.0);
        EntityRenderDispatcher d = mc.getEntityRenderDispatcher();
        d.setRenderShadow(false);
        int light = LevelRenderer.getLightColor(mc.level, BlockPos.containing(q[0], q[1] + 0.3, q[2]));
        d.render(e, 0.0, 0.0, 0.0, 0f, part, ps, bs, light);
        bs.endBatch();
        d.setRenderShadow(true);
        ps.popPose();
    }

    /** A block model as a rubbery prop: bottom-centre pivot, rotate Y/X/Z, non-uniform scale (squash & stretch). */
    private static void drawProp(Minecraft mc, PoseStack ps, MultiBufferSource.BufferSource bs, Vec3 cam, PropRt pr, double[] q) {
        if (q[3] == 0) return;
        BlockPos bp = BlockPos.containing(q[0], q[1] + 0.5, q[2]);
        int l0 = LevelRenderer.getLightColor(mc.level, bp), l1 = LevelRenderer.getLightColor(mc.level, bp.above());
        int light = (Math.max(l0 >> 20 & 15, l1 >> 20 & 15) << 20) | (Math.max(l0 >> 4 & 15, l1 >> 4 & 15) << 4);
        int col = mc.getBlockColors().getColor(pr.state, mc.level, bp, 0);
        float r = 1f, g = 1f, b = 1f;
        if (col != -1) { r = (col >> 16 & 255) / 255f; g = (col >> 8 & 255) / 255f; b = (col & 255) / 255f; }
        ps.pushPose();
        ps.translate(q[0] - cam.x, q[1] - cam.y, q[2] - cam.z);
        if (q[6] != 0) ps.mulPose(Axis.YP.rotationDegrees((float) q[6]));
        if (q[7] != 0) ps.mulPose(Axis.XP.rotationDegrees((float) q[7]));
        if (q[8] != 0) ps.mulPose(Axis.ZP.rotationDegrees((float) q[8]));
        ps.scale((float) q[3], (float) q[4], (float) q[5]);
        ps.translate(-0.5, 0.0, -0.5);
        ModelBlockRenderer mbr = mc.getBlockRenderer().getModelRenderer();
        for (RenderType rt : pr.model.getRenderTypes(pr.state, RandomSource.create(42L), ModelData.EMPTY))
            mbr.renderModel(ps.last(), bs.getBuffer(RenderTypeHelper.getEntityRenderType(rt, false)), pr.state, pr.model,
                            r, g, b, light, OverlayTexture.NO_OVERLAY, ModelData.EMPTY, rt);
        ps.popPose();
    }

    /** Square-section tube along a quadratic arc: p1 -> (mid + up*lift) -> p2, radius r1 -> r2, shimmering blue. */
    private static void drawBeam(PoseStack ps, MultiBufferSource.BufferSource bs, Vec3 cam, double[] b, double t) {
        if (b[8] <= 0.001) return;
        double len = Math.sqrt((b[3]-b[0])*(b[3]-b[0]) + (b[4]-b[1])*(b[4]-b[1]) + (b[5]-b[2])*(b[5]-b[2]));
        final int N = b[15] > 0 ? (int) b[15] : (int) Math.max(18, Math.min(90, len * 0.8));
        double[][] c = new double[N + 1][3];
        double[][] tan = new double[N + 1][3];
        double cx = (b[0] + b[3]) / 2, cy = (b[1] + b[4]) / 2 + b[9], cz = (b[2] + b[5]) / 2 + b[10];
        for (int i = 0; i <= N; i++) {
            double u = i / (double) N, v = 1 - u;
            c[i][0] = v * v * b[0] + 2 * u * v * cx + u * u * b[3] - cam.x;
            c[i][1] = v * v * b[1] + 2 * u * v * cy + u * u * b[4] - cam.y;
            c[i][2] = v * v * b[2] + 2 * u * v * cz + u * u * b[5] - cam.z;
            tan[i][0] = 2 * v * (cx - b[0]) + 2 * u * (b[3] - cx);
            tan[i][1] = 2 * v * (cy - b[1]) + 2 * u * (b[4] - cy);
            tan[i][2] = 2 * v * (cz - b[2]) + 2 * u * (b[5] - cz);
        }
        PoseStack.Pose pose = ps.last();
        Matrix4f mat = pose.pose();
        Matrix3f nrm = pose.normal();
        VertexConsumer vc = bs.getBuffer(RenderType.entityTranslucent(WHITE));
        double[][][] ring = new double[N + 1][4][3];
        for (int i = 0; i <= N; i++) {
            double[] T = norm(tan[i]);
            double[] ref = Math.abs(T[1]) > 0.95 ? new double[]{1, 0, 0} : new double[]{0, 1, 0};
            double[] U = norm(cross(T, ref));
            double[] V = norm(cross(T, U));
            double rad = b[6] + (b[7] - b[6]) * (i / (double) N);
            double[][] s = {{1, 1}, {-1, 1}, {-1, -1}, {1, -1}};
            for (int k = 0; k < 4; k++)
                for (int d = 0; d < 3; d++) ring[i][k][d] = c[i][d] + rad * (s[k][0] * U[d] + s[k][1] * V[d]);
        }
        int light = 0xF000F0;
        int style = (int) b[14];
        for (int i = 0; i < N; i++) {
            float rr, gg, bb, al;
            if (style == 1) {                       // straw: red / white bands
                boolean red = ((i / 3) & 1) == 0;
                rr = red ? 0.92f : 0.98f; gg = red ? 0.12f : 0.98f; bb = red ? 0.14f : 0.98f;
                al = (float) Math.min(1.0, b[8]);
            } else if (style == 2) {
                rr = (float) b[11]; gg = (float) b[12]; bb = (float) b[13]; al = (float) Math.min(1.0, b[8]);
            } else {
                double wave = 0.5 + 0.5 * Math.sin(i * 1.15 - t * 16.0);
                rr = (float) (0.30 + 0.35 * wave); gg = (float) (0.58 + 0.30 * wave); bb = 1f;
                al = (float) Math.min(1.0, b[8]) * (float) (0.72 + 0.2 * wave);
            }
            for (int k = 0; k < 4; k++) {
                int k2 = (k + 1) & 3;
                quad(vc, mat, nrm, ring[i][k], ring[i][k2], ring[i + 1][k2], ring[i + 1][k], rr, gg, bb, al, light);
            }
        }
    }

    private static void quad(VertexConsumer vc, Matrix4f mat, Matrix3f nrm, double[] a, double[] b, double[] c, double[] d,
                             float r, float g, float bl, float al, int light) {
        double[] n = norm(cross(new double[]{b[0] - a[0], b[1] - a[1], b[2] - a[2]}, new double[]{d[0] - a[0], d[1] - a[1], d[2] - a[2]}));
        float nx = (float) n[0], ny = (float) n[1], nz = (float) n[2];
        v(vc, mat, nrm, a, 0, 0, r, g, bl, al, light, nx, ny, nz);
        v(vc, mat, nrm, b, 1, 0, r, g, bl, al, light, nx, ny, nz);
        v(vc, mat, nrm, c, 1, 1, r, g, bl, al, light, nx, ny, nz);
        v(vc, mat, nrm, d, 0, 1, r, g, bl, al, light, nx, ny, nz);
    }

    private static void v(VertexConsumer vc, Matrix4f mat, Matrix3f nrm, double[] p, float u, float w, float r, float g, float b, float a,
                          int light, float nx, float ny, float nz) {
        vc.vertex(mat, (float) p[0], (float) p[1], (float) p[2]).color(r, g, b, a).uv(u, w)
          .overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(nrm, nx, ny, nz).endVertex();
    }

    private static double[] cross(double[] a, double[] b) {
        return new double[]{a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
    }

    private static double[] norm(double[] a) {
        double l = Math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
        if (l < 1e-9) return new double[]{0, 1, 0};
        return new double[]{a[0] / l, a[1] / l, a[2] / l};
    }
}
