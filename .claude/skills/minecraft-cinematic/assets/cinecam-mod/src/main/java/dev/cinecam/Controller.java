package dev.cinecam;

import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.platform.Window;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.resources.ResourceLocation;
import org.joml.Matrix4f;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;
import com.mojang.blaze3d.pipeline.RenderTarget;
import com.mojang.blaze3d.systems.RenderSystem;
import net.minecraft.FileUtil;
import net.minecraft.client.CloudStatus;
import net.minecraft.client.GraphicsStatus;
import net.minecraft.client.Minecraft;
import net.minecraft.client.ParticleStatus;
import net.minecraft.client.Camera;
import net.minecraft.client.Timer;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.tutorial.TutorialSteps;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import java.nio.FloatBuffer;
import java.nio.ByteOrder;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.lwjgl.BufferUtils;
import org.lwjgl.opengl.GL11;

import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;
import java.util.stream.Stream;

/**
 * Drives the real client through: title -> fresh/copied world -> scene setup -> chunk preload -> film.
 * During FILM every loop iteration is one render pass with a camera pose taken from camera.csv, the game clock is
 * a {@link FixedTimer} (deterministic), and each finished pass is read back from the framebuffer and piped to ffmpeg.
 */
@Mod.EventBusSubscriber(modid = CineCam.MOD_ID, value = Dist.CLIENT)
public final class Controller {
    private static final String JOB_PROP = System.getProperty("cinecam.job");
    private static final boolean ON = JOB_PROP != null && !JOB_PROP.isBlank();

    private enum Phase { TITLE, WORLD, SETUP, PRELOAD, COMMANDS, SETTLE, FILM, FINISH, IDLE, DONE }

    private static Phase phase = Phase.TITLE;
    private static int tick;
    private static long startedNs;
    private static long phaseStartNs;
    private static Job job;
    private static CamTable table;
    private static String worldDir;
    private static CompletableFuture<Void> pending;
    private static String fatal;
    private static final List<String> WARN = new ArrayList<>();

    // film state
    private static FixedTimer fixed;
    private static FfmpegSink sink;
    private static boolean stills;
    private static boolean scoutOnly;
    private static int idx;                // next table row to capture
    private static int readyStreak, waitPasses, totalPasses, totalRetries, maxWait;
    private static boolean posing;
    private static ByteBuffer buf;
    private static byte[] scratch, out;
    private static int[] acc;
    private static int capW, capH, resizeFixes;
    private static long filmStartNs;
    private static int[] lut;
    private static byte[] invLut;
    private static int stableTicks;
    private static long waitStartNs;
    private static FfmpegSink depthSink;
    private static FloatBuffer depthBuf;
    private static ByteBuffer depthOut;
    private static Anim anim;
    // batch (v0.8): shots queued after the current one; the vanilla timer is put back between shots so client ticks run again
    private static final java.util.ArrayDeque<Path> QUEUE = new java.util.ArrayDeque<>();
    private static Timer vanillaTimer;
    private static int shotNo;

    private Controller() {}

    private static void loadShot(Path p) throws IOException {
        job = Job.load(p);
        table = CamTable.load(job.cameraCsv);
        String mode = job.mode != null ? job.mode : System.getProperty("cinecam.mode", "film");
        stills = "stills".equals(mode);
        scoutOnly = "scout".equals(mode);
        QUEUE.addAll(job.next);
        CineCam.LOG.info("[cinecam] job '{}' ({}) {}x{} @{}fps rows={} subframes={} queued={}", job.name, mode, job.width, job.height, job.fps, table.n, job.subframes, QUEUE.size());
        if (table.n == 0) throw new IllegalStateException("camera.csv is empty");
    }

    // ------------------------------------------------------------------ events

    @SubscribeEvent
    public static void clientTick(TickEvent.ClientTickEvent e) {
        if (!ON || e.phase != TickEvent.Phase.END || phase == Phase.DONE) return;
        Minecraft mc = Minecraft.getInstance();
        try {
            if (startedNs == 0) {
                startedNs = System.nanoTime();
                phaseStartNs = startedNs;
                loadShot(Path.of(JOB_PROP));
                initLut();
            }
            mc.options.pauseOnLostFocus = false;
            tick++;
            if (phase != Phase.FILM && phase != Phase.FINISH && phase != Phase.IDLE && (System.nanoTime() - phaseStartNs) / 1e9 > Math.max(job.preloadTimeoutSec, 60) + 120 && phase != Phase.TITLE) {
                throw new IllegalStateException("timeout in phase " + phase);
            }
            runPhase(mc);
        } catch (Throwable ex) {
            CineCam.LOG.error("[cinecam] failure in phase " + phase, ex);
            fatal = phase + ": " + ex;
            go(Phase.FINISH);
        }
    }

