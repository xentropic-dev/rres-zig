const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const upstream = b.dependency("upstream", .{});

    const lib = b.addLibrary(.{
        .name = "rres-zig",
        .root_module = b.createModule(.{
            .target = target,
            .optimize = optimize,
            .link_libc = true,
            .root_source_file = b.path("src/root.zig"),
        }),
    });

    lib.addIncludePath(upstream.path("src"));
    lib.addIncludePath(b.path("src"));
    lib.root_module.addCSourceFiles(.{
        .root = upstream.path("src/external"),
        .files = &.{ "aes.c", "lz4.c", "monocypher.c" },
        .flags = &.{},
    });
    lib.root_module.addCSourceFile(.{
        .file = b.path("src/rres_impl.c"),
        .flags = &.{},
    });

    // Example executable
    const exe = b.addExecutable(.{ .name = "example", .root_module = b.createModule(.{
        .root_source_file = b.path("example/main.zig"),
        .target = target,
        .optimize = optimize,
    }) });

    exe.root_module.addImport("rres", lib.root_module);

    b.installArtifact(exe);

    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());

    if (b.args) |args| {
        run_cmd.addArgs(args);
    }

    const run_step = b.step("run", "Run the example");
    run_step.dependOn(&run_cmd.step);
}
