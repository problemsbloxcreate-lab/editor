package dev.cinecam;

import com.mojang.logging.LogUtils;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraft.resources.ResourceLocation;
import org.slf4j.Logger;

/**
 * CineCam: offline cinematic camera renderer.
 * Everything happens in {@link Controller}; this class only exists so Forge loads the mod.
 * The mod is inert unless the JVM property {@code cinecam.job} points to a job.json.
 */
@Mod(CineCam.MOD_ID)
public final class CineCam {
    public static final String MOD_ID = "cinecam";
    public static final Logger LOG = LogUtils.getLogger();

    public CineCam() {
        LOG.info("[cinecam] loaded; job={}", System.getProperty("cinecam.job", "<none>"));
        FMLJavaModLoadingContext.get().getModEventBus().addListener(CineCam::models);
    }

    /** Extra item models shipped in assets/cinecam/models/item (props for actors' hands, e.g. the Elastic Glove). */
    public static final String[] EXTRA_MODELS = {"item/elastic_glove"};

    private static void models(net.minecraftforge.client.event.ModelEvent.RegisterAdditional e) {
        for (String m : EXTRA_MODELS) e.register(new ResourceLocation(MOD_ID, m));
    }
}