    @SubscribeEvent
    public static void renderStart(TickEvent.RenderTickEvent e) {
        if (!ON || (phase != Phase.FILM && !(phase == Phase.FINISH && e.phase == TickEvent.Phase.END && fixed != null))) return;
        if (phase == Phase.FINISH) { finish(Minecraft.getInstance()); return; }
        try {
            if (e.phase == TickEvent.Phase.START) {
                if (idx < table.n) {
                    posing = true;
                    if (anim != null && idx < anim.water.length) WaterDrain.apply(Minecraft.getInstance(), anim.water[idx], anim.funnel[idx]);
                }
            } else {
                posing = false;
                filmRenderEnd(Minecraft.getInstance());
            }
        } catch (Throwable ex) {
            CineCam.LOG.error("[cinecam] failure during film", ex);
            fatal = "FILM: " + ex;
            posing = false;
            go(Phase.FINISH);
        }
        // With a frozen world the FixedTimer yields no client ticks, so ClientTickEvent never fires again:
        // the shutdown has to be driven from the render loop.
        if (e.phase == TickEvent.Phase.END && phase == Phase.FINISH) finish(Minecraft.getInstance());
    }

    /** v1.1: névoa da cena (estúdio do Shorts: FX.nevoa / paisagem / shot.fog) — distância e cor fixas na cena. */
    @SubscribeEvent
    public static void fog(ViewportEvent.RenderFog e) {
        if (!ON || job == null || job.fog == null || job.fog.length < 2 || !(phase == Phase.FILM || phase == Phase.SETTLE)) return;
        e.setNearPlaneDistance((float) job.fog[0]);
        e.setFarPlaneDistance((float) job.fog[1]);
        e.setCanceled(true);
    }

    @SubscribeEvent
    public static void fogColor(ViewportEvent.ComputeFogColor e) {
        if (!ON || job == null || job.fog == null || job.fog.length < 5 || !(phase == Phase.FILM || phase == Phase.SETTLE)) return;
        e.setRed((float) job.fog[2]); e.setGreen((float) job.fog[3]); e.setBlue((float) job.fog[4]);
    }

    @SubscribeEvent
    public static void cameraAngles(ViewportEvent.ComputeCameraAngles e) {
        if (!posing || idx >= table.n) return;
        e.setYaw((float) table.yaw[idx]);
        e.setPitch((float) table.pitch[idx]);
        e.setRoll((float) table.roll[idx]);
        Reflect.setCameraPosition(e.getCamera(), new Vec3(table.x[idx], table.y[idx], table.z[idx]));
    }

    /** Depth must be read right after the world is drawn: the GUI pass clears the depth buffer. */
    @SubscribeEvent
    public static void levelStage(RenderLevelStageEvent e) {
        if (!ON || !posing || depthBuf == null || e.getStage() != RenderLevelStageEvent.Stage.AFTER_LEVEL) return;
        if (idx % job.subframes != job.subframes / 2) return;      // only the middle subframe is written (v0.8: was read on every pass)
        Minecraft mc = Minecraft.getInstance();
        RenderTarget rt = mc.getMainRenderTarget();
        int prev = GL11.glGetInteger(GL11.GL_TEXTURE_BINDING_2D);
        GlStateManager._bindTexture(rt.getDepthTextureId());
        depthBuf.clear();
        GL11.glGetTexImage(GL11.GL_TEXTURE_2D, 0, GL11.GL_DEPTH_COMPONENT, GL11.GL_FLOAT, depthBuf);
        GlStateManager._bindTexture(prev);
        depthBuf.rewind();
    }

    private static final ResourceLocation SUN_TEX = new ResourceLocation("minecraft", "textures/environment/sun.png");
    private static ResourceLocation sunTexId;

