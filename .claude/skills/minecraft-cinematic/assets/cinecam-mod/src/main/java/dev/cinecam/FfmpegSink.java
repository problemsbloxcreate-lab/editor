package dev.cinecam;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.channels.Channels;
import java.nio.channels.WritableByteChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/** Pipes raw RGB24 frames (bottom-up, as read from OpenGL) into ffmpeg. */
public final class FfmpegSink implements AutoCloseable {
    private final Process proc;
    private final WritableByteChannel ch;
    private final OutputStream os;
    public final Path output;

    /** 16-bit depth stream (lossless FFV1). */
    public static FfmpegSink depth(Job job, Path output) throws IOException {
        return new FfmpegSink(job, output, List.of(
                job.ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "rawvideo", "-pix_fmt", "gray16le", "-s", job.width + "x" + job.height, "-framerate", String.valueOf(job.fps),
                "-i", "-", "-vf", "vflip", "-c:v", "ffv1", "-threads", "2", "-pix_fmt", "gray16le", output.toString()));
    }

    private FfmpegSink(Job job, Path output, List<String> cmd) throws IOException {
        this.output = output;
        Files.createDirectories(output.getParent());
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        pb.redirectOutput(output.resolveSibling(output.getFileName() + ".ffmpeg.log").toFile());
        this.proc = pb.start();
        this.os = proc.getOutputStream();
        this.ch = Channels.newChannel(os);
    }

    public FfmpegSink(Job job, Path output, boolean stills) throws IOException {
        this.output = output;
        Files.createDirectories(output.getParent());
        List<String> cmd = new ArrayList<>(List.of(
                job.ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "rawvideo", "-pix_fmt", "rgb24",
                "-s", job.width + "x" + job.height,
                "-framerate", String.valueOf(job.fps),
                "-i", "-",
                "-vf", "vflip"));
        if (stills) {
            cmd.addAll(List.of("-start_number", "0"));
        } else if (job.codec.equals("lossless")) {
            // RGB lossless master: no chroma subsampling, no colour-matrix rounding. Post-processing re-encodes it.
            cmd.addAll(List.of("-c:v", "libx264rgb", "-preset", "ultrafast", "-qp", "0", "-pix_fmt", "rgb24", "-threads", "4"));   // v0.8: 4 threads ~ same speed here (input ~7 fps), far less RAM than auto (30 frame threads)
        } else {
            cmd.addAll(List.of("-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", "-movflags", "+faststart"));
        }
        cmd.add(output.toString());
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        pb.redirectOutput(output.resolveSibling(output.getFileName() + ".ffmpeg.log").toFile());
        this.proc = pb.start();
        this.os = proc.getOutputStream();
        this.ch = Channels.newChannel(os);
    }

    public void write(ByteBuffer rgb) throws IOException {
        rgb.rewind();
        while (rgb.hasRemaining()) ch.write(rgb);
    }

    public void write(byte[] rgb) throws IOException {
        os.write(rgb);
    }

    @Override
    public void close() throws IOException {
        try {
            os.flush();
            os.close();
            if (!proc.waitFor(120, java.util.concurrent.TimeUnit.SECONDS)) proc.destroyForcibly();
        } catch (InterruptedException e) {
            proc.destroyForcibly();
            Thread.currentThread().interrupt();
        }
    }
}
