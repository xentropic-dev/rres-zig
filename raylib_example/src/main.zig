// raylib-zig (c) Nikolas Wipper 2023

const std = @import("std");
const rl = @import("raylib");
const rres = @import("rres");

pub fn main() anyerror!void {
    // Initialization
    //--------------------------------------------------------------------------------------
    const screenWidth = 800;
    const screenHeight = 450;

    rl.initWindow(screenWidth, screenHeight, "raylib-zig [core] example - basic window");
    defer rl.closeWindow();

    // Load rres central directory
    const rres_dir = rres.rresLoadCentralDirectory("resources/example.rres");
    defer rres.rresUnloadCentralDirectory(rres_dir);

    // Get resource ID for "zero.png"
    const id_signed = rres.rresGetResourceId(rres_dir, "zero.png");
    const id: c_uint = @bitCast(id_signed);

    // Load and unpack resource chunk
    var chunk = rres.rresLoadResourceChunk("resources/example.rres", id);
    defer rres.rresUnloadResourceChunk(chunk);

    const unpack_result = rres.rres_raylib.UnpackResourceChunk(&chunk);
    if (unpack_result != 0) {
        std.debug.print("ERROR: Failed to unpack resource (error code: {d})\n", .{unpack_result});
        return error.UnpackFailed;
    }

    // Load image from unpacked resource
    const image_c = rres.rres_raylib.LoadImageFromResource(chunk);
    const image: rl.Image = @bitCast(image_c);
    const texture = rl.loadTextureFromImage(image) catch |err| {
        std.debug.print("ERROR: Failed to load texture: {}\n", .{err});
        return err;
    };
    defer rl.unloadTexture(texture);
    rl.unloadImage(image);

    rl.setTargetFPS(60);
    //--------------------------------------------------------------------------------------

    // Main game loop
    while (!rl.windowShouldClose()) {
        // Draw
        //----------------------------------------------------------------------------------
        rl.beginDrawing();
        defer rl.endDrawing();

        rl.clearBackground(.white);

        // Draw the texture from the rres resource
        rl.drawTexture(texture, screenWidth / 2 - @divTrunc(texture.width, 2), screenHeight / 2 - @divTrunc(texture.height, 2), .white);

        rl.drawText("Image loaded from rres resource!", 190, 400, 20, .light_gray);
        //----------------------------------------------------------------------------------
    }
}