    /** Big sun: the vanilla sun texture redrawn sunScale x larger at the vanilla sun transform, right after the sky
     *  (terrain, entities and clouds still draw over it). Same centre as the real sun, which hides inside it. */
    @SubscribeEvent
    public static void bigSun(RenderLevelStageEvent e) {
        if (!ON || job == null || job.sunScale <= 1.01 || e.getStage() != RenderLevelStageEvent.Stage.AFTER_SKY) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) return;
        PoseStack ps = e.getPoseStack();
        float tod = mc.level.getTimeOfDay(e.getPartialTick());
        float vis = 1.0F - mc.level.getRainLevel(e.getPartialTick());
        ps.pushPose();
        ps.mulPose(Axis.YP.rotationDegrees(-90.0F));
        ps.mulPose(Axis.XP.rotationDegrees(tod * 360.0F));
        Matrix4f m = ps.last().pose();
        float s = (float) (30.0 * job.sunScale);
        RenderSystem.enableBlend();
        if (job.sunTexture != null) {                       // custom RGBA sun: one straight-alpha pass, exact colours
            if (sunTexId == null) {
                try (java.io.InputStream in = java.nio.file.Files.newInputStream(java.nio.file.Path.of(job.sunTexture))) {
                    sunTexId = new ResourceLocation("cinecam", "sun_custom");
                    mc.getTextureManager().register(sunTexId, new net.minecraft.client.renderer.texture.DynamicTexture(
                            com.mojang.blaze3d.platform.NativeImage.read(in)));
                } catch (IOException ex) {
                    WARN.add("sunTexture: " + ex); job.sunTexture = null; ps.popPose(); return;
                }
            }
            RenderSystem.defaultBlendFunc();
            RenderSystem.depthMask(false);
            RenderSystem.setShader(GameRenderer::getPositionTexShader);
            RenderSystem.setShaderTexture(0, sunTexId);
            RenderSystem.setShaderColor(1f, 1f, 1f, vis);
            BufferBuilder bb = Tesselator.getInstance().getBuilder();
            bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX);
            bb.vertex(m, -s, 100f, -s).uv(0f, 0f).endVertex();
            bb.vertex(m, s, 100f, -s).uv(1f, 0f).endVertex();
            bb.vertex(m, s, 100f, s).uv(1f, 1f).endVertex();
            bb.vertex(m, -s, 100f, s).uv(0f, 1f).endVertex();
            BufferUploader.drawWithShader(bb.end());
            RenderSystem.setShaderColor(1f, 1f, 1f, 1f);
            RenderSystem.depthMask(true);
            RenderSystem.disableBlend();
            ps.popPose();
            return;
        }
        // "over" composite with the texture as coverage, in two passes: dst*(1-tex) then + tex*tint
        // (plain additive clips to white over a bright sky; screen blend keeps the sky's blue -> pink sun)
        RenderSystem.depthMask(false);
        RenderSystem.setShader(GameRenderer::getPositionTexShader);
        RenderSystem.setShaderTexture(0, SUN_TEX);
        for (int pass = 0; pass < 2; pass++) {
            if (pass == 0) {
                RenderSystem.blendFuncSeparate(GlStateManager.SourceFactor.ZERO, GlStateManager.DestFactor.ONE_MINUS_SRC_COLOR,
                        GlStateManager.SourceFactor.ZERO, GlStateManager.DestFactor.ONE);
                RenderSystem.setShaderColor(vis, vis, vis, 1f);
            } else {
                RenderSystem.blendFuncSeparate(GlStateManager.SourceFactor.ONE, GlStateManager.DestFactor.ONE,
                        GlStateManager.SourceFactor.ZERO, GlStateManager.DestFactor.ONE);
                RenderSystem.setShaderColor((float) job.sunTint[0] * vis, (float) job.sunTint[1] * vis, (float) job.sunTint[2] * vis, 1f);
            }
            BufferBuilder bb = Tesselator.getInstance().getBuilder();
            bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX);
            bb.vertex(m, -s, 100f, -s).uv(0f, 0f).endVertex();
            bb.vertex(m, s, 100f, -s).uv(1f, 0f).endVertex();
            bb.vertex(m, s, 100f, s).uv(1f, 1f).endVertex();
            bb.vertex(m, -s, 100f, s).uv(0f, 1f).endVertex();
            BufferUploader.drawWithShader(bb.end());
        }
        RenderSystem.setShaderColor(1f, 1f, 1f, 1f);
        RenderSystem.depthMask(true);
        RenderSystem.defaultBlendFunc();
        RenderSystem.disableBlend();
        ps.popPose();
    }

    /** Posed actors and water beams are drawn right after the vanilla entities of every film pass. */
    @SubscribeEvent
    public static void actorsStage(RenderLevelStageEvent e) {
        if (!ON || !posing || anim == null || idx >= table.n || idx >= anim.poses.length) return;
        if (e.getStage() != RenderLevelStageEvent.Stage.AFTER_ENTITIES) return;
        try {
            Actors.render(e, anim, idx, table.t[idx]);
        } catch (Throwable ex) {
            if (!WARN.contains("actors: " + ex)) { WARN.add("actors: " + ex); CineCam.LOG.error("[cinecam] actor render failed", ex); }
        }
    }

    @SubscribeEvent
    public static void cameraFov(ViewportEvent.ComputeFov e) {
        if (!posing || idx >= table.n) return;
        e.setFOV(table.fov[idx]);
    }

    // ------------------------------------------------------------------ phases

    private static void runPhase(Minecraft mc) throws Exception {
        switch (phase) {
            case TITLE -> {
                if (tick > 60 && mc.level == null && !(mc.screen instanceof TitleScreen) && mc.getOverlay() == null) mc.setScreen(new TitleScreen());
                if (tick > 40 && mc.screen instanceof TitleScreen) {
                    applyOptions(mc);
                    startWorld(mc);
                    go(Phase.WORLD);
                }
            }
            case WORLD -> {
                if (mc.player != null && mc.level != null && mc.getSingleplayerServer() != null && tick > 60) go(Phase.SETUP);
            }
            case SETUP -> {
                if (tick == 1) {
                    double[] a = job.anchor != null ? job.anchor : new double[]{table.x[0], table.y[0], table.z[0]};
                    checkReach(a);
                    server(mc, p -> {
                        var level = p.server.getLevel(net.minecraft.resources.ResourceKey.create(Registries.DIMENSION, new net.minecraft.resources.ResourceLocation(job.dimension)));
                        if (level == null) throw new IllegalStateException("unknown dimension " + job.dimension);
                        run(p, "gamerule doDaylightCycle false");
                        run(p, "gamerule doWeatherCycle false");
                        run(p, "gamerule doMobSpawning false");
                        run(p, "gamerule randomTickSpeed 0");
                        run(p, "gamerule doFireTick false");
                        run(p, "time set " + job.dayTime);
                        run(p, "weather " + job.weather);
                        p.setGameMode(GameType.SPECTATOR);
                        p.teleportTo(level, a[0], a[1], a[2], 0f, 0f);
                        p.getAbilities().flying = true;
                        p.onUpdateAbilities();
                    });
                }
                if (tick > 5 && ready()) go(Phase.PRELOAD);
            }
            case PRELOAD -> {
                int r = job.renderDistance;
                long want = (long) ((2 * r + 1) * (2 * r + 1) * 0.80);
                long have = mc.level.getChunkSource().getLoadedChunksCount();
                boolean idle = mc.levelRenderer.hasRenderedAllChunks();
                stableTicks = (have >= want && idle) ? stableTicks + 1 : 0;
                if (tick % 100 == 0) CineCam.LOG.info("[cinecam] preload chunks {}/{} idle={} stable={}", have, want, idle, stableTicks);
                if (stableTicks >= 40) go(Phase.COMMANDS);
            }
            case COMMANDS -> {
                if (tick == 1) {
                    // v1.1 live session: the same set as the previous shot (same command list) is already built — skip it
                    int ch = job.commands.hashCode() * 31 + job.dimension.hashCode();
                    boolean same = shotNo > 0 && ch == lastCmdsHash && !job.commands.isEmpty();
                    lastCmdsHash = ch;
                    if (same) CineCam.LOG.info("[cinecam] set unchanged: {} commands skipped", job.commands.size());
                    server(mc, p -> {
                        if (!same) for (String c : job.commands) run(p, c);
                        try {
                            Files.createDirectories(job.outDir);
                            if (!job.queries.isEmpty()) Scout.queries(p, job.queries, job.outDir.resolve(job.name + "_queries.json"));
                            for (Scout.Spec sp : job.scoutMaps) Scout.map(p, sp, job.outDir.resolve(job.name + "_scout_" + sp.name + ".json"));
                        } catch (Exception ex) {
                            WARN.add("scout: " + ex);
                            CineCam.LOG.error("[cinecam] scout failed", ex);
                        }
                    });
                    mc.options.hideGui = true;
                    mc.setScreen(null);
                    mc.getToasts().clear();
                }
                if (tick > 5 && ready()) go(Phase.SETTLE);
            }
            case SETTLE -> {
                if (tick == 1) {
                    var rt0 = mc.getMainRenderTarget();
                    if (rt0.width != job.width || rt0.height != job.height) {
                        Reflect.resizeFramebuffer(mc, job.width, job.height);
                        CineCam.LOG.info("[cinecam] framebuffer forced to {}x{}", job.width, job.height);
                    }
                }
                boolean idle = mc.levelRenderer.hasRenderedAllChunks();
                stableTicks = idle ? stableTicks + 1 : 0;
                if (tick >= job.settleTicks && stableTicks >= 20) {
                    if (scoutOnly) go(Phase.FINISH); else beginFilm(mc);
                }
            }
            case FILM -> { /* driven by render events */ }
            case FINISH -> finish(mc);
            case IDLE -> idle(mc);
            default -> { }
        }
    }

    private static void applyOptions(Minecraft mc) {
        var o = mc.options;
        mc.getWindow().setWindowed(job.width, job.height);
        o.enableVsync().set(false);
        o.framerateLimit().set(260);
        o.renderDistance().set(job.renderDistance);
        o.simulationDistance().set(job.simulationDistance);
        o.bobView().set(false);
        o.ambientOcclusion().set(true);
        o.mipmapLevels().set(job.mipmap);
        o.biomeBlendRadius().set(job.biomeBlend);
        o.cloudStatus().set(job.clouds ? CloudStatus.FANCY : CloudStatus.OFF);
        o.graphicsMode().set(GraphicsStatus.FANCY);
        o.particles().set(job.particles ? ParticleStatus.ALL : ParticleStatus.MINIMAL);
        o.gamma().set(job.gamma);
        o.entityDistanceScaling().set(2.0);
        o.getSoundSourceOptionInstance(SoundSource.MASTER).set(0.0);
        o.onboardAccessibility = false;
        mc.getTutorial().setStep(TutorialSteps.NONE);
        mc.getToasts().clear();
    }

    private static void startWorld(Minecraft mc) throws IOException {
        Path saves = mc.getLevelSource().getBaseDir();
        if ("copy".equals(job.worldMode) && job.copyFrom != null) {
            worldDir = FileUtil.findAvailableName(saves, "cinecam-" + job.name, "");
            copyDir(Path.of(job.copyFrom), saves.resolve(worldDir));
            Files.deleteIfExists(saves.resolve(worldDir).resolve("session.lock"));
            mc.createWorldOpenFlows().loadLevel(new TitleScreen(), worldDir);
            return;
        }
        worldDir = FileUtil.findAvailableName(saves, "cinecam-" + job.name, "");
        LevelSettings s = new LevelSettings("CineCam " + job.name, GameType.CREATIVE, false, Difficulty.PEACEFUL, true, new GameRules(), WorldDataConfiguration.DEFAULT);
        var preset = "flat".equals(job.preset) ? WorldPresets.FLAT : WorldPresets.NORMAL;
        mc.createWorldOpenFlows().createFreshLevel(worldDir, s, new WorldOptions(job.seed, job.structures, false),
                r -> r.registryOrThrow(Registries.WORLD_PRESET).getHolderOrThrow(preset).value().createWorldDimensions());
    }

    private static void checkReach(double[] a) {
        double[] b = table.bounds();
        double reach = job.renderDistance * 16.0 - 16.0;
        double far = Math.max(Math.max(Math.abs(b[0] - a[0]), Math.abs(b[1] - a[0])), Math.max(Math.abs(b[4] - a[2]), Math.abs(b[5] - a[2])));
        if (far > reach) WARN.add(String.format("camera path reaches %.0f blocks from the anchor but loaded radius is ~%.0f; distant parts will be empty", far, reach));
        for (String w : WARN) CineCam.LOG.warn("[cinecam] {}", w);
    }

    // ------------------------------------------------------------------ film

    private static void beginFilm(Minecraft mc) throws IOException {
        mc.options.hideGui = true;
        mc.options.setCameraType(net.minecraft.client.CameraType.FIRST_PERSON);
        Path file = stills ? job.outDir.resolve("stills").resolve("frame_%04d.png") : job.outDir.resolve(job.name + "_master.mkv");
        // The sink is opened lazily on the first capture because the real framebuffer size may differ from the request.
        // the OS may have snapped the window (and the main target) back between SETTLE and now: force the requested size again
        if (mc.getMainRenderTarget().width != job.width || mc.getMainRenderTarget().height != job.height) {
            Reflect.resizeFramebuffer(mc, job.width, job.height);
            CineCam.LOG.info("[cinecam] framebuffer re-forced to {}x{} at film start", job.width, job.height);
        }
        capW = mc.getMainRenderTarget().width;
        capH = mc.getMainRenderTarget().height;
        if (capW != job.width || capH != job.height) {
            WARN.add("framebuffer is " + capW + "x" + capH + " but " + job.width + "x" + job.height + " was requested (window clamped by the OS?)");
            CineCam.LOG.warn("[cinecam] {}", WARN.get(WARN.size() - 1));
        }
        job.width = capW;
        job.height = capH;
        sink = new FfmpegSink(job, file, stills);
        buf = BufferUtils.createByteBuffer(capW * capH * 3);
        scratch = new byte[capW * capH * 3];
        out = new byte[capW * capH * 3];
        acc = new int[capW * capH * 3];
        if (job.depth && !stills) {
            depthSink = FfmpegSink.depth(job, job.outDir.resolve(job.name + "_depth.mkv"));
            depthBuf = BufferUtils.createFloatBuffer(capW * capH);
            depthOut = ByteBuffer.allocateDirect(capW * capH * 2).order(ByteOrder.LITTLE_ENDIAN);
        }
        if (job.animFile != null) {
            anim = Anim.load(job.animFile);
            if (anim.water.length != table.n) WARN.add("anim.json has " + anim.water.length + " rows but camera.csv has " + table.n);
            try {
                Actors.init(mc, anim);
                WaterDrain.scan(mc, anim);
            } catch (Exception ex) {
                throw new IOException("anim init failed: " + ex, ex);
            }
        }
        fixed = new FixedTimer();
        if (vanillaTimer == null) vanillaTimer = Reflect.getTimer(mc);
        Reflect.setTimer(mc, fixed);
        fixed.schedule(0);
        idx = 0;
        filmStartNs = System.nanoTime();
        CineCam.LOG.info("[cinecam] FILM start: {} passes -> {}", table.n, file);
        go(Phase.FILM);
    }

    private static void filmRenderEnd(Minecraft mc) throws IOException {
        if (idx >= table.n) { go(Phase.FINISH); return; }
        totalPasses++;
        // The OS can resize the window mid-film (focus/DPI/display events) and the main target snaps back to the window size:
        // re-force it and redo this pass instead of reading a smaller image into the full-size buffer (tiled garbage).
        RenderTarget rt = mc.getMainRenderTarget();
        if (rt.width != capW || rt.height != capH) {
            Reflect.resizeFramebuffer(mc, capW, capH);
            resizeFixes++;
            if (resizeFixes == 1) WARN.add("framebuffer was resized by the OS during the film (" + rt.width + "x" + rt.height + "); re-forced");
            CineCam.LOG.warn("[cinecam] framebuffer snapped to {}x{} at row {}; re-forced to {}x{}", rt.width, rt.height, idx, capW, capH);
            readyStreak = 0;
            fixed.schedule(0);
            return;
        }
        int sub = idx % job.subframes;
        boolean idle = mc.levelRenderer.hasRenderedAllChunks();
        readyStreak = idle ? readyStreak + 1 : 0;
        int need = sub == 0 ? 2 : 1;
        boolean timedOut = waitStartNs != 0 && (System.nanoTime() - waitStartNs) / 1e9 > 40.0;
        if (readyStreak >= need || timedOut) {
            if (timedOut && readyStreak < need) {
                WARN.add("chunk wait timeout (40 s) at row " + idx);
            }
            waitStartNs = 0;
            maxWait = Math.max(maxWait, waitPasses);
            capture(sub);
            idx++;
            readyStreak = 0;
            waitPasses = 0;
            if (idx % (job.subframes * 30) == 0) {
                double secs = (System.nanoTime() - filmStartNs) / 1e9;
                CineCam.LOG.info("[cinecam] frame {}/{}  passes={} retries={}  {}s elapsed", idx / job.subframes, table.n / job.subframes, totalPasses, totalRetries, (int) secs);
            }
            if (idx >= table.n) {
                go(Phase.FINISH);
                return;
            }
            double dt = (table.t[idx] - table.t[idx - 1]) * 1000.0;
            fixed.schedule(job.worldTicks ? Math.max(0, dt) : 0);
        } else {
            if (waitStartNs == 0) waitStartNs = System.nanoTime();
            waitPasses++;
            totalRetries++;
            fixed.schedule(0);
            if (waitPasses > 3) {
                try { Thread.sleep(2); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); }
            }
        }
    }

    private static void capture(int sub) throws IOException {
        RenderTarget rt = Minecraft.getInstance().getMainRenderTarget();
        RenderSystem.assertOnRenderThread();
        GlStateManager._bindTexture(rt.getColorTextureId());
        GL11.glPixelStorei(GL11.GL_PACK_ALIGNMENT, 1);
        buf.clear();
        GL11.glGetTexImage(GL11.GL_TEXTURE_2D, 0, GL11.GL_RGB, GL11.GL_UNSIGNED_BYTE, buf);
        buf.rewind();
        int S = job.subframes;
        if (depthBuf != null && sub == S / 2) writeDepth();
        if (S == 1) {
            sink.write(buf);
            return;
        }
        buf.get(scratch);
        final int[] a = acc;
        final byte[] s = scratch;
        for (int i = 0; i < a.length; i++) a[i] += lut[s[i] & 0xFF];
        if (sub == S - 1) {
            final byte[] o = out;
            for (int i = 0; i < a.length; i++) {
                o[i] = invLut[a[i] / S];
                a[i] = 0;
            }
            sink.write(o);
        }
    }

    private static void writeDepth() throws IOException {
        float far = Minecraft.getInstance().gameRenderer.getRenderDistance() * 4.0f, near = 0.05f;
        depthOut.clear();
        var sb = depthOut.asShortBuffer();
        for (int i = 0; i < capW * capH; i++) {
            float d = depthBuf.get(i);
            float z = (2f * near * far) / (far + near - (2f * d - 1f) * (far - near));
            int v = Math.min(65535, Math.max(0, (int) (z * 128f)));
            sb.put(i, (short) v);
        }
        depthOut.rewind();
        depthSink.write(depthOut);
    }

    /** Linear-light accumulation tables: motion blur averaged in linear space looks like real shutter blur. */
    private static void initLut() {
        lut = new int[256];
        for (int v = 0; v < 256; v++) lut[v] = (int) Math.round(Math.pow(v / 255.0, 2.2) * 65535.0);
        invLut = new byte[65536];
        for (int v = 0; v < 65536; v++) invLut[v] = (byte) Math.round(255.0 * Math.pow(v / 65535.0, 1 / 2.2));
    }

    private static void finish(Minecraft mc) {
        if (phase == Phase.DONE) return;
        try {
            if (sink != null) sink.close();
            if (depthSink != null) depthSink.close();
        } catch (Exception ex) {
            WARN.add("ffmpeg close: " + ex);
        }
        try {
            Files.createDirectories(job.outDir);
            double secs = filmStartNs == 0 ? 0 : (System.nanoTime() - filmStartNs) / 1e9;
            StringBuilder r = new StringBuilder("{\n");
            r.append("  \"name\": ").append(q(job.name)).append(",\n");
            r.append("  \"ok\": ").append(fatal == null && (scoutOnly || idx >= table.n)).append(",\n");
            r.append("  \"error\": ").append(fatal == null ? "null" : q(fatal)).append(",\n");
            r.append("  \"width\": ").append(job.width).append(", \"height\": ").append(job.height).append(",\n");
            r.append("  \"fps\": ").append(job.fps).append(", \"subframes\": ").append(job.subframes).append(",\n");
            r.append("  \"rows\": ").append(table.n).append(", \"rowsRendered\": ").append(idx).append(",\n");
            r.append("  \"passes\": ").append(totalPasses).append(", \"retries\": ").append(totalRetries).append(", \"maxWait\": ").append(maxWait).append(",\n");
            r.append("  \"filmSeconds\": ").append(String.format(java.util.Locale.ROOT, "%.1f", secs)).append(",\n");
            r.append("  \"output\": ").append(sink == null ? "null" : q(sink.output.toString())).append(",\n");
            r.append("  \"warnings\": [");
            for (int i = 0; i < WARN.size(); i++) r.append(i == 0 ? "" : ", ").append(q(WARN.get(i)));
            r.append("]\n}\n");
            Files.writeString(job.outDir.resolve(job.name + "_report.json"), r.toString(), StandardCharsets.UTF_8);
        } catch (Exception ex) {
            CineCam.LOG.error("[cinecam] report failed", ex);
        }
        while (!QUEUE.isEmpty()) {                 // batch: same world, next shot (a failed shot does not stop the others)
            Path nxt = QUEUE.poll();
            try {
                nextShot(mc, nxt);
                return;
            } catch (Throwable ex) {
                CineCam.LOG.error("[cinecam] could not start queued shot " + nxt, ex);
            }
        }
        if (job != null && job.inbox != null) {    // v1.1 live session: keep the game and the world open for the next shots
            if (vanillaTimer != null) Reflect.setTimer(mc, vanillaTimer);
            WaterDrain.reset(mc);
            idleSinceNs = System.nanoTime();
            idleInbox = job.inbox; idleLimit = job.idleSec;
            phase = Phase.IDLE;
            CineCam.LOG.info("[cinecam] idle: waiting for jobs in {}", idleInbox);
            return;
        }
        phase = Phase.DONE;
        CineCam.LOG.info("[cinecam] done ({}), stopping game", fatal == null ? "ok" : fatal);
        if (!Boolean.getBoolean("cinecam.keepOpen")) mc.stop();
    }

    private static int lastCmdsHash;
    private static long idleSinceNs;
    private static Path idleInbox;
    private static int idleLimit = 900;

    /** v1.1 live session: every 10 ticks look for "*.go" files (each holds the path of a job.json) in the inbox; "stop" quits. */
    private static void idle(Minecraft mc) {
        if (tick % 10 != 0) return;
        try {
            if (Files.exists(idleInbox.resolve("stop")) || (System.nanoTime() - idleSinceNs) / 1e9 > idleLimit) {
                Files.deleteIfExists(idleInbox.resolve("stop"));
                phase = Phase.DONE;
                CineCam.LOG.info("[cinecam] live session closed");
                mc.stop();
                return;
            }
            java.util.List<Path> go = new java.util.ArrayList<>();
            try (var ds = Files.newDirectoryStream(idleInbox, "*.go")) { for (Path p : ds) go.add(p); }
            if (go.isEmpty()) return;
            go.sort(null);
            Path f = go.get(0);
            Path jobPath = Path.of(Files.readString(f, StandardCharsets.UTF_8).trim());
            Files.deleteIfExists(f);
            nextShot(mc, jobPath);
        } catch (Throwable ex) {
            CineCam.LOG.error("[cinecam] inbox", ex);
            idleSinceNs = System.nanoTime();
            phase = Phase.IDLE;
        }
    }

    /** Batch: put the vanilla clock back, drop the film state of the finished shot and start the next one at SETUP (same world). */
    private static void nextShot(Minecraft mc, Path p) throws IOException {
        if (vanillaTimer != null) Reflect.setTimer(mc, vanillaTimer);
        WaterDrain.reset(mc);
        sink = null; depthSink = null; depthBuf = null; depthOut = null; anim = null; fixed = null;
        buf = null; scratch = null; out = null; acc = null;
        idx = 0; readyStreak = 0; waitPasses = 0; totalPasses = 0; totalRetries = 0; maxWait = 0;
        posing = false; resizeFixes = 0; filmStartNs = 0; waitStartNs = 0;
        WARN.clear(); fatal = null; sunTexId = null; pending = null;
        shotNo++;
        loadShot(p);
        var o = mc.options;
        o.renderDistance().set(job.renderDistance);
        o.simulationDistance().set(job.simulationDistance);
        o.cloudStatus().set(job.clouds ? CloudStatus.FANCY : CloudStatus.OFF);
        o.particles().set(job.particles ? ParticleStatus.ALL : ParticleStatus.MINIMAL);
        o.gamma().set(job.gamma);
        if (o.biomeBlendRadius().get() != job.biomeBlend) o.biomeBlendRadius().set(job.biomeBlend);
        CineCam.LOG.info("[cinecam] batch shot {} -> {}", shotNo, job.name);
        go(Phase.SETUP);
    }

    // ------------------------------------------------------------------ helpers

    private static void go(Phase next) {
        phase = next;
        tick = 0;
        stableTicks = 0;
        phaseStartNs = System.nanoTime();
        CineCam.LOG.info("[cinecam] phase {}", next);
    }

    private static void server(Minecraft mc, Consumer<ServerPlayer> task) {
        var s = mc.getSingleplayerServer();
        if (s == null) throw new IllegalStateException("no integrated server");
        pending = new CompletableFuture<>();
        var f = pending;
        s.execute(() -> {
            try {
                task.accept(s.getPlayerList().getPlayers().get(0));
            } catch (Throwable t) {
                CineCam.LOG.error("[cinecam] server task failed", t);
                WARN.add("server task: " + t);
            } finally {
                f.complete(null);
            }
        });
    }

    private static boolean ready() {
        return pending == null || pending.isDone();
    }

    private static void run(ServerPlayer p, String command) {
        String c = command.startsWith("/") ? command.substring(1) : command;
        try {
            int r = p.server.getCommands().performPrefixedCommand(p.createCommandSourceStack().withPermission(4), c);
            CineCam.LOG.info("[cinecam] /{} -> {}", c, r);
        } catch (Throwable t) {
            WARN.add("command '" + c + "': " + t);
            CineCam.LOG.warn("[cinecam] command failed: {}", c, t);
        }
    }

    private static void copyDir(Path from, Path to) throws IOException {
        try (Stream<Path> s = Files.walk(from)) {
            for (Path p : (Iterable<Path>) s::iterator) {
                Path d = to.resolve(from.relativize(p).toString());
                if (Files.isDirectory(p)) Files.createDirectories(d);
                else Files.copy(p, d, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            }
        }
    }

    private static String q(String s) {
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\"";
    }

    /** Reflection helpers resolved by signature, so they work with dev (Mojang) and production (SRG) names alike. */
    private static final class Reflect {
        private static Method setPos;
        private static Field timerField;

        static void setCameraPosition(Camera cam, Vec3 v) {
            try {
                if (setPos == null) {
                    for (Method m : Camera.class.getDeclaredMethods()) {
                        if (m.getParameterCount() == 1 && m.getParameterTypes()[0] == Vec3.class && m.getReturnType() == void.class) {
                            m.setAccessible(true);
                            setPos = m;
                            break;
                        }
                    }
                    if (setPos == null) throw new IllegalStateException("Camera.setPosition(Vec3) not found");
                }
                setPos.invoke(cam, v);
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException(e);
            }
        }

        /** Resizes the main render target independently of the OS window (the window is clamped to the monitor). */
        static void resizeFramebuffer(Minecraft mc, int w, int h) {
            try {
                Window win = mc.getWindow();
                Method m = ObfuscationReflectionHelper.findMethod(Window.class, "m_85415_", long.class, int.class, int.class);
                m.setAccessible(true);
                m.invoke(win, win.getWindow(), w, h);
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException(e);
            }
        }

        static Timer getTimer(Minecraft mc) {
            try {
                if (timerField == null) {
                    for (Field f : Minecraft.class.getDeclaredFields()) {
                        if (f.getType() == Timer.class) { f.setAccessible(true); timerField = f; break; }
                    }
                    if (timerField == null) throw new IllegalStateException("Minecraft.timer not found");
                }
                return (Timer) timerField.get(mc);
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException(e);
            }
        }

        static void setTimer(Minecraft mc, Timer t) {
            try {
                if (timerField == null) {
                    for (Field f : Minecraft.class.getDeclaredFields()) {
                        if (f.getType() == Timer.class) { f.setAccessible(true); timerField = f; break; }
                    }
                    if (timerField == null) throw new IllegalStateException("Minecraft.timer not found");
                }
                timerField.set(mc, t);
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException(e);
            }
        }
    }
}
