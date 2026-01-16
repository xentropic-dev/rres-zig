// raylib-zig (c) Nikolas Wipper 2023

const std = @import("std");
const rl = @import("raylib");
const rres = @import("rres");

pub fn main() anyerror!void {
    // Initialization
    //--------------------------------------------------------------------------------------
    const screenWidth = 800;
    const screenHeight = 450;

    // Set password FIRST, before initializing raylib
    // rres.rresSetCipherPassword("a");

    rl.initWindow(screenWidth, screenHeight, "raylib-zig [core] example - basic window");

    // Verify password was set
    const set_password = rres.rresGetCipherPassword();
    std.debug.print("Password set to: {s}\n", .{set_password});

    const rres_dir = rres.rresLoadCentralDirectory("resources/example.rres");
    defer rres.rresUnloadCentralDirectory(rres_dir);

    const id_signed = rres.rresGetResourceId(rres_dir, "zero.png");
    const id: c_uint = @bitCast(id_signed);

    var chunk = rres.rresLoadResourceChunk("resources/example_chacha2.rres", id);
    defer rres.rresUnloadResourceChunk(chunk);

    std.debug.print("Chunk cipher type: {d}, compression type: {d}\n", .{ chunk.info.cipherType, chunk.info.compType });

    const unpack_result = rres.rres_raylib.UnpackResourceChunk(&chunk);

    if (unpack_result != 0) {
        std.debug.print("ERROR: Failed to unpack (result: {d}). Please create an unencrypted rres file for testing.\n", .{unpack_result});
        return error.UnpackFailed;
    }

    const image_c = rres.rres_raylib.LoadImageFromResource(chunk);
    const image: rl.Image = @bitCast(image_c);
    const texture = rl.loadTextureFromImage(image) catch |err| {
        std.debug.print("Failed to load texture: {}\n", .{err});
        return err;
    };
    defer rl.unloadTexture(texture);
    rl.unloadImage(image);

    defer rl.closeWindow(); // Close window and OpenGL context

    rl.setTargetFPS(60); // Set our game to run at 60 frames-per-second
    //--------------------------------------------------------------------------------------

    // Main game loop
    while (!rl.windowShouldClose()) { // Detect window close button or ESC key
        // Update
        //----------------------------------------------------------------------------------
        // TODO: Update your variables here
        //----------------------------------------------------------------------------------

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
