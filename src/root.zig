//! Zig bindings for rres (raylib resource format)
const std = @import("std");

const c = @cImport({
    @cInclude("rres.h");
});

// Types
pub const rresFileHeader = c.rresFileHeader;
pub const rresResourceChunkInfo = c.rresResourceChunkInfo;
pub const rresResourceChunkData = c.rresResourceChunkData;
pub const rresResourceChunk = c.rresResourceChunk;
pub const rresResourceMulti = c.rresResourceMulti;
pub const rresDirEntry = c.rresDirEntry;
pub const rresCentralDir = c.rresCentralDir;
pub const rresFontGlyphInfo = c.rresFontGlyphInfo;

// Enums
pub const rresResourceDataType = c.rresResourceDataType;
pub const rresCompressionType = c.rresCompressionType;
pub const rresEncryptionType = c.rresEncryptionType;
pub const rresErrorType = c.rresErrorType;
pub const rresTextEncoding = c.rresTextEncoding;
pub const rresCodeLang = c.rresCodeLang;
pub const rresPixelFormat = c.rresPixelFormat;
pub const rresVertexAttribute = c.rresVertexAttribute;
pub const rresVertexFormat = c.rresVertexFormat;
pub const rresFontStyle = c.rresFontStyle;

// Functions
pub const rresLoadResourceChunk = c.rresLoadResourceChunk;
pub const rresUnloadResourceChunk = c.rresUnloadResourceChunk;
pub const rresLoadResourceMulti = c.rresLoadResourceMulti;
pub const rresUnloadResourceMulti = c.rresUnloadResourceMulti;
pub const rresLoadResourceChunkInfo = c.rresLoadResourceChunkInfo;
pub const rresLoadResourceChunkInfoAll = c.rresLoadResourceChunkInfoAll;
pub const rresLoadCentralDirectory = c.rresLoadCentralDirectory;
pub const rresUnloadCentralDirectory = c.rresUnloadCentralDirectory;
pub const rresGetDataType = c.rresGetDataType;
pub const rresGetResourceId = c.rresGetResourceId;
pub const rresComputeCRC32 = c.rresComputeCRC32;
pub const rresSetCipherPassword = c.rresSetCipherPassword;
pub const rresGetCipherPassword = c.rresGetCipherPassword;
