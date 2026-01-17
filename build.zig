const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const enable_raylib = b.option(bool, "raylib", "Enable raylib integration") orelse false;

    const upstream = b.dependency("upstream", .{});

    const options = b.addOptions();
    options.addOption(bool, "enable_raylib", enable_raylib);

    const rres_module = b.addModule("rres", .{
        .root_source_file = b.path("src/root.zig"),
        .target = target,
        .optimize = optimize,
        .link_libc = true,
    });

    rres_module.addImport("build_options", options.createModule());

    rres_module.addIncludePath(upstream.path("src"));
    rres_module.addIncludePath(b.path("src"));

    // Add emscripten sysroot for wasm builds
    if (target.result.os.tag == .emscripten) {
        const emsdk_dep = b.dependency("emsdk", .{});
        rres_module.addSystemIncludePath(emsdk_dep.path("upstream/emscripten/cache/sysroot/include"));
    }

    // Note: external libraries (aes, lz4, monocypher) are included by the implementation headers
    // so we don't compile them separately to avoid duplicate symbols

    rres_module.addCSourceFile(.{
        .file = b.path("src/rres_impl.c"),
        .flags = &.{
            "-DRRES_SUPPORT_COMPRESSION_LZ4",
            "-DRRES_SUPPORT_ENCRYPTION_AES",
            "-DRRES_SUPPORT_ENCRYPTION_XCHACHA20",
        },
    });

    if (enable_raylib) {
        const raylib_dep = b.dependency("raylib_zig", .{
            .target = target,
            .optimize = optimize,
        });
        const raylib_module = raylib_dep.module("raylib");
        const raylib_artifact = raylib_dep.artifact("raylib");

        rres_module.addImport("raylib", raylib_module);
        rres_module.linkLibrary(raylib_artifact);

        rres_module.addCSourceFile(.{
            .file = b.path("src/rres_raylib_impl.c"),
            .flags = &.{
                "-DRRES_SUPPORT_COMPRESSION_LZ4",
                "-DRRES_SUPPORT_ENCRYPTION_AES",
                "-DRRES_SUPPORT_ENCRYPTION_XCHACHA20",
            },
        });
    }
}
